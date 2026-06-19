import streamlit as st
import yfinance as yf
import pandas as pd

import firebase_client as fb
from streamlit_js_eval import streamlit_js_eval

def calculate_rsi(data, window=7):
    delta = data.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=window-1, adjust=False).mean()
    ema_down = down.ewm(com=window-1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

def calculate_macd(close):
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist

def calculate_bb(close, window=20):
    sma = close.rolling(window=window).mean()
    std = close.rolling(window=window).std(ddof=0)
    upper = sma + (std * 2)
    lower = sma - (std * 2)
    return upper, lower

def calculate_atr(high, low, close, window=14):
    high_low = high - low
    high_close = (high - close.shift()).abs()
    low_close = (low - close.shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(com=window-1, adjust=False).mean()

def calculate_obv_trend(close, volume, ema_window=10):
    direction = pd.Series(0, index=close.index)
    direction[close > close.shift(1)] = 1
    direction[close < close.shift(1)] = -1
    obv = (direction * volume).cumsum()
    obv_ema = obv.ewm(span=ema_window, adjust=False).mean()
    return obv, obv_ema

def calculate_stoch_rsi(rsi_series, window=14, smooth_k=3, smooth_d=3):
    rsi_min = rsi_series.rolling(window=window).min()
    rsi_max = rsi_series.rolling(window=window).max()
    stoch_rsi = (rsi_series - rsi_min) / (rsi_max - rsi_min + 1e-10)
    stoch_rsi_k = stoch_rsi.rolling(window=smooth_k).mean() * 100
    stoch_rsi_d = stoch_rsi_k.rolling(window=smooth_d).mean()
    return stoch_rsi_k, stoch_rsi_d

def calculate_vwap(high, low, close, volume, window=14):
    typical_price = (high + low + close) / 3
    tp_vol = typical_price * volume
    vwap = tp_vol.rolling(window=window).sum() / volume.rolling(window=window).sum()
    return vwap

@st.cache_data(ttl=300, show_spinner=False)
def analyze_stock_cached(ticker, yf_period, yf_interval, arabic_name, sector_name, index_name):
    # auto_adjust=True مهم جداً في السوق المصري عشان تعديل الأسعار بناءً على تجزئة الأسهم وتوزيعات الأرباح
    df = yf.download(ticker, period=yf_period, interval=yf_interval, progress=False, auto_adjust=True)
    if df.empty:
        return None
        
    # تنظيف البيانات من أي أيام إجازات أو بيانات ناقصة
    df = df.ffill().dropna()
        
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
    
    if stoch_k is not None and stoch_d is not None:
        if stoch_k > stoch_d and stoch_k < 80: score += 1
        elif stoch_k < stoch_d and stoch_k > 20: score -= 1
        
    if vwap_14 is not None:
        if last_close > vwap_14: score += 1
        elif last_close < vwap_14: score -= 1
        
    if sma_50 is not None and sma_200 is not None:
        if sma_50 > sma_200: score += 1
        elif sma_50 < sma_200: score -= 1
    
    if not is_valid_for_day_trading:
        score = -10
        signal = "🚫 لا يدعم T+0 (سيولة ضعيفة)"
    elif score >= 4:
        signal = "🟢 إشارة شراء قوية"
    elif score >= 1:
        signal = "🟡 إيجابي / تجميع"
    elif score >= -1:
        signal = "⚪ محايد / استقرار"
    elif score >= -4:
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
        # تحويل التقييم من [-8, 8] إلى نسبة مئوية [0%, 100%]
        # حيث 8 تعني 100% (شراء قوي جداً) و -8 تعني 0% (بيع قوي جداً)
        perc = int(((score + 8) / 16) * 100)
        perc = max(0, min(100, perc)) # للحماية من أي قيمة غير متوقعة
        score_percent = f"{perc}%"
    else:
        score_percent = "غير صالح"

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
        "قوة التقييم": score_percent,
        "التوجيه الحالي": signal,
        "Score": score
    }


# 1. إعدادات الصفحة لتناسب الموبايل
st.set_page_config(page_title="نسر البورصة المصرية", layout="centered")

# CSS مخصص لتحسين الخطوط والأنيميشن
st.markdown("""
<style>
/* إخفاء أدوات Streamlit اللي بتظهر جوه التطبيق فقط */
.stAppDeployButton, [data-testid="stAppDeployButton"] {
    display: none !important;
}
footer {visibility: hidden;}
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Cairo', sans-serif !important;
}

/* Button styling & animation */
.stButton>button {
    background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-weight: 700 !important;
    transition: all 0.3s ease !important;
}
.stButton>button:hover {
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 5px 15px rgba(0,0,0,0.3) !important;
}

/* Title styling */
h1 {
    color: #1e3c72 !important;
    animation: slideDown 0.6s ease-out;
}
@keyframes slideDown {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Copyright banner glow effect */
.copyright-banner {
    transition: all 0.3s ease;
    border: 1px solid rgba(0,0,0,0.05);
}
.copyright-banner:hover {
    box-shadow: 0 0 15px rgba(0, 86, 179, 0.15);
    transform: scale(1.01);
}

/* Fade in for the tables and elements */
.stDataFrame {
    animation: fadeIn 0.8s ease-in-out;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)

# عنوان الموقع
st.markdown("<h1 style='text-align: center;'>🦅 نسر البورصة المصرية</h1>", unsafe_allow_html=True)

# حقوق الملكية (Copyright)
st.markdown("""
<div class='copyright-banner' style='text-align: center; margin-top: -15px; margin-bottom: 20px; padding: 10px; border-radius: 8px; background: rgba(0,0,0,0.03);'>
    <span style='font-size: 13px; color: #666; font-family: monospace;'>DEVELOPED & ENGINEERED BY</span>
    <br>
    <span style='font-size: 20px; font-weight: 900; letter-spacing: 2px; color: #0056b3; font-family: "Arial Black", sans-serif;'>AHMED SAMY</span>
    <br>
    <span style='font-size: 11px; color: #999; font-family: monospace;'>© 2026 All Rights Reserved</span>
</div>
""", unsafe_allow_html=True)
import extra_streamlit_components as stx
cookie_manager = stx.CookieManager(key="cookie_manager")

# معالجة حفظ أو مسح الكوكيز من الجلسة السابقة قبل أي شيء آخر
if "token_to_save" in st.session_state:
    cookie_manager.set("egx_refresh_token", st.session_state["token_to_save"], max_age=30*24*60*60)
    del st.session_state["token_to_save"]

if "token_to_delete" in st.session_state:
    cookie_manager.delete("egx_refresh_token")
    del st.session_state["token_to_delete"]

# Session State Variables
if "user" not in st.session_state:
    st.session_state["user"] = None
if "user_data" not in st.session_state:
    st.session_state["user_data"] = {"favorites": [], "portfolio": []}

# قراءة التوكن المحفوظ (بيكون متوفر دايماً بعد تحميل الصفحة)
saved_token = cookie_manager.get("egx_refresh_token")

# محاولة تسجيل الدخول التلقائي من الكوكيز
if st.session_state["user"] is None and saved_token and isinstance(saved_token, str):
    try:
        user = fb.refresh_id_token(saved_token)
        st.session_state["user"] = user
        st.session_state["user_data"] = fb.get_user_data(user["localId"], user["idToken"])
        st.rerun()
    except:
        pass # التوكن غير صالح أو منتهي

# شاشة تسجيل الدخول / إنشاء حساب
if st.session_state["user"] is None:
    st.markdown("<h2 style='text-align: center; color: #1e3c72;'>🔐 تسجيل الدخول للرادار</h2>", unsafe_allow_html=True)
    st.write("برجاء تسجيل الدخول للوصول لمحفظتك ومفضلاتك. إذا لم تكن تمتلك حساباً، أدخل إيميل وكلمة مرور واضغط على إنشاء حساب جديد.")
    
    auth_col1, auth_col2, auth_col3 = st.columns([1,2,1])
    with auth_col2:
        email = st.text_input("البريد الإلكتروني (Email)", placeholder="name@example.com")
        password = st.text_input("كلمة المرور (Password)", type="password")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("تسجيل الدخول", use_container_width=True):
                if email and password:
                    with st.spinner("جاري تسجيل الدخول..."):
                        try:
                            user = fb.sign_in(email, password)
                            st.session_state["user"] = user
                            st.session_state["user_data"] = fb.get_user_data(user["localId"], user["idToken"])
                            # نطلب من المتصفح يحفظ التوكن في اللفة الجاية
                            st.session_state["token_to_save"] = user.get("refreshToken", "")
                            st.rerun()
                        except Exception as e:
                            st.error(f"خطأ في الدخول: {str(e)}")
                else:
                    st.warning("أدخل الإيميل والباسورد")
                    
        with col_btn2:
            if st.button("إنشاء حساب جديد", use_container_width=True):
                if email and password:
                    if len(password) < 6:
                        st.error("كلمة المرور يجب أن تكون 6 أحرف على الأقل.")
                    else:
                        with st.spinner("جاري إنشاء الحساب..."):
                            try:
                                user = fb.sign_up(email, password)
                                st.session_state["user"] = user
                                st.session_state["user_data"] = {"favorites": [], "portfolio": []}
                                fb.update_user_data(user["localId"], user["idToken"], st.session_state["user_data"])
                                # نطلب من المتصفح يحفظ التوكن في اللفة الجاية
                                st.session_state["token_to_save"] = user.get("refreshToken", "")
                                st.success("تم إنشاء الحساب بنجاح! جاري الدخول...")
                                st.rerun()
                            except Exception as e:
                                st.error(f"خطأ في الإنشاء: {str(e)}")
                else:
                    st.warning("أدخل الإيميل والباسورد")
    
    st.stop()

# زر تسجيل الخروج
with st.sidebar:
    st.write(f"👤 {st.session_state['user'].get('email', '')}")
    if st.button("تسجيل الخروج"):
        st.session_state["token_to_delete"] = True
        st.session_state["user"] = None
        st.session_state["user_data"] = {"favorites": [], "portfolio": []}
        st.rerun()



# 2. قائمة الأسهم الافتراضية (مقسمة لقطاعات تغطي مؤشرات السوق EGX30, EGX70, EGX100)

egx_stocks = {
    "🏦 البنوك": {
        "COMI.CA": "البنك التجاري الدولي",
        "CIEB.CA": "كريدي أجريكول",
        "ADIB.CA": "مصرف أبو ظبي الإسلامي",
        "EGBE.CA": "البنك المصري الخليجي",
        "FAIT.CA": "بنك فيصل الإسلامي",
        "EXPA.CA": "البنك المصري لتنمية الصادرات",
        "CANA.CA": "بنك قناة السويس",
        "QNBA.CA": "بنك قطر الوطني",
        "HDBK.CA": "بنك التعمير والإسكان",
        "SAUD.CA": "بنك البركة"
    },
    "🏢 العقارات والمقاولات": {
        "TMGH.CA": "مجموعة طلعت مصطفى",
        "PHDC.CA": "بالم هيلز",
        "HELI.CA": "مصر الجديدة للإسكان",
        "MASR.CA": "مدينة مصر",
        "EMFD.CA": "إعمار مصر",
        "OCDI.CA": "سوديك",
        "ARAB.CA": "المطورون العرب",
        "UNIT.CA": "المتحدة للإسكان",
        "SWDY.CA": "السويدي إيليكتريك",
        "ORAS.CA": "أوراسكوم كونستراكشون",
        "ZMID.CA": "زهراء المعادي",
        "EHDR.CA": "المصريين للإسكان",
        "ELSH.CA": "الشمس للإسكان",
        "RTVC.CA": "ريمكو للقرى السياحية",
        "GGCC.CA": "الجيزة العامة للمقاولات",
        "ORHD.CA": "أوراسكوم للتنمية",
        "MINA.CA": "مينا للاستثمار السياحي",
        "EGTS.CA": "المصرية للمنتجعات السياحية",
        "UEGC.CA": "الصعيد العامة للمقاولات",
        "ISMA.CA": "الإسماعيلية للتطوير",
        "ADRI.CA": "العقارية للبنوك"
    },
    "🛢️ الموارد الأساسية والبتروكيماويات والأسمنت": {
        "ABUK.CA": "أبو قير للأسمدة",
        "MFPC.CA": "موبكو",
        "SKPC.CA": "سيدي كرير",
        "AMOC.CA": "أموك",
        "EGAL.CA": "مصر للألومنيوم",
        "ESRS.CA": "حديد عز",
        "EFIC.CA": "المالية والصناعية",
        "IRON.CA": "الحديد والصلب",
        "SVCE.CA": "جنوب الوادي للأسمنت",
        "ARCC.CA": "الإسكندرية للأسمنت",
        "EGCH.CA": "المصرية للكيمياويات",
        "MCQE.CA": "مصر لصناعة الكيماويات",
        "ASCM.CA": "أسيك للتعدين",
        "PACH.CA": "البويات والصناعات (باكين)",
        "MICH.CA": "مصر لصناعة الكيماويات"
    },
    "💻 الاتصالات وتكنولوجيا المعلومات والتعليم": {
        "FWRY.CA": "فوري",
        "EFIH.CA": "إي فاينانس",
        "ETEL.CA": "المصرية للاتصالات",
        "RACC.CA": "راية مراكز الاتصالات",
        "CIRA.CA": "القاهرة للاستثمار (سيرا)",
        "OIH.CA": "أوراسكوم للاستثمار"
    },
    "📈 الخدمات المالية والاستثمار": {
        "HRHO.CA": "إي إف جي القابضة",
        "BTFH.CA": "بلتون المالية",
        "CCAP.CA": "القلعة للاستثمارات",
        "PRMH.CA": "برايم القابضة",
        "RAYA.CA": "راية القابضة",
        "BINV.CA": "بي إنفستمنتس",
        "AMIA.CA": "الملتقى العربي للاستثمارات",
        "ODIN.CA": "أودن للاستثمارات",
        "MOIN.CA": "المهندس للتأمين",
        "ATLC.CA": "الأهلي للتنمية والاستثمار",
        "CICH.CA": "سي آي كابيتال",
        "CECE.CA": "القاهرة الوطنية للاستثمار",
        "AIFI.CA": "العربية للاستثمارات"
    },
    "💊 الرعاية الصحية والأدوية": {
        "ISPH.CA": "ابن سينا فارما",
        "CLHO.CA": "كليوباترا مستشفى",
        "RMDA.CA": "راميدا",
        "CPMI.CA": "كليوباترا ميديكال",
        "IPCI.CA": "إيبيكو للأدوية",
        "MIPH.CA": "مينا فارم",
        "NIPH.CA": "النيل للأدوية",
        "MCRO.CA": "ماكرو جروب"
    },
    "🛒 الأغذية والسلع الاستهلاكية والمنسوجات": {
        "JUFO.CA": "جهينة",
        "SUGR.CA": "الدلتا للسكر",
        "DOMT.CA": "دومتي",
        "EFID.CA": "إيديتا",
        "ORWE.CA": "النساجون الشرقيون",
        "AUTO.CA": "جي بي كوربوريشن",
        "MTIE.CA": "إم إم جروب",
        "DSCW.CA": "دايس للملابس",
        "ACGC.CA": "العربية لحليج الأقطان",
        "POUL.CA": "القاهرة للدواجن",
        "SPIN.CA": "سبينالكس",
        "ELEC.CA": "إلكتروكابل",
        "MPCO.CA": "المنصورة للدواجن",
        "KABO.CA": "النصر للملابس (كابو)",
        "ELKA.CA": "القاهرة للزيوت والصابون",
        "ZEOT.CA": "الإسكندرية للزيوت",
        "ICMI.CA": "الدولية للمحاصيل"
    },
    "🚢 الشحن والنقل وقطاعات أخرى": {
        "ALCN.CA": "الإسكندرية لتداول الحاويات",
        "UASG.CA": "المتحدة للشحن",
        "CSAG.CA": "القناة للتوكيلات الملاحية",
        "ETRS.CA": "المصرية لخدمات النقل",
        "EGYT.CA": "إيجيترانس",
        "TRNS.CA": "ترانس كارجو",
        "ENGC.CA": "الهندسية للإنشاء",
        "ARVA.CA": "أراب فالف",
        "SDTI.CA": "شرم دريمز",
        "PRDC.CA": "بيراميزا للفنادق",
        "ROTO.CA": "رواد السياحة"
    }
}

stock_names = {}
stock_sectors = {}

for sector, stocks in egx_stocks.items():
    clean_sector_name = sector.split(' ', 1)[1] if ' ' in sector else sector
    stock_names.update(stocks)
    for ticker in stocks.keys():
        stock_sectors[ticker] = clean_sector_name


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

favorites_list = st.session_state['user_data'].get('favorites', [])
portfolio_list = st.session_state['user_data'].get('portfolio', [])
st.markdown('---')
tabs = st.tabs(['📊 رادار السوق', '⭐ المفضلة', '💼 محفظتي الذكية'])

with tabs[0]:

    specific_search_stocks = st.multiselect(
        "ابحث باسم السهم (عربي) أو الكود (إنجليزي):",
        options=list(stock_names.keys()),
        default=[],
        format_func=lambda x: f"{x.replace('.CA', '')} - {stock_names[x]}"
    )

    st.subheader("📋 طريقة اختيار الأسهم للمراقبة")
    selection_method = st.radio(
        "هل ترغب في فحص مجموعات أو مؤشرات؟",
        ["تحديد يدوي (حسب المؤشرات)", "فحص مؤشر EGX30 بالكامل", "فحص مؤشر EGX70 بالكامل", "فحص البورصة بالكامل (كل الأسهم)", "فحص قائمتي المفضلة", "لا أريد (سأكتفي بأسهم السيرش فقط)"],
        horizontal=True
    )

    # نبدأ القائمة بالأسهم اللي اختارها في السيرش المخصص
    selected_stocks = list(specific_search_stocks)

    if selection_method == "تحديد يدوي (حسب المؤشرات)":
        st.write("💡 ملحوظة: الفحص بياخد حوالي ثانية لكل سهم، اختر أسهمك بعناية.")
        cols = st.columns(3)
        with cols[0]:
            with st.expander("مؤشر EGX 30", expanded=True):
                selected_egx30 = st.multiselect(
                    "اختر أسهم EGX30:",
                    options=egx30_list,
                    default=[],
                    format_func=lambda x: f"{x.replace('.CA', '')} - {stock_names.get(x, '')}"
                )
                selected_stocks.extend(selected_egx30)
        with cols[1]:
            with st.expander("مؤشر EGX 70", expanded=True):
                selected_egx70 = st.multiselect(
                    "اختر أسهم EGX70:",
                    options=egx70_list,
                    default=[],
                    format_func=lambda x: f"{x.replace('.CA', '')} - {stock_names.get(x, '')}"
                )
                selected_stocks.extend(selected_egx70)
        with cols[2]:
            with st.expander("مؤشر EGX 100", expanded=True):
                selected_egx100 = st.multiselect(
                    "اختر أسهم EGX100:",
                    options=egx100_list,
                    default=[],
                    format_func=lambda x: f"{x.replace('.CA', '')} - {stock_names.get(x, '')}"
                )
                selected_stocks.extend(selected_egx100)
    elif selection_method == "فحص قائمتي المفضلة":
        selected_stocks.extend(favorites_list)
    elif selection_method == "لا أريد (سأكتفي بأسهم السيرش فقط)":
        pass
    else:
        if "EGX30" in selection_method:
            selected_stocks.extend(egx30_list)
        elif "EGX70" in selection_method:
            selected_stocks.extend(egx70_list)
        elif "البورصة بالكامل" in selection_method:
            selected_stocks.extend(egx100_list)

        st.info(f"تم تحديد {len(selected_stocks)} سهم للفحص التلقائي. (قد يستغرق الفحص دقيقة أو أكثر)")

    # منع تكرار الأسهم في حالة اختيار نفس السهم من السيرش ومن القطاع
    selected_stocks = list(dict.fromkeys(selected_stocks))

    # فلاتر العرض السريعة
    st.subheader("🔎 فلاتر العرض السريعة")
    filter_signal = st.selectbox("تصفية حسب الإشارة:", ["عرض الكل", "فرص الشراء فقط", "الأسهم السلبية فقط"])

    # 4. زرار تشغيل الفحص
    if st.button("🔄 فحص السوق وتحديث التوجيهات"):
        st.cache_data.clear() # مسح الذاكرة المؤقتة لضمان جلب بيانات حية في كل مرة يضغط فيها على فحص
        if not selected_stocks:
            st.warning("برجاء اختيار أسهم للفحص أولاً!")
        else:
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            total = len(selected_stocks)

            for i, ticker in enumerate(selected_stocks):
                arabic_name = stock_names.get(ticker, "")
                status_text.markdown(f"**⏳ جاري الفحص:** {arabic_name} ({ticker}) ... [{i+1}/{total}]")

                # سحب الداتا بناءً على الإعدادات
                sector_name = stock_sectors.get(ticker, "غير محدد")
                index_name = "EGX30" if ticker in egx30_list else ("EGX70" if ticker in egx70_list else "-")

                res = analyze_stock_cached(ticker, yf_period, yf_interval, arabic_name, sector_name, index_name)
                if res:
                    results.append(res)

                progress_bar.progress((i + 1) / total)

            status_text.success(f"✅ تم الانتهاء من فحص {len(results)} سهم بنجاح!")

        # 4. عرض النتائج في جدول منظم
        if results:
            res_df = pd.DataFrame(results)

            # تطبيق الفلاتر
            if filter_signal == "فرص الشراء فقط":
                res_df = res_df[res_df["Score"] >= 1]
            elif filter_signal == "الأسهم السلبية فقط":
                res_df = res_df[res_df["Score"] < 0]

            if not res_df.empty:
                # ترتيب الأسهم حسب قوة الإشارة ثم بالاسم عشان الترتيب ميتغيرش عشوائياً
                res_df = res_df.sort_values(by=["Score", "اسم السهم"], ascending=[False, True]).drop(columns=["Score"])
                res_df.reset_index(drop=True, inplace=True)

                st.success(f"تم تحديث البيانات بنجاح! إجمالي الأسهم المعروضة: {len(res_df)}")
                # عرض الجدول بشكل يناسب حجم الشاشة
                st.dataframe(res_df, use_container_width=True)
            else:
                st.warning("لا توجد أسهم تطابق الفلاتر اللي اخترتها. جرب تختار 'عرض الكل'.")
        else:
            st.warning("تأكد من اختيار أسهم صحيحة أو اتصالك بالإنترنت.")

with tabs[1]:
    st.subheader("⭐ الأسهم المفضلة (متابعة حية)")
    st.write("الأسهم اللي هتختارها هنا هتتحفظ في حسابك السحابي وهيتعملها تحليل فوري أول ما تفتح البرنامج.")


    new_favorites = st.multiselect(
        "إدارة قائمتي المفضلة:",
        options=list(stock_names.keys()),
        default=[x for x in favorites_list if x in stock_names.keys()],
        format_func=lambda x: f"{x.replace('.CA', '')} - {stock_names[x]}"
    )

    if new_favorites != favorites_list:
        st.session_state["user_data"]["favorites"] = new_favorites
        # Sync with Firebase
        try:
            fb.update_user_data(st.session_state["user"]["localId"], st.session_state["user"]["idToken"], st.session_state["user_data"])
        except Exception as e:
            st.error(f"خطأ في الحفظ السحابي: {str(e)}")
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
                    st.markdown(f"<div style='border:1px solid #ddd; padding:10px; border-radius:8px; text-align:center;'><b>{fav_ticker.replace('.CA', '')}</b><br>{signal} {res['السعر الحالي']}<br><span style='font-size:12px;color:#666;'>دخول: {res['الدخول المقترح']} | هدف: {res['الهدف المتوقع']}<br>وقف: {res['وقف الخسارة']}</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='border:1px solid #ddd; padding:10px; border-radius:8px; text-align:center;'><b>{fav_ticker.replace('.CA', '')}</b><br>⏳ جاري..</div>", unsafe_allow_html=True)


with tabs[2]:
    st.subheader("💼 محفظتي الذكية (Smart Portfolio Tracker)")
    st.write("أضف الأسهم التي اشتريتها لمراقبة الربح/الخسارة والقيمة الإجمالية لمحفظتك، وتحديد أهداف الخروج ووقف الخسارة ديناميكياً.")


    col_p1, col_p2, col_p3, col_p4 = st.columns([2, 1, 1, 1])
    with col_p1:
        new_p_ticker = st.selectbox("اختر السهم للإضافة:", options=[""] + list(stock_names.keys()), format_func=lambda x: f"{x.replace('.CA', '')} - {stock_names[x]}" if x else "اختر سهم...")
    with col_p2:
        new_p_price = st.number_input("متوسط السعر:", min_value=0.0, format="%.3f")
    with col_p3:
        new_p_qty = st.number_input("العدد (أسهم):", min_value=0, step=1)
    with col_p4:
        st.write("")
        st.write("")
        if st.button("➕ إضافة للمحفظة", use_container_width=True):
            if new_p_ticker and new_p_price > 0 and new_p_qty > 0:
                exists = False
                for p in portfolio_list:
                    if p["ticker"] == new_p_ticker:
                        p["buy_price"] = new_p_price
                        p["qty"] = new_p_qty
                        exists = True
                if not exists:
                    portfolio_list.append({"ticker": new_p_ticker, "buy_price": new_p_price, "qty": new_p_qty})

                st.session_state["user_data"]["portfolio"] = portfolio_list
                try:
                    fb.update_user_data(st.session_state["user"]["localId"], st.session_state["user"]["idToken"], st.session_state["user_data"])
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ: {e}")

    if portfolio_list:
        st.write("📊 **تفاصيل المحفظة:**")
        total_portfolio_cost = 0.0
        total_portfolio_value = 0.0

        for p in portfolio_list:
            ticker = p["ticker"]
            buy_price = float(p["buy_price"])
            qty = int(p.get("qty", 1))  # Fallback for old data

            arabic_name = stock_names.get(ticker, "")
            sector_name = stock_sectors.get(ticker, "غير محدد")
            index_name = "EGX30" if ticker in egx30_list else ("EGX70" if ticker in egx70_list else "-")

            res_live = analyze_stock_cached(ticker, yf_period, yf_interval, arabic_name, sector_name, index_name)
            if res_live:
                current_price = res_live['السعر الحالي']

                stock_cost = buy_price * qty
                stock_value = current_price * qty
                pnl_money = stock_value - stock_cost
                pnl_perc = ((current_price - buy_price) / buy_price) * 100

                total_portfolio_cost += stock_cost
                total_portfolio_value += stock_value

                radar_sl = res_live['وقف الخسارة']
                radar_tp = res_live['الهدف المتوقع']

                if radar_sl != "-" and radar_tp != "-":
                    sl_val = float(radar_sl)
                    tp_val = float(radar_tp)
                    if sl_val < buy_price:
                        act_sl = sl_val
                    else:
                        act_sl = buy_price * 0.95
                else:
                    act_sl = buy_price * 0.95
                    tp_val = buy_price * 1.05

                if current_price <= act_sl:
                    action = "🛑 فعل وقف الخسارة!"
                    card_color = "rgba(255, 235, 238, 0.5)"
                elif current_price >= tp_val:
                    action = "🎯 جني أرباح!"
                    card_color = "rgba(232, 245, 233, 0.5)"
                else:
                    if pnl_perc > 0:
                        action = "🛡️ احتفاظ (ربح)"
                        card_color = "rgba(240, 253, 244, 0.5)"
                    else:
                        action = "⏳ احتفاظ (انتظار)"
                        card_color = "rgba(255, 251, 235, 0.5)"

                pnl_perc_str = f"+{pnl_perc:.1f}%" if pnl_perc > 0 else f"{pnl_perc:.1f}%"
                pnl_money_str = f"+{pnl_money:.2f} EGP" if pnl_money > 0 else f"{pnl_money:.2f} EGP"
                pnl_color = "#28a745" if pnl_perc > 0 else "#dc3545"

                st.markdown(f"""
                <div style='background:{card_color}; border:1px solid #ddd; padding:15px; border-radius:10px; margin-bottom:10px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <h4 style='margin:0;color:#1e3c72;'>{ticker.replace('.CA', '')} {arabic_name}</h4>
                            <span style='font-size:14px;color:#555;'>متوسط السعر: {buy_price} | الكمية: {qty} سهم | الإجمالي: {stock_cost:,.0f} ج</span><br>
                            <span style='font-size:14px;color:#111;'>السعر الحالي: <b>{current_price}</b> | القيمة الحالية: {stock_value:,.0f} ج</span>
                        </div>
                        <div style='text-align:right;'>
                            <h3 style='margin:0;color:{pnl_color};'>{pnl_money_str}</h3>
                            <h4 style='margin:0;color:{pnl_color};'>{pnl_perc_str}</h4>
                            <span style='font-size:14px;font-weight:bold;'>{action}</span>
                        </div>
                    </div>
                    <hr style='margin:8px 0;'/>
                    <div style='font-size:13px; color:#666; display:flex; justify-content:space-between;'>
                        <span>🎯 الهدف المقترح: {tp_val:.2f}</span>
                        <span>🛑 وقف الخسارة: {act_sl:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"❌ حذف من المحفظة", key=f"del_{ticker}"):
                    st.session_state["user_data"]["portfolio"] = [x for x in portfolio_list if x["ticker"] != ticker]
                    try:
                        fb.update_user_data(st.session_state["user"]["localId"], st.session_state["user"]["idToken"], st.session_state["user_data"])
                        st.rerun()
                    except Exception as e:
                        st.error(f"خطأ: {e}")

        if total_portfolio_cost > 0:
            tot_pnl = total_portfolio_value - total_portfolio_cost
            tot_perc = (tot_pnl / total_portfolio_cost) * 100
            t_color = "#28a745" if tot_pnl > 0 else "#dc3545"
            st.markdown(f"""
            <div style='background:#f8f9fa; border:2px solid #ccc; padding:15px; border-radius:10px; text-align:center;'>
                <h3 style='margin:0;'>إجمالي المحفظة: <span style='color:#0056b3;'>{total_portfolio_value:,.0f} ج.م</span></h3>
                <h4 style='color:{t_color}; margin:5px 0 0 0;'>الأرباح/الخسائر: {tot_pnl:,.0f} ج.م ({tot_perc:,.1f}%)</h4>
            </div>
            """, unsafe_allow_html=True)

