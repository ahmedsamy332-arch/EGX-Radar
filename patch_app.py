import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Imports
content = content.replace("import pandas as pd", "import pandas as pd\nimport json\nfrom streamlit_local_storage import LocalStorage")

# 2. Add Cached Function after calculate_obv_trend
func_code = """
@st.cache_data(ttl=300, show_spinner=False)
def analyze_stock_cached(ticker, yf_period, yf_interval, arabic_name, sector_name, index_name):
    df = yf.download(ticker, period=yf_period, interval=yf_interval, progress=False)
    if df.empty:
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
    
    last_close = float(close_series.iloc[-1])
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
        
    if rsi_14 < 30: score += 1
    elif rsi_14 > 70: score -= 1
    if ema_9 > ema_21: score += 1
    elif ema_9 < ema_21: score -= 1
    if macd > macd_signal: score += 1
    elif macd < macd_signal: score -= 1
    if last_close <= bb_lower: score += 1
    elif last_close >= bb_upper: score -= 1
    if obv > obv_ema: score += 1
    elif obv < obv_ema: score -= 1
    
    if not is_valid_for_day_trading:
        score = -10
        signal = "🚫 لا يدعم T+0 (سيولة ضعيفة)"
    elif score >= 2:
        signal = "🟢 إشارة شراء قوية"
    elif score == 1:
        signal = "🟡 إيجابي / تجميع"
    elif score == 0:
        signal = "⚪ محايد / استقرار"
    elif score == -1:
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
    
    return {
        "المؤشر": index_name,
        "القطاع": sector_name,
        "نظام التسوية": settlement,
        "اسم السهم": ticker_display,
        "السعر الحالي": round(last_close, 2),
        "الدخول المقترح": entry_str,
        "الهدف المتوقع": tp_str,
        "وقف الخسارة": sl_str,
        "السيولة": vol_status,
        "الزخم (RSI)": round(rsi_14, 1),
        "التوجيه الحالي": signal,
        "Score": score
    }
"""
content = content.replace("def calculate_obv_trend(close, volume, ema_window=10):\n    direction = pd.Series(0, index=close.index)\n    direction[close > close.shift(1)] = 1\n    direction[close < close.shift(1)] = -1\n    obv = (direction * volume).cumsum()\n    obv_ema = obv.ewm(span=ema_window, adjust=False).mean()\n    return obv, obv_ema", 
"def calculate_obv_trend(close, volume, ema_window=10):\n    direction = pd.Series(0, index=close.index)\n    direction[close > close.shift(1)] = 1\n    direction[close < close.shift(1)] = -1\n    obv = (direction * volume).cumsum()\n    obv_ema = obv.ewm(span=ema_window, adjust=False).mean()\n    return obv, obv_ema\n" + func_code)

# 3. Add Local Storage & Favorites logic right before specific_search_stocks
favorites_logic = """
# 3. إعدادات التحليل والمدى الزمني
st.subheader("⚙️ إعدادات التحليل (تُطبق على المفضلة والفحص)")
timeframe = st.radio(
    "اختر المدى الزمني للرادار:",
    ["مضاربة لحظية (15 دقيقة) - لتداول نفس الجلسة", 
     "مضاربة قصيرة (ساعة) - لسوينجات أيام", 
     "تداول يومي (شمعة يومية) - للاتجاه العام والمستثمر"],
    index=2
)

if "15 دقيقة" in timeframe:
    yf_period = "60d"
    yf_interval = "15m"
elif "ساعة" in timeframe:
    yf_period = "730d"
    yf_interval = "1h"
else:
    yf_period = "2y"
    yf_interval = "1d"

egx30_list = ["COMI.CA", "FWRY.CA", "EFIH.CA", "EGAL.CA", "ABUK.CA", "TMGH.CA", "HRHO.CA", "SWDY.CA", "ETEL.CA", "ESRS.CA", "AMOC.CA", "SKPC.CA", "HELI.CA", "PHDC.CA", "MFPC.CA", "MASR.CA", "ORAS.CA", "ORWE.CA", "ISPH.CA", "CIEB.CA", "ADIB.CA", "AUTO.CA", "CLHO.CA", "JUFO.CA", "SUGR.CA", "BTFH.CA", "DOMT.CA", "OIH.CA", "MTIE.CA", "CCAP.CA", "EMFD.CA", "RMDA.CA", "QNBA.CA", "HDBK.CA", "SAUD.CA"]
egx70_list = [t for t in stock_names.keys() if t not in egx30_list]
egx100_list = egx30_list + egx70_list

st.markdown("---")
st.subheader("⭐ الأسهم المفضلة (متابعة حية)")
st.write("الأسهم اللي هتختارها هنا هتفضل متسجلة في متصفحك وهيتعملها تحليل فوري أول ما تفتح البرنامج.")

localS = LocalStorage()
fav_raw = localS.getItem("egx_favorites")
favorites_list = []
if fav_raw:
    if isinstance(fav_raw, str):
        try:
            favorites_list = json.loads(fav_raw)
        except:
            pass
    elif isinstance(fav_raw, list):
        favorites_list = fav_raw

new_favorites = st.multiselect(
    "إدارة قائمتي المفضلة:",
    options=list(stock_names.keys()),
    default=[x for x in favorites_list if x in stock_names.keys()],
    format_func=lambda x: f"{x.replace('.CA', '')} - {stock_names[x]}"
)

if new_favorites != favorites_list:
    localS.setItem("egx_favorites", json.dumps(new_favorites))
    favorites_list = new_favorites

if favorites_list:
    st.write("📊 **إشارات المفضلة الآن:**")
    cols = st.columns(min(len(favorites_list), 4) if len(favorites_list) > 0 else 1)
    
    for i, fav_ticker in enumerate(favorites_list):
        with cols[i % 4]:
            arabic_name = stock_names.get(fav_ticker, "")
            sector_name = stock_sectors.get(fav_ticker, "غير محدد")
            index_name = "EGX30" if fav_ticker in egx30_list else ("EGX70" if fav_ticker in egx70_list else "-")
            
            res = analyze_stock_cached(fav_ticker, yf_period, yf_interval, arabic_name, sector_name, index_name)
            if res:
                signal = res['التوجيه الحالي'].split(' ')[0] # just the emoji
                st.markdown(f"<div style='border:1px solid #ddd; padding:10px; border-radius:8px; text-align:center;'><b>{fav_ticker.replace('.CA', '')}</b><br>{signal} {res['السعر الحالي']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='border:1px solid #ddd; padding:10px; border-radius:8px; text-align:center;'><b>{fav_ticker.replace('.CA', '')}</b><br>⏳ جاري..</div>", unsafe_allow_html=True)
st.markdown("---")
"""

content = content.replace('specific_search_stocks = st.multiselect(\n    "ابحث باسم السهم (عربي) أو الكود (إنجليزي):",\n    options=list(stock_names.keys()),\n    default=[],\n    format_func=lambda x: f"{x.replace(\'.CA\', \'\')} - {stock_names[x]}"\n)',
favorites_logic + '\n' + 'specific_search_stocks = st.multiselect(\n    "ابحث باسم السهم (عربي) أو الكود (إنجليزي):",\n    options=list(stock_names.keys()),\n    default=[],\n    format_func=lambda x: f"{x.replace(\'.CA\', \'\')} - {stock_names[x]}"\n)')

# 4. Modify selection_method options to include favorites
content = content.replace('["تحديد يدوي (حسب القطاعات)", "فحص مؤشر EGX30 بالكامل", "فحص مؤشر EGX70 بالكامل", "فحص البورصة بالكامل (كل الأسهم)", "لا أريد (سأكتفي بأسهم السيرش فقط)"]',
'["تحديد يدوي (حسب القطاعات)", "فحص مؤشر EGX30 بالكامل", "فحص مؤشر EGX70 بالكامل", "فحص البورصة بالكامل (كل الأسهم)", "فحص قائمتي المفضلة", "لا أريد (سأكتفي بأسهم السيرش فقط)"]')

# 5. Remove the old timeframe selection since we moved it up
content = re.sub(r'# 3\. إعدادات التحليل والمدى الزمني\nst\.subheader\("⚙️ إعدادات التحليل"\)\ntimeframe = st\.radio\([\s\S]*?yf_interval = "1d"', '', content)

# 6. Add favorites logic to selected_stocks
content = content.replace('elif selection_method == "لا أريد (سأكتفي بأسهم السيرش فقط)":\n    pass',
'elif selection_method == "فحص قائمتي المفضلة":\n    selected_stocks.extend(favorites_list)\nelif selection_method == "لا أريد (سأكتفي بأسهم السيرش فقط)":\n    pass')

# 7. Replace the big loop in st.button with the cached function call
big_loop = """            df = yf.download(ticker, period=yf_period, interval=yf_interval, progress=False)
            
            if df.empty:
                continue
                
            # حساب المؤشرات
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
            
            # جلب بيانات آخر جلسة قفلت
            last_close = float(close_series.iloc[-1])
            atr_val = float(df['ATR'].iloc[-1])
            rsi_14 = float(df['RSI_14'].iloc[-1])
            ema_9 = float(df['EMA_9'].iloc[-1])
            ema_21 = float(df['EMA_21'].iloc[-1])
            macd = float(df['MACD'].iloc[-1])
            macd_signal = float(df['MACD_Signal'].iloc[-1])
            macd_hist = float(df['MACD_Hist'].iloc[-1])
            bb_upper = float(df['BB_Upper'].iloc[-1])
            bb_lower = float(df['BB_Lower'].iloc[-1])
            obv = float(df['OBV'].iloc[-1])
            obv_ema = float(df['OBV_EMA'].iloc[-1])
            
            # رادار السيولة المفاجئة (Volume Spikes)
            volume_sma_10 = volume_series.rolling(window=10).mean()
            if len(volume_sma_10) > 0 and pd.notna(volume_sma_10.iloc[-1]):
                last_vol = float(volume_series.iloc[-1])
                avg_vol_10 = float(volume_sma_10.iloc[-1])
                vol_spike = (last_vol / avg_vol_10) * 100 if avg_vol_10 > 0 else 0
            else:
                last_vol = 0
                avg_vol_10 = 0
                vol_spike = 0
                
            if vol_spike >= 300:
                vol_status = f"🔥 انفجار ({int(vol_spike)}%)"
            elif vol_spike >= 150:
                vol_status = f"⚡ عالية ({int(vol_spike)}%)"
            else:
                vol_status = "طبيعي"
            
            # نظام تقييم النقاط لتحديد قوة الإشارة
            score = 0
            
            # فلتر الذكاء: استبعاد الأسهم غير الصالحة للمضاربة اللحظية (T+0) بسبب ضعف السيولة
            # القيمة المتداولة التقديرية = متوسط الحجم * السعر
            avg_traded_value = avg_vol_10 * last_close
            is_valid_for_day_trading = True
            
            if yf_interval == "15m":
                # إذا كانت السيولة المتداولة في المتوسط أقل من مليون جنيه، لا يُنصح بالمضاربة اللحظية فيه
                if avg_traded_value < 1000000:
                    is_valid_for_day_trading = False
            
            # 1. RSI (الزخم)
            if rsi_14 < 30: score += 1
            elif rsi_14 > 70: score -= 1
            
            # 2. EMA Trend (الاتجاه)
            if ema_9 > ema_21: score += 1
            elif ema_9 < ema_21: score -= 1
            
            # 3. MACD (تأكيد الاتجاه)
            if macd > macd_signal: score += 1
            elif macd < macd_signal: score -= 1
            
            # 4. Bollinger Bands (الارتدادات)
            if last_close <= bb_lower: score += 1
            elif last_close >= bb_upper: score -= 1
            
            # 5. الفوليوم (السيولة الذكية OBV)
            if obv > obv_ema: score += 1
            elif obv < obv_ema: score -= 1
            
            # تحديد التوجيه بناءً على النقاط
            if not is_valid_for_day_trading:
                score = -10 # إبعاده عن قائمة الشراء في الترتيب
                signal = "🚫 لا يدعم T+0 (سيولة ضعيفة)"
            elif score >= 2:
                signal = "🟢 إشارة شراء قوية"
            elif score == 1:
                signal = "🟡 إيجابي / تجميع"
            elif score == 0:
                signal = "⚪ محايد / استقرار"
            elif score == -1:
                signal = "🟠 سلبي / جني أرباح جزئي"
            else: # score <= -2
                signal = "🔴 إشارة بيع قوية"
            
            # إضافة النتيجة للقائمة
            arabic_name = stock_names.get(ticker, "")
            sector_name = stock_sectors.get(ticker, "غير محدد")
            ticker_display = f"{ticker.replace('.CA', '')} - {arabic_name}" if arabic_name else ticker.replace('.CA', '')
            
            # تحديد المؤشر
            if ticker in egx30_list:
                index_name = "EGX30"
            elif ticker in egx70_list:
                index_name = "EGX70"
            else:
                index_name = "-"
                
            # حساب نظام التسوية (T+0, T+1, T+2)
            # بما أن معظم أسهم EGX100 في القائمة (أ) و (ب) فهي تدعم T+0 / T+1
            # لكننا نضع فلتر أمان بناءً على السيولة لعدم التورط في سهم ضعيف
            if avg_traded_value > 2000000:
                settlement = "T+0 / T+1"
            elif avg_traded_value > 500000:
                settlement = "T+1 (سيولة متوسطة)"
            else:
                settlement = "T+2 (سيولة ضعيفة)"
            
            # حساب نقاط الدخول والخروج بناءً على التقلب (ATR) للإشارات الإيجابية
            entry_point = last_close
            stop_loss = last_close - (1.5 * atr_val)
            take_profit = last_close + (3.0 * atr_val)
            
            if score < 0:
                entry_str = "انتظار"
                tp_str = "-"
                sl_str = "-"
            else:
                entry_str = str(round(entry_point, 2))
                tp_str = str(round(take_profit, 2))
                sl_str = str(round(stop_loss, 2))
            
            results.append({
                "المؤشر": index_name,
                "القطاع": sector_name,
                "نظام التسوية": settlement,
                "اسم السهم": ticker_display,
                "السعر الحالي": round(last_close, 2),
                "الدخول المقترح": entry_str,
                "الهدف المتوقع": tp_str,
                "وقف الخسارة": sl_str,
                "السيولة": vol_status,
                "الزخم (RSI)": round(rsi_14, 1),
                "التوجيه الحالي": signal,
                "Score": score
            })"""

new_loop = """            arabic_name = stock_names.get(ticker, "")
            sector_name = stock_sectors.get(ticker, "غير محدد")
            index_name = "EGX30" if ticker in egx30_list else ("EGX70" if ticker in egx70_list else "-")
            
            res = analyze_stock_cached(ticker, yf_period, yf_interval, arabic_name, sector_name, index_name)
            if res:
                results.append(res)"""

content = content.replace(big_loop, new_loop)

# Fix egx30_list definition duplication
content = content.replace('egx30_list = ["COMI.CA", "FWRY.CA", "EFIH.CA", "EGAL.CA", "ABUK.CA", "TMGH.CA", "HRHO.CA", "SWDY.CA", "ETEL.CA", "ESRS.CA", "AMOC.CA", "SKPC.CA", "HELI.CA", "PHDC.CA", "MFPC.CA", "MASR.CA", "ORAS.CA", "ORWE.CA", "ISPH.CA", "CIEB.CA", "ADIB.CA", "AUTO.CA", "CLHO.CA", "JUFO.CA", "SUGR.CA", "BTFH.CA", "DOMT.CA", "OIH.CA", "MTIE.CA", "CCAP.CA", "EMFD.CA", "RMDA.CA", "QNBA.CA", "HDBK.CA", "SAUD.CA"]\negx70_list = [t for t in stock_names.keys() if t not in egx30_list]\negx100_list = egx30_list + egx70_list\n\n# نبدأ القائمة بالأسهم اللي اختارها في السيرش المخصص', '# نبدأ القائمة بالأسهم اللي اختارها في السيرش المخصص')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
