import streamlit as st

egx_stocks = {
    "🏦 البنوك": {
        "COMI.CA": "البنك التجاري الدولي",
        "CIEB.CA": "كريدي أجريكول",
        "ADIB.CA": "مصرف أبو ظبي الإسلامي",
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
        "SWDY.CA": "السويدي إيليكتريك",
        "ORAS.CA": "أوراسكوم كونستراكشون"
    },
    "🛢️ الموارد الأساسية والبتروكيماويات": {
        "ABUK.CA": "أبو قير للأسمدة",
        "MFPC.CA": "موبكو",
        "SKPC.CA": "سيدي كرير",
        "AMOC.CA": "أموك",
        "EGAL.CA": "مصر للألومنيوم",
        "ESRS.CA": "حديد عز"
    },
    "💻 الاتصالات وتكنولوجيا المعلومات": {
        "FWRY.CA": "فوري",
        "EFIH.CA": "إي فاينانس",
        "ETEL.CA": "المصرية للاتصالات",
        "OIH.CA": "أوراسكوم للاستثمار"
    },
    "📈 الخدمات المالية والاستثمار": {
        "HRHO.CA": "إي إف جي القابضة",
        "BTFH.CA": "بلتون المالية",
        "CCAP.CA": "القلعة للاستثمارات"
    },
    "💊 الرعاية الصحية والأدوية": {
        "ISPH.CA": "ابن سينا فارما",
        "CLHO.CA": "كليوباترا مستشفى",
        "RMDA.CA": "راميدا"
    },
    "🛒 الأغذية والسلع الاستهلاكية": {
        "JUFO.CA": "جهينة",
        "SUGR.CA": "الدلتا للسكر",
        "DOMT.CA": "دومتي",
        "ORWE.CA": "النساجون الشرقيون",
        "AUTO.CA": "جي بي كوربوريشن",
        "MTIE.CA": "إم إم جروب"
    }
}

stock_names = {}
stock_sectors = {}

for sector, stocks in egx_stocks.items():
    clean_sector_name = sector.split(' ', 1)[1] if ' ' in sector else sector
    stock_names.update(stocks)
    for ticker in stocks.keys():
        stock_sectors[ticker] = clean_sector_name

egx30_list = list(stock_names.keys())
egx70_list = []
egx100_list = list(egx30_list)
