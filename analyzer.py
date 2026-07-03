import streamlit as st
import yfinance as yf
import pandas as pd
from tvDatafeed import TvDatafeed, Interval
from indicators import *

@st.cache_resource
def get_tv():
    try:
        return TvDatafeed()
    except Exception as e:
        print("tvDatafeed init error:", e)
        return None


@st.cache_data(ttl=300, show_spinner=False, max_entries=200)
def analyze_stock_cached(ticker, yf_period, yf_interval, arabic_name, sector_name, index_name):
    df = pd.DataFrame()
    tv = get_tv()
    
    # 1. المحاولة الأولى باستخدام TradingView (أدق للسوق المصري)
    if tv is not None:
        try:
            tv_interval_map = {"15m": Interval.in_15_minute, "1h": Interval.in_1_hour, "1d": Interval.in_daily}
            tv_interval_val = tv_interval_map.get(yf_interval, Interval.in_daily)
            tv_ticker = ticker.replace('.CA', '')
            df_tv = tv.get_hist(symbol=tv_ticker, exchange='EGX', interval=tv_interval_val, n_bars=600)
            if df_tv is not None and not df_tv.empty:
                df_tv.rename(columns={'open':'Open', 'high':'High', 'low':'Low', 'close':'Close', 'volume':'Volume'}, inplace=True)
                if 'symbol' in df_tv.columns: df_tv.drop(columns=['symbol'], inplace=True)
                df = df_tv
        except Exception as e:
            print(f"TV fetch error for {ticker}: {e}")
            
    # 2. المصدر الاحتياطي (Fallback) من Yahoo Finance
    if df.empty:
        df = yf.download(ticker, period=yf_period, interval=yf_interval, progress=False, auto_adjust=True)
        
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
    
    df['RSI_14'] = calculate_rsi(close_series, window=14)
    df['EMA_9'] = close_series.ewm(span=9, adjust=False).mean()
    df['EMA_21'] = close_series.ewm(span=21, adjust=False).mean()
    df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = calculate_macd(close_series)
    df['BB_Upper'], df['BB_Lower'] = calculate_bb(close_series)
    df['ATR'] = calculate_atr(high_series, low_series, close_series)
    df['OBV'], df['OBV_EMA'] = calculate_obv_trend(close_series, volume_series)
    df['StochRSI_K'], df['StochRSI_D'] = calculate_stoch_rsi(df['RSI_14'])
    df['VWAP_14'] = calculate_vwap(high_series, low_series, close_series, volume_series)
    df['SMA_50'] = close_series.rolling(window=50).mean()
    df['SMA_200'] = close_series.rolling(window=200).mean()
    
    last_close = float(close_series.iloc[-1])
    last_open = float(df['Open'].squeeze().iloc[-1])
    atr_val = float(df['ATR'].iloc[-1])
    rsi_14 = float(df['RSI_14'].iloc[-1])
    ema_9 = float(df['EMA_9'].iloc[-1])
    ema_21 = float(df['EMA_21'].iloc[-1])
    macd = float(df['MACD'].iloc[-1])
    macd_signal = float(df['MACD_Signal'].iloc[-1])
    bb_upper = float(df['BB_Upper'].iloc[-1])
    bb_lower = float(df['BB_Lower'].iloc[-1])
    obv = float(df['OBV'].iloc[-1])
    obv_ema = float(df['OBV_EMA'].iloc[-1])
    stoch_k = float(df['StochRSI_K'].iloc[-1]) if not pd.isna(df['StochRSI_K'].iloc[-1]) else None
    stoch_d = float(df['StochRSI_D'].iloc[-1]) if not pd.isna(df['StochRSI_D'].iloc[-1]) else None
    vwap_14 = float(df['VWAP_14'].iloc[-1]) if not pd.isna(df['VWAP_14'].iloc[-1]) else None
    sma_50 = float(df['SMA_50'].iloc[-1]) if not pd.isna(df['SMA_50'].iloc[-1]) else None
    sma_200 = float(df['SMA_200'].iloc[-1]) if not pd.isna(df['SMA_200'].iloc[-1]) else None
    
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
    
    score = 0
    avg_traded_value = avg_vol_10 * last_close
    is_valid_for_day_trading = True
    if yf_interval == "15m" and avg_traded_value < 1000000:
        is_valid_for_day_trading = False
        
    # === نظام التقييم الفني المطور ===
    
    # 1. فلتر الاتجاه العام (Trend Filter)
    trend_up = False
    if sma_50 is not None:
        if last_close > sma_50:
            trend_up = True
            score += 2  # السعر فوق المتوسط 50 (إيجابي جداً)
        else:
            score -= 2  # السعر تحت المتوسط 50 (سلبي)
            
    # 2. الزخم قصير الأجل (EMA)
    if ema_9 > ema_21: 
        score += 1
    elif ema_9 < ema_21: 
        score -= 1
        
    # 3. تقاطع الماكد (MACD)
    if macd > macd_signal: 
        score += 1
        if macd < 0: # تقاطع إيجابي تحت خط الصفر (بداية ارتداد)
            score += 1 
    elif macd < macd_signal: 
        score -= 1
        
    # 4. مؤشر القوة النسبية (RSI) - تجنب السكاكين الساقطة
    if rsi_14 < 35:
        # السهم متشبع بيعياً.. هل هناك بوادر ارتداد؟
        if macd > macd_signal or last_close > last_open:
            score += 2 # ارتداد مؤكد
        else:
            score -= 1 # ترند هابط قوي (سكين ساقط)
    elif rsi_14 > 70:
        score -= 1 # السهم متشبع شرائياً (جني أرباح)
    elif 40 <= rsi_14 <= 60 and trend_up:
        score += 1 # تجميع صحي في ترند صاعد
        
    # 5. السيولة والـ VWAP
    if vwap_14 is not None:
        if last_close > vwap_14: 
            score += 1
        elif last_close < vwap_14: 
            score -= 1
            
    # تأكيد الاختراق بالسيولة
    if vol_spike >= 150:
        if last_close >= last_open: # شمعة خضراء بسيولة عالية
            score += 2
        else: # شمعة حمراء بسيولة بيعية عالية
            score -= 2
            
    # 6. السيولة التراكمية (OBV)
    if obv > obv_ema: 
        score += 1
    elif obv < obv_ema: 
        score -= 1
    
    if not is_valid_for_day_trading:
        score = -10
        signal = "🚫 لا يدعم T+0 (سيولة ضعيفة)"
    elif score >= 6:
        signal = "🟢 إشارة شراء قوية"
    elif score >= 2:
        signal = "🟡 إيجابي / تجميع"
    elif score >= -2:
        signal = "⚪ محايد / استقرار"
    elif score >= -5:
        signal = "🟠 سلبي / جني أرباح جزئي"
    else:
        signal = "🔴 إشارة بيع قوية"
        
    if avg_traded_value > 2000000:
        settlement = "T+0 / T+1"
    elif avg_traded_value > 500000:
        settlement = "T+1 (سيولة متوسطة)"
    else:
        settlement = "T+2 (سيولة ضعيفة)"
        
    entry_point = last_close
    stop_loss = last_close - (1.5 * atr_val)
    take_profit = last_close + (3.0 * atr_val)
    
    if score < 0:
        entry_str, tp_str, sl_str = "انتظار", "-", "-"
    else:
        entry_str = str(round(entry_point, 2))
        tp_str = str(round(take_profit, 2))
        sl_str = str(round(stop_loss, 2))
        
    ticker_display = f"{ticker.replace('.CA', '')} - {arabic_name}" if arabic_name else ticker.replace('.CA', '')
    
    if is_valid_for_day_trading:
        # تحويل التقييم لنسبة مئوية (الحد الأقصى للسكور الجديد حوالي 12 والحد الأدنى -10)
        # لتجنب كسر النسب، سنقوم بحسابها على أساس 12/-12
        perc = int(((score + 12) / 24) * 100)
        perc = max(0, min(100, perc)) 
        score_percent = f"{perc}%"
    else:
        score_percent = "غير صالح"

    # حساب نسبة المخاطرة للعائد (Risk:Reward)
    if score >= 0:
        risk = entry_point - stop_loss
        reward = take_profit - entry_point
        if risk > 0:
            rr_ratio = round(reward / risk, 1)
            rr_str = f"1:{rr_ratio}"
        else:
            rr_str = "-"
    else:
        rr_str = "-"

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
        "قوة التقييم": score_percent,
        "التوجيه الحالي": signal,
        "Score": score
    }



@st.cache_data(ttl=120, show_spinner=False, max_entries=50)
def get_daily_performance(ticker, arabic_name):
    tv = get_tv()
    if not tv: return None
    
    try:
        tv_ticker = ticker.replace('.CA', '')
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
    except Exception as e:
        pass
    return None
