import streamlit as st
import yfinance as yf
import pandas as pd
from tvDatafeed import TvDatafeed, Interval
from indicators import *

@st.cache_resource
def get_tv():
    try:
        try:
            if hasattr(st, "secrets") and "TV_USER" in st.secrets and "TV_PASS" in st.secrets:
                return TvDatafeed(st.secrets["TV_USER"], st.secrets["TV_PASS"])
        except Exception:
            pass
        return TvDatafeed()
    except Exception as e:
        print("tvDatafeed init error:", e)
        return None


_tv_consecutive_failures = 0

def is_tv_available():
    global _tv_consecutive_failures
    return _tv_consecutive_failures < 2


@st.cache_data(ttl=300, show_spinner=False, max_entries=200)
def analyze_stock_cached(ticker, yf_period, yf_interval, arabic_name, sector_name, index_name):
    global _tv_consecutive_failures
    df = pd.DataFrame()
    tv = get_tv()
    
    # 1. المحاولة الأولى باستخدام TradingView (أدق للسوق المصري)
    if tv is not None and is_tv_available():
        try:
            tv_interval_map = {"15m": Interval.in_15_minute, "1h": Interval.in_1_hour, "1d": Interval.in_daily}
            tv_interval_val = tv_interval_map.get(yf_interval, Interval.in_daily)
            tv_ticker = ticker.replace('.CA', '')
            if tv_ticker in ["QNBA", "QNBE"]:
                tv_ticker = "QNBE"
            elif tv_ticker in ["AUTO", "GBCO"]:
                tv_ticker = "GBCO"
            df_tv = tv.get_hist(symbol=tv_ticker, exchange='EGX', interval=tv_interval_val, n_bars=600)
            if df_tv is not None and not df_tv.empty:
                df_tv.rename(columns={'open':'Open', 'high':'High', 'low':'Low', 'close':'Close', 'volume':'Volume'}, inplace=True)
                if 'symbol' in df_tv.columns: df_tv.drop(columns=['symbol'], inplace=True)
                df = df_tv
                _tv_consecutive_failures = 0
            else:
                _tv_consecutive_failures += 1
        except Exception as e:
            _tv_consecutive_failures += 1
            print(f"TV fetch error for {ticker}: {e}")
            
    # 2. المصدر الاحتياطي (Fallback) من Yahoo Finance
    if df.empty:
        df = yf.download(ticker, period=yf_period, interval=yf_interval, progress=False, auto_adjust=True)
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
        
    if df.empty:
        return None
        
    # تنظيف البيانات من أي أيام إجازات أو بيانات ناقصة
    df = df.ffill().dropna()
    
    if len(df) < 20: # لا يوجد بيانات كافية للحسابات الفنية
        return None
        
    close_series = df['Close'].squeeze()
    high_series = df['High'].squeeze()
    low_series = df['Low'].squeeze()
    volume_series = df['Volume'].squeeze()
    
    # فحص نشاط السهم واستبعاد الأسهم المجمدة بدون تداول
    recent_vol_sum = float(volume_series.tail(10).sum()) if len(volume_series) >= 10 else float(volume_series.sum())
    is_price_flat = bool(close_series.tail(10).nunique() <= 1) if len(close_series) >= 10 else False
    if recent_vol_sum == 0 or is_price_flat:
        last_close = float(close_series.iloc[-1])
        ticker_display = f"{ticker.replace('.CA', '')} - {arabic_name}" if arabic_name else ticker.replace('.CA', '')
        return {
            "المؤشر": index_name,
            "القطاع": sector_name,
            "نظام التسوية": "غير متداول (سيولة منعدمة)",
            "الكود": ticker,
            "اسم السهم": ticker_display,
            "السعر الحالي": round(last_close, 2),
            "الدخول المقترح": "انتظار",
            "الهدف المتوقع": "-",
            "وقف الخسارة": "-",
            "المخاطرة:العائد": "-",
            "السيولة": "منعدمة ⚠️",
            "الزخم (RSI)": 50.0,
            "الحالة الفنية": "سهم خامل / لا يوجد تداول",
            "قوة التقييم": "0%",
            "التوجيه الحالي": "⚪ محايد / استقرار",
            "Score": 0.0
        }
    
    # === حساب المؤشرات الفنية V3.0 ===
    df['RSI_14'] = calculate_rsi(close_series, window=14)
    df['EMA_9'] = close_series.ewm(span=9, adjust=False).mean()
    df['EMA_21'] = close_series.ewm(span=21, adjust=False).mean()
    df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = calculate_macd(close_series)
    df['ATR'] = calculate_atr(high_series, low_series, close_series)
    df['OBV'], df['OBV_EMA'] = calculate_obv_trend(close_series, volume_series)
    df['ADX'], df['PLUS_DI'], df['MINUS_DI'] = calculate_adx(high_series, low_series, close_series)
    df['SuperTrend'], df['SuperTrend_Dir'] = calculate_supertrend(high_series, low_series, close_series)
    df['BB_Squeeze'] = calculate_bb_squeeze(close_series)
    df['CMF'] = calculate_cmf(high_series, low_series, close_series, volume_series)
    
    # المؤشرات الجديدة V3.0
    df['StochRSI_K'], df['StochRSI_D'] = calculate_stochastic_rsi(close_series)
    df['VWAP'] = calculate_vwap(high_series, low_series, close_series, volume_series)
    
    # كشف التباعد (Divergence)
    divergence = detect_rsi_divergence(close_series, df['RSI_14'])
    
    # مستويات الدعم والمقاومة (Pivot Points)
    pivots = calculate_pivot_points(high_series, low_series, close_series)
    
    last_close = float(close_series.iloc[-1])
    last_open = float(df['Open'].squeeze().iloc[-1])
    atr_val = float(df['ATR'].iloc[-1])
    rsi_14 = float(df['RSI_14'].iloc[-1])
    ema_9 = float(df['EMA_9'].iloc[-1])
    ema_21 = float(df['EMA_21'].iloc[-1])
    macd = float(df['MACD'].iloc[-1])
    macd_signal = float(df['MACD_Signal'].iloc[-1])
    obv = float(df['OBV'].iloc[-1])
    obv_ema = float(df['OBV_EMA'].iloc[-1])
    adx_val = float(df['ADX'].iloc[-1]) if not pd.isna(df['ADX'].iloc[-1]) else 0
    plus_di = float(df['PLUS_DI'].iloc[-1]) if not pd.isna(df['PLUS_DI'].iloc[-1]) else 0
    minus_di = float(df['MINUS_DI'].iloc[-1]) if not pd.isna(df['MINUS_DI'].iloc[-1]) else 0
    st_val = float(df['SuperTrend'].iloc[-1]) if not pd.isna(df['SuperTrend'].iloc[-1]) else 0
    st_dir = float(df['SuperTrend_Dir'].iloc[-1]) if not pd.isna(df['SuperTrend_Dir'].iloc[-1]) else 0
    bb_squeeze = bool(df['BB_Squeeze'].iloc[-1])
    cmf_val = float(df['CMF'].iloc[-1]) if not pd.isna(df['CMF'].iloc[-1]) else 0
    stoch_k = float(df['StochRSI_K'].iloc[-1]) if not pd.isna(df['StochRSI_K'].iloc[-1]) else 50
    stoch_d = float(df['StochRSI_D'].iloc[-1]) if not pd.isna(df['StochRSI_D'].iloc[-1]) else 50
    vwap_val = float(df['VWAP'].iloc[-1]) if not pd.isna(df['VWAP'].iloc[-1]) else last_close
    
    volume_sma_10 = volume_series.rolling(window=10).mean()
    if len(volume_sma_10) > 0 and pd.notna(volume_sma_10.iloc[-1]):
        last_vol = float(volume_series.iloc[-1])
        avg_vol_10 = float(volume_sma_10.iloc[-1])
        vol_spike = (last_vol / avg_vol_10) * 100 if avg_vol_10 > 0 else 0
    else:
        avg_vol_10 = 0
        vol_spike = 0
        
    if vol_spike >= 300:
        vol_status = f"🔥 انفجار ({int(vol_spike)}%)"
    elif vol_spike >= 150:
        vol_status = f"⚡ عالية ({int(vol_spike)}%)"
    else:
        vol_status = "طبيعي"
    
    score = 0.0
    status_tags = []
    avg_traded_value = avg_vol_10 * last_close
    is_valid_for_day_trading = True
    if yf_interval == "15m" and avg_traded_value < 1000000:
        is_valid_for_day_trading = False
        
    # === نظام التقييم الفني V3.0 ===
    
    is_trend_strong = adx_val > 25
    is_trend_choppy = adx_val < 20
    is_uptrend = st_dir == 1
    
    # 1. SuperTrend (وزن مخفض لمنع السيطرة المفرطة)
    if is_uptrend:
        score += 2
        status_tags.append("ترند صاعد مدعوم" if is_trend_strong else "بداية إيجابية")
    else:
        score -= 2
        status_tags.append("ترند هابط صريح" if is_trend_strong else "هبوط ضعيف")
        
    # 2. ADX + DI Filter (وزن مخفض)
    if is_uptrend and is_trend_strong and plus_di > minus_di:
        score += 1.5
    elif not is_uptrend and is_trend_strong and minus_di > plus_di:
        score -= 1.5
    elif is_trend_choppy:
        status_tags.append("تذبذب عرضي")
        
    # 3. EMA Cross
    if ema_9 > ema_21:
        score += 1
    elif ema_9 < ema_21:
        score -= 1
        
    # 4. MACD
    if macd > macd_signal: 
        if not is_trend_choppy:
            score += 1
        if macd < 0 and is_uptrend:  # تقاطع إيجابي تحت الصفر مع ترند صاعد
            score += 1.5
    elif macd < macd_signal: 
        if not is_trend_choppy:
            score -= 1
            
    # 5. RSI (مع تحسين منطق التشبع)
    if rsi_14 < 35:
        if is_uptrend:
            score += 2
            status_tags.append("تجميع من قاع (فرصة)")
        elif bb_squeeze:
            score += 1
            status_tags.append("تشبع بيعي مع انكماش")
        else:
            score -= 1  # سكين ساقط
    elif rsi_14 > 70:
        if is_trend_strong and is_uptrend:
            score += 1
        else:
            score -= 2
            status_tags.append("تشبع شرائي متضخم")
    elif 40 <= rsi_14 <= 60 and is_uptrend:
        score += 1
        
    # 6. Stochastic RSI — فعال جداً في التذبذب العرضي (جديد V3.0)
    if is_trend_choppy:
        if stoch_k < 20 and stoch_k > stoch_d:
            score += 1.5
            status_tags.append("StochRSI: ارتداد من قاع")
        elif stoch_k > 80 and stoch_k < stoch_d:
            score -= 1.5
            status_tags.append("StochRSI: هبوط من قمة")
    else:
        # حتى في الترند، StochRSI يعطي تأكيد إضافي
        if stoch_k < 20 and is_uptrend:
            score += 1
        elif stoch_k > 80 and not is_uptrend:
            score -= 1
        
    # 7. BB Squeeze & CMF (استكشاف الانفجارات السعرية)
    if bb_squeeze:
        status_tags.append("استعداد لانفجار سعري")
        if cmf_val > 0.05:
            score += 2
            status_tags[-1] = "تجميع لانفجار لأعلى"
        elif cmf_val < -0.05:
            score -= 2
            status_tags[-1] = "تصريف متوقع لانفجار لأسفل"
            
    # 8. تأكيد السيولة العالية والمكثفة
    if vol_spike >= 150:
        if last_close >= last_open and cmf_val >= -0.02:
            score += 2
        elif last_close < last_open and cmf_val < -0.02:
            score -= 2
            
    # 9. السيولة التراكمية (OBV) — كشف التصريف الخفي
    if obv > obv_ema: 
        score += 1
    elif obv < obv_ema: 
        score -= 1
    
    # 10. كشف التباعد — Divergence Detection (جديد V3.0)
    if divergence == 1:  # Bullish Divergence
        score += 2.5
        status_tags.append("📈 تباعد إيجابي (انعكاس صاعد)")
    elif divergence == -1:  # Bearish Divergence
        score -= 2.5
        status_tags.append("📉 تباعد سلبي (انعكاس هابط)")
    
    # 11. VWAP — مهم للمضاربة اللحظية والساعة (جديد V3.0)
    if yf_interval in ["15m", "1h"]:
        if last_close > vwap_val and is_uptrend:
            score += 1
        elif last_close < vwap_val and not is_uptrend:
            score -= 1
    
    # === تجميع الحالة الفنية ===
    status_desc = " | ".join(status_tags) if status_tags else "محايد / تذبذب"
    
    # === التوجيه النهائي V3.0 ===
    # النطاق النظري: أقصى = +19.5 | أدنى = -17
    if not is_valid_for_day_trading:
        score = -10
        signal = "🚫 لا يدعم T+0 (سيولة ضعيفة)"
    elif score >= 9:
        signal = "🟢 إشارة شراء قوية"
    elif score >= 4:
        signal = "🟡 إيجابي / تجميع"
    elif score >= -3:
        signal = "⚪ محايد / استقرار"
    elif score >= -8:
        signal = "🟠 سلبي / جني أرباح جزئي"
    else:
        signal = "🔴 إشارة بيع قوية"
        
    if avg_traded_value > 2000000:
        settlement = "T+0 / T+1"
    elif avg_traded_value > 500000:
        settlement = "T+1 (سيولة متوسطة)"
    else:
        settlement = "T+2 (سيولة ضعيفة)"
    
    # === نقاط الدخول والأهداف الذكية ووقف الخسارة V3.5 ===
    recent_high_20 = float(high_series.tail(20).max())
    recent_low_20 = float(low_series.tail(20).min())
    effective_atr = max(atr_val, last_close * 0.02)
    
    if score >= 0:
        # نقطة الدخول: السعر الحالي أو أقرب دعم معقول (دون الابتعاد أكثر من 1.5% لتكون قابلة للتنفيذ)
        entry_point = round(last_close, 2)
        if last_close > pivots["S1"] and (last_close - pivots["S1"]) / last_close < 0.015:
            entry_point = round(pivots["S1"], 2)
            
        # وقف الخسارة: وضع الوقف تحت أدنى سعر أخير أو مسافة 1.5 ATR
        # مع ضمان أن الوقف دائماً أسفل الدخول بمسافة أمان لا تقل عن 2% ولا تزيد عن 6%
        sl_candidate = max(last_close - (1.5 * effective_atr), recent_low_20)
        if is_uptrend and st_val > 0 and st_val < last_close * 0.985:
            sl_candidate = max(sl_candidate, st_val)
            
        # ضمان أن وقف الخسارة يقع أسفل نقطة الدخول دوماً بنسبة 2% على الأقل
        stop_loss = round(min(entry_point * 0.98, sl_candidate), 2)
        risk = entry_point - stop_loss
        if risk <= 0:
            risk = round(entry_point * 0.025, 2)
            stop_loss = round(entry_point - risk, 2)
            
        # الهدف المتوقع (Take Profit):
        # يرتكز على قمة الحركة الأخيرة لـ 20 جلسة أو أهداف البيفوت الأعلى أو مضاعف المخاطرة (1.5 إلى 2)
        # لضمان عدم ظهور أهداف وهمية بفارق قروش معدودة
        min_reward = max(risk * 1.5, 1.8 * effective_atr, entry_point * 0.03)
        tp_candidate = entry_point + min_reward
        
        # إذا كانت المقاومة R1 أو R2 تحقق ربحاً كافياً (أكثر من 2.5%) نأخذ بها، وإلا نأخذ قمة آخر 20 شمعة
        if pivots["R1"] > entry_point * 1.025:
            tp_candidate = max(tp_candidate, pivots["R1"])
        if recent_high_20 > entry_point * 1.03:
            tp_candidate = max(tp_candidate, recent_high_20)
            
        take_profit = round(tp_candidate, 2)
        reward = take_profit - entry_point
        rr_ratio = round(reward / risk, 1) if risk > 0 else 1.5
        rr_str = f"1:{rr_ratio}"
        
        entry_str = str(entry_point)
        tp_str = str(take_profit)
        sl_str = str(stop_loss)
    else:
        entry_str, tp_str, sl_str = "انتظار", "-", "-"
        rr_str = "-"
        
    ticker_display = f"{ticker.replace('.CA', '')} - {arabic_name}" if arabic_name else ticker.replace('.CA', '')
    
    if is_valid_for_day_trading:
        # النطاق الجديد V3.0: أقصى +19.5 والأدنى -17 → مجموع 36.5
        perc = int(((score + 17) / 36.5) * 100)
        perc = max(0, min(100, perc)) 
        score_percent = f"{perc}%"
    else:
        score_percent = "غير صالح"

    return {
        "المؤشر": index_name,
        "القطاع": sector_name,
        "نظام التسوية": settlement,
        "الكود": ticker,
        "اسم السهم": ticker_display,
        "السعر الحالي": round(last_close, 2),
        "الدخول المقترح": entry_str,
        "الهدف المتوقع": tp_str,
        "وقف الخسارة": sl_str,
        "المخاطرة:العائد": rr_str,
        "السيولة": vol_status,
        "الزخم (RSI)": round(rsi_14, 1),
        "الحالة الفنية": status_desc,
        "قوة التقييم": score_percent,
        "التوجيه الحالي": signal,
        "Score": score
    }



@st.cache_data(ttl=120, show_spinner=False, max_entries=50)
def get_daily_performance(ticker, arabic_name):
    tv = get_tv()
    if tv:
        try:
            tv_ticker = ticker.replace('.CA', '')
            if tv_ticker in ["QNBA", "QNBE"]:
                tv_ticker = "QNBE"
            elif tv_ticker in ["AUTO", "GBCO"]:
                tv_ticker = "GBCO"
            df_tv = tv.get_hist(symbol=tv_ticker, exchange='EGX', interval=Interval.in_daily, n_bars=2)
            if df_tv is not None and len(df_tv) >= 2:
                close_today = float(df_tv['close'].iloc[-1])
                close_yest = float(df_tv['close'].iloc[-2])
                vol_today = float(df_tv['volume'].iloc[-1])
                
                change_perc = ((close_today - close_yest) / close_yest) * 100
                
                return {
                    "اسم السهم": arabic_name if arabic_name else tv_ticker,
                    "الكود": ticker,
                    "السعر": round(close_today, 3),
                    "التغير (%)": round(change_perc, 2),
                    "حجم التداول": int(vol_today),
                    "قيمة التداول (تقريبية)": int(vol_today * close_today)
                }
        except Exception:
            pass
            
    # المصدر الاحتياطي من Yahoo Finance لضمان عمل تبويب حصاد الجلسة
    try:
        df_yf = yf.download(ticker, period="5d", interval="1d", progress=False)
        if df_yf is not None and len(df_yf) >= 2:
            if isinstance(df_yf.columns, pd.MultiIndex):
                df_yf.columns = df_yf.columns.get_level_values(0)
            close_today = float(df_yf['Close'].iloc[-1])
            close_yest = float(df_yf['Close'].iloc[-2])
            vol_today = float(df_yf['Volume'].iloc[-1])
            change_perc = ((close_today - close_yest) / close_yest) * 100
            
            return {
                "اسم السهم": arabic_name if arabic_name else ticker.replace('.CA', ''),
                "الكود": ticker,
                "السعر": round(close_today, 3),
                "التغير (%)": round(change_perc, 2),
                "حجم التداول": int(vol_today),
                "قيمة التداول (تقريبية)": int(vol_today * close_today)
            }
    except Exception:
        pass
        
    return None
