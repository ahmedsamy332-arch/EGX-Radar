import streamlit as st

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

egx30_list = ["COMI.CA", "FWRY.CA", "EFIH.CA", "EGAL.CA", "ABUK.CA", "TMGH.CA", "HRHO.CA", "SWDY.CA", "ETEL.CA", "ESRS.CA", "AMOC.CA", "SKPC.CA", "HELI.CA", "PHDC.CA", "MFPC.CA", "MASR.CA", "ORAS.CA", "ORWE.CA", "ISPH.CA", "CIEB.CA", "ADIB.CA", "AUTO.CA", "CLHO.CA", "JUFO.CA", "SUGR.CA", "BTFH.CA", "DOMT.CA", "OIH.CA", "MTIE.CA", "CCAP.CA", "EMFD.CA", "RMDA.CA", "QNBA.CA", "HDBK.CA", "SAUD.CA"]
egx70_list = [t for t in stock_names.keys() if t not in egx30_list]
egx100_list = egx30_list + egx70_list

favorites_list = st.session_state['user_data'].get('favorites', [])
portfolio_list = st.session_state['user_data'].get('portfolio', [])
st.markdown('---')

is_admin = st.session_state['user'].get('email', '').strip().lower() == "ahmedsamy332@gmail.com"

favorites_list = st.session_state['user_data'].get('favorites', []) if 'user_data' in st.session_state else []
portfolio_list = st.session_state['user_data'].get('portfolio', []) if 'user_data' in st.session_state else []
is_admin = st.session_state['user'].get('email', '').strip().lower() == 'ahmedsamy332@gmail.com' if 'user' in st.session_state and st.session_state['user'] else False
