import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
from tvDatafeed import TvDatafeed, Interval

import firebase_client as fb

from analyzer import analyze_stock_cached, get_daily_performance
from data_assets import *


# 1. إعدادات الصفحة لتناسب الموبايل
st.set_page_config(page_title="نسر البورصة المصرية", layout="centered")

# CSS مخصص لتحسين الخطوط والأنيميشن
st.markdown("""
<style>
/* إخفاء زر النشر في الشريط العلوي فقط */
.stAppDeployButton, [data-testid="stAppDeployButton"] {
    display: none !important;
}
footer {visibility: hidden;}
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Cairo', sans-serif !important;
}
/* تكبير الخط العام بدون استخدام !important اللي بتبوظ التصميمات المخصصة */
p, label, span, li {
    font-size: 18px;
}
/* كلاس مخصص لاسم البرنامج عشان نكبره براحتنا */
.main-eagle-title {
    font-size: 48px !important;
    font-weight: 900 !important;
    color: #1e3c72 !important;
    line-height: 1.2 !important;
}

/* قلب اتجاه المحتوى من اليمين لليسار باستخدام الكلاسات الأساسية لستريمليت */
.block-container {
    direction: rtl;
    text-align: right;
}

[data-testid="stSidebar"] {
    direction: rtl;
}

/* محاذاة كل النصوص لليمين */
p, div, span, h1, h2, h3, h4, h5, h6, label, .stMarkdown, .stText {
    text-align: right !important;
}

/* تكبير حجم الخطوط للعناصر النصية فقط بدون التأثير على التصميمات المخصصة */
.stMarkdown p, .stText {
    font-size: 18px;
}

h1 { font-size: 32px !important; }
h2 { font-size: 28px !important; }
h3 { font-size: 24px !important; }

/* قلب اتجاه القائمة الجانبية */
section[data-testid="stSidebar"] {
    direction: rtl;
    text-align: right;
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

# عنوان الموقع والإمضاء بتصميم متناسق مع حجم الخطوط
st.markdown("""
<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: -30px; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #e6e6e6; width: 100%;">
    <div class="main-eagle-title" style="margin: 0; padding: 0; text-align: center;">🦅 نسر البورصة</div>
    <div style="font-size: 16px !important; color: #666; font-weight: bold; font-family: sans-serif; margin-top: 10px; text-align: center;">
        <span style="font-weight: normal; color: #888;">By</span> <span style="color: #0056b3;">AHMED SAMY</span>
    </div>
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
    except Exception:
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

# تحديث آخر ظهور لو مر أكتر من 5 دقائق (300 ثانية)
import time
current_time = int(time.time() * 1000)
last_active = st.session_state["user_data"].get("last_active", 0)
if current_time - last_active > 300000:
    st.session_state["user_data"]["last_active"] = current_time
    try:
        fb.update_user_data(st.session_state["user"]["localId"], st.session_state["user"]["idToken"], st.session_state["user_data"])
    except Exception:
        pass
# القائمة الجانبية
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
st.subheader("⚙️ 1. إعدادات التحليل والمدى الزمني")
timeframe = st.radio(
    "اختر المدى الزمني للرادار:",
    ["مضاربة لحظية (15 دقيقة) - لتداول نفس الجلسة", 
     "مضاربة قصيرة (ساعة) - لسوينجات أيام", 
     "تداول يومي (شمعة يومية) - للاتجاه العام والمستثمر"],
    index=None
)
if not timeframe:
    st.info("👈 يرجى اختيار المدى الزمني لفتح البرنامج.")
    st.stop()


if "15 دقيقة" in timeframe:
    yf_period = "60d"
    yf_interval = "15m"
elif "ساعة" in timeframe:
    yf_period = "730d"
    yf_interval = "1h"
else:
    yf_period = "2y"
    yf_interval = "1d"

favorites_list = st.session_state.get('user_data', {}).get('favorites', [])
portfolio_list = st.session_state.get('user_data', {}).get('portfolio', [])
user_obj = st.session_state.get('user')
is_admin = user_obj.get('email', '').strip().lower() == "ahmedsamy332@gmail.com" if user_obj else False

tab_names = ['📊 رادار السوق', '🔥 الفرص الذهبية', '📉 قنص القيعان', '📈 حصاد الجلسة', '⭐ المفضلة', '💼 محفظتي الذكية']
if is_admin:
    tab_names.append('👑 لوحة الإدارة')

tabs = st.tabs(tab_names)

with tabs[0]:

    def format_stock_option(ticker):
        name = stock_names.get(ticker, "")
        idx = "EGX30" if ticker in egx30_list else ("EGX70" if ticker in egx70_list else "EGX100")
        return f"{ticker.replace('.CA', '')} - {name} ({idx})"

    st.subheader("📋 2. طريقة اختيار الأسهم للمراقبة")
    selection_method = st.radio(
        "هل ترغب في فحص مجموعات أو مؤشرات؟",
        ["لا أريد (سأكتفي بأسهم السيرش فقط)", "فحص قائمتي المفضلة", "فحص مؤشر EGX30 بالكامل", "فحص مؤشر EGX70 بالكامل", "فحص البورصة بالكامل (كل الأسهم)"],
        horizontal=True,
        index=None
    )

    if selection_method:
        st.subheader("📋 3. إضافة أسهم مخصصة للبحث (اختياري)")
        specific_search_stocks = st.multiselect(
            "ابحث باسم السهم (عربي) أو الكود (إنجليزي):",
            options=list(stock_names.keys()),
            default=[],
            format_func=format_stock_option
        )

        st.subheader("🔎 4. فلاتر العرض السريعة")
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            filter_signal = st.selectbox("تصفية حسب الإشارة:", ["عرض الكل", "فرص الشراء فقط", "الأسهم السلبية فقط"], index=0)
        with filter_col2:
            all_sectors = ["عرض الكل"] + sorted(list(set([s for s in stock_sectors.values() if s != "غير محدد"])))
            filter_sector = st.selectbox("تصفية حسب القطاع:", all_sectors, index=0)
        with filter_col3:
            filter_liquidity = st.selectbox("تصفية حسب السيولة:", ["عرض الكل", "T+0 فقط (أعلى سيولة)", "استبعاد السيولة الضعيفة", "سيولة انفجارية 🔥"], index=0)

        if True:
            selected_stocks = list(specific_search_stocks)

            if selection_method == "فحص قائمتي المفضلة":
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

            selected_stocks = list(dict.fromkeys(selected_stocks))

            if st.button("🔄 فحص السوق وتحديث التوجيهات"):
                st.cache_data.clear()
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

                        sector_name = stock_sectors.get(ticker, "غير محدد")
                        index_name = "EGX30" if ticker in egx30_list else ("EGX70" if ticker in egx70_list else "-")

                        res = analyze_stock_cached(ticker, yf_period, yf_interval, arabic_name, sector_name, index_name)
                        if res:
                            results.append(res)

                        progress_bar.progress((i + 1) / total)

                    status_text.success(f"✅ تم الانتهاء من فحص {len(results)} سهم بنجاح!")

                if results:
                    res_df = pd.DataFrame(results)

                    if filter_signal == "فرص الشراء فقط":
                        res_df = res_df[res_df["Score"] >= 1]
                    elif filter_signal == "الأسهم السلبية فقط":
                        res_df = res_df[res_df["Score"] < 0]
                        
                    if filter_sector != "عرض الكل":
                        res_df = res_df[res_df["القطاع"] == filter_sector]
                        
                    if filter_liquidity == "T+0 فقط (أعلى سيولة)":
                        res_df = res_df[res_df["نظام التسوية"].str.contains(r"T\+0")]
                    elif filter_liquidity == "استبعاد السيولة الضعيفة":
                        res_df = res_df[~res_df["نظام التسوية"].str.contains(r"T\+2")]
                    elif filter_liquidity == "سيولة انفجارية 🔥":
                        res_df = res_df[res_df["السيولة"].str.contains("انفجار|عالية")]

                    if not res_df.empty:
                        res_df = res_df.sort_values(by=["Score", "اسم السهم"], ascending=[False, True]).drop(columns=["Score"])
                        res_df.reset_index(drop=True, inplace=True)
                        st.success(f"تم تحديث البيانات بنجاح! إجمالي الأسهم المعروضة: {len(res_df)}")
                        st.dataframe(res_df, use_container_width=True)
                    else:
                        st.warning("لا توجد أسهم تطابق الفلاتر اللي اخترتها. جرب تختار 'عرض الكل'.")
                else:
                    st.warning("تأكد من اختيار أسهم صحيحة أو اتصالك بالإنترنت.")


with tabs[1]:
    st.subheader("🔥 الفرص الذهبية (اقتراحات الذكاء الاصطناعي)")
    st.write("البرنامج هيفحص أسهم EGX30 على المدى (اليومي + اللحظي) وهيرشحلك الأسهم اللي فيها إشارة شراء قوية واتجاه صاعد متطابق.")
    
    if st.button("🔍 ابدأ فحص الفرص الذهبية (يستغرق دقيقتين)", use_container_width=True):
        st.cache_data.clear()
        golden_results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total = len(egx30_list)
        for i, ticker in enumerate(egx30_list):
            arabic_name = stock_names.get(ticker, "")
            status_text.markdown(f"**⏳ جاري فحص وتحليل:** {arabic_name} ({ticker}) ... [{i+1}/{total}]")
            sector_name = stock_sectors.get(ticker, "غير محدد")
            
            # تحليل يومي
            res_1d = analyze_stock_cached(ticker, "2y", "1d", arabic_name, sector_name, "EGX30")
            # تحليل ساعة
            res_1h = analyze_stock_cached(ticker, "60d", "1h", arabic_name, sector_name, "EGX30")
            
            if res_1d and res_1h:
                score_1d = res_1d.get("Score", 0)
                score_1h = res_1h.get("Score", 0)
                
                # فرصة ذهبية لو اليومي والساعة إيجابيين (تجميع أو شراء قوي)
                if score_1d >= 1 and score_1h >= 1:
                    is_super = score_1d >= 4 and score_1h >= 4
                    golden_results.append({
                        "اسم السهم": res_1d["اسم السهم"],
                        "السعر": res_1d["السعر الحالي"],
                        "الدخول": res_1d["الدخول المقترح"],
                        "الهدف": res_1d["الهدف المتوقع"],
                        "وقف الخسارة": res_1d["وقف الخسارة"],
                        "توافق الاتجاه": "🟢 متطابق جداً (سوبر)" if is_super else "🟡 متطابق (تجميع)",
                        "السيولة": res_1d["السيولة"],
                        "المؤشر اليومي": res_1d["التوجيه الحالي"],
                        "المؤشر اللحظي": res_1h["التوجيه الحالي"],
                        "Score_1d": score_1d,
                        "Score_1h": score_1h
                    })
                    
            progress_bar.progress((i + 1) / total)
            
        status_text.success(f"✅ تم الانتهاء من الفحص، لقينا {len(golden_results)} فرصة دهبية!")
        
        if golden_results:
            # ترتيب الفرص بناء على قوة الإشارات
            golden_df = pd.DataFrame(golden_results)
            golden_df["Total_Score"] = golden_df["Score_1d"] + golden_df["Score_1h"]
            golden_df = golden_df.sort_values(by="Total_Score", ascending=False).drop(columns=["Score_1d", "Score_1h", "Total_Score"])
            golden_df.reset_index(drop=True, inplace=True)
            
            # عرض أفضل سهم ككارت تعريفي
            top_stock = golden_df.iloc[0]
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #FFD700 0%, #FDB931 100%); padding: 20px; border-radius: 15px; margin-bottom: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h2 style='margin:0; color: #fff; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);'>🏆 سهم اليوم (الأعلى تقييماً)</h2>
                <h1 style='margin:10px 0; color: #1e3c72;'>{top_stock['اسم السهم']}</h1>
                <h3 style='margin:0; color: #fff;'>السعر الحالي: {top_stock['السعر']} ج.م | التوجيه: {top_stock['المؤشر اليومي']}</h3>
                <p style='font-size:18px; margin-top:10px; color:#333; font-weight:bold;'>الدخول: {top_stock['الدخول']} | الهدف: {top_stock['الهدف']} | الوقف: {top_stock['وقف الخسارة']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader("📋 باقي الفرص المتاحة:")
            st.dataframe(golden_df, use_container_width=True)
        else:
            st.warning("للأسف مفيش أسهم مطابقة للشروط القوية حالياً. السوق قد يكون سلبي أو في مرحلة هبوط.")


with tabs[2]:
    st.subheader("📉 قنص القيعان (Oversold Scanner)")
    st.write("البرنامج هيفحص أسهم السوق بالكامل (EGX30 و EGX70) وهيرشحلك الأسهم اللي نزلت لأقصى قاع لها (التشبع البيعي) وفي احتمالية كويسة لارتدادها.")
    
    if st.button("🔎 ابدأ فحص قنص القيعان", use_container_width=True):
        st.cache_data.clear()
        oversold_results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        combined_list = list(set(egx30_list + egx70_list))
        total = len(combined_list)
        
        for i, ticker in enumerate(combined_list):
            arabic_name = stock_names.get(ticker, "")
            status_text.markdown(f"**⏳ جاري الفحص:** {arabic_name} ({ticker}) ... [{i+1}/{total}]")
            sector_name = stock_sectors.get(ticker, "غير محدد")
            index_name = "EGX30" if ticker in egx30_list else ("EGX70" if ticker in egx70_list else "-")
            
            # تحليل يومي لضمان الدقة (استخدام سنتين لضمان حساب البولينجر والـ RSI بدقة)
            res = analyze_stock_cached(ticker, "2y", "1d", arabic_name, sector_name, index_name)
            
            if res:
                rsi_val = res.get("الزخم (RSI)", 50)
                
                # شرط التشبع البيعي: RSI أقل من أو يساوي 35
                if rsi_val <= 35:
                    oversold_results.append({
                        "اسم السهم": res["اسم السهم"],
                        "السعر": res["السعر الحالي"],
                        "الزخم (RSI)": rsi_val,
                        "الدخول المقترح": res["الدخول المقترح"],
                        "الهدف الأول": res["الهدف المتوقع"],
                        "وقف الخسارة": res["وقف الخسارة"],
                        "السيولة": res["السيولة"],
                        "التوجيه": res["التوجيه الحالي"]
                    })
                    
            progress_bar.progress((i + 1) / total)
            
        status_text.success(f"✅ تم الانتهاء من الفحص، لقينا {len(oversold_results)} سهم في مرحلة قاع!")
        
        if oversold_results:
            import pandas as pd
            # ترتيب الفرص بناء على الـ RSI من الأقل للأكبر (الأقل يعني فرصة ارتداد أقوى)
            oversold_df = pd.DataFrame(oversold_results)
            oversold_df = oversold_df.sort_values(by="الزخم (RSI)", ascending=True)
            oversold_df.reset_index(drop=True, inplace=True)
            
            # عرض أفضل سهم ارتدادي (أقل RSI)
            top_stock = oversold_df.iloc[0]
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 15px; margin-bottom: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h2 style='margin:0; color: #fff; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);'>🎯 سهم القاع (فرصة قنص)</h2>
                <h1 style='margin:10px 0; color: #4facfe;'>{top_stock['اسم السهم']}</h1>
                <h3 style='margin:0; color: #fff;'>السعر الحالي: {top_stock['السعر']} ج.م | نسبة التشبع: RSI {top_stock['الزخم (RSI)']}</h3>
                <p style='font-size:18px; margin-top:10px; color:#ddd; font-weight:bold;'>الدخول: {top_stock['الدخول المقترح']} | الهدف: {top_stock['الهدف الأول']} | الوقف: {top_stock['وقف الخسارة']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader("📋 باقي الأسهم في مرحلة القاع:")
            st.dataframe(oversold_df, use_container_width=True)
        else:
            st.warning("لا يوجد أسهم في حالة تشبع بيعي حالياً (السوق في حالة إيجابية غالباً).")


with tabs[3]:
    st.subheader("📈 حصاد الجلسة (الأكثر صعوداً وهبوطاً)")
    st.write("البرنامج هيفحص أداء أسهم EGX100 لليوم الحالي ويطلعلك الأسهم الأكثر ربحاً والأكثر خسارة بنهاية الجلسة.")
    
    if st.button("📊 ابدأ فحص حصاد الجلسة (فحص سريع)", use_container_width=True):
        st.cache_data.clear()
        daily_results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total = len(egx100_list)
        
        for i, ticker in enumerate(egx100_list):
            arabic_name = stock_names.get(ticker, "")
            status_text.markdown(f"**⏳ جاري الفحص:** {arabic_name} ({ticker}) ... [{i+1}/{total}]")
            
            res = get_daily_performance(ticker, arabic_name)
            if res:
                daily_results.append(res)
                
            progress_bar.progress((i + 1) / total)
            
        status_text.success(f"✅ تم الانتهاء من الفحص!")
        
        if daily_results:
            import pandas as pd
            df_harvest = pd.DataFrame(daily_results)
            df_harvest = df_harvest.sort_values(by="التغير (%)", ascending=False)
            df_harvest.reset_index(drop=True, inplace=True)
            
            top_gainers = df_harvest.head(15).copy()
            top_losers = df_harvest.tail(15).copy()
            top_losers = top_losers.sort_values(by="التغير (%)", ascending=True)
            top_losers.reset_index(drop=True, inplace=True)
            
            col_gain, col_lose = st.columns(2)
            
            with col_gain:
                st.markdown("<h3 style='text-align: center; color: #28a745;'>🟢 الأكثر صعوداً (Top Gainers)</h3>", unsafe_allow_html=True)
                st.dataframe(top_gainers.style.map(lambda x: 'color: #28a745; font-weight: bold;', subset=['التغير (%)']), use_container_width=True)
                
            with col_lose:
                st.markdown("<h3 style='text-align: center; color: #dc3545;'>🔴 الأكثر هبوطاً (Top Losers)</h3>", unsafe_allow_html=True)
                st.dataframe(top_losers.style.map(lambda x: 'color: #dc3545; font-weight: bold;', subset=['التغير (%)']), use_container_width=True)
        else:
            st.warning("عفواً، لا توجد بيانات متاحة حالياً.")

with tabs[4]:
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


with tabs[5]:
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


if is_admin:
    with tabs[6]:
        st.subheader("👑 لوحة تحكم الإدارة")
        st.write("هذه اللوحة تظهر لك فقط بصفتك مدير النظام.")
        
        users_list = fb.get_all_users()
        if not users_list:
            st.warning("لم يتم العثور على مستخدمين أو ملف الصلاحيات غير متوفر.")
        else:
            st.info(f"إجمالي عدد المستخدمين المسجلين: **{len(users_list)}**")
            
            for u in users_list:
                status = "🔴 موقوف" if u["disabled"] else "🟢 نشط"
                
                # Format timestamps safely (Egypt time: UTC+3)
                def format_eg_time(ts_ms):
                    if not ts_ms: return "غير متوفر"
                    import datetime
                    dt_utc = datetime.datetime.fromtimestamp(ts_ms / 1000.0, tz=datetime.timezone.utc)
                    dt_eg = dt_utc + datetime.timedelta(hours=3)
                    ampm = "م" if dt_eg.hour >= 12 else "ص"
                    hr = dt_eg.hour % 12
                    hr = 12 if hr == 0 else hr
                    return dt_eg.strftime(f'%Y-%m-%d {hr:02d}:%M ') + ampm

                created = format_eg_time(u.get("creationTime"))
                last_sign_in = format_eg_time(u.get("lastSignInTime"))
                
                with st.expander(f"{status} | {u['email']}"):
                    st.write(f"**تاريخ التسجيل:** {created}")
                    st.write(f"**آخر دخول:** {last_sign_in}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if u["disabled"]:
                            if st.button("✅ تفعيل الحساب", key=f"en_{u['uid']}"):
                                if fb.disable_user(u["uid"], False):
                                    st.success("تم التفعيل!")
                                    st.rerun()
                        else:
                            if st.button("🚫 إيقاف الحساب", key=f"dis_{u['uid']}"):
                                if fb.disable_user(u["uid"], True):
                                    st.warning("تم إيقاف الحساب!")
                                    st.rerun()
                    with c2:
                        if st.button("🗑️ حذف الحساب نهائياً", key=f"del_{u['uid']}"):
                            if fb.delete_user(u["uid"]):
                                st.error("تم الحذف بنجاح!")
                                st.rerun()


