import re

with open("app.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update timeframe to have index=None and use a warning if not selected
timeframe_original = """st.subheader("⚙️ إعدادات التحليل (تُطبق على المفضلة والفحص)")
timeframe = st.radio(
    "اختر المدى الزمني للرادار:",
    ["مضاربة لحظية (15 دقيقة) - لتداول نفس الجلسة", 
     "مضاربة قصيرة (ساعة) - لسوينجات أيام", 
     "تداول يومي (شمعة يومية) - للاتجاه العام والمستثمر"],
    index=2
)"""
timeframe_new = """st.subheader("⚙️ 1. إعدادات التحليل والمدى الزمني")
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
"""
code = code.replace(timeframe_original, timeframe_new)

# 2. Extract tabs[0] block and rewrite it
# We know tabs[0] starts with `with tabs[0]:` and ends before `with tabs[1]:`
tabs_parts = code.split("with tabs[1]:")
before_tabs1 = tabs_parts[0]
after_tabs1 = "with tabs[1]:" + tabs_parts[1]

tab0_parts = before_tabs1.split("with tabs[0]:")
before_tab0 = tab0_parts[0]
tab0_content = tab0_parts[1]

# Rebuild tab0_content progressively
new_tab0 = """
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
        filter_signal = st.selectbox("تصفية حسب الإشارة:", ["عرض الكل", "فرص الشراء فقط", "الأسهم السلبية فقط"], index=None)

        if filter_signal:
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

                    if not res_df.empty:
                        res_df = res_df.sort_values(by=["Score", "اسم السهم"], ascending=[False, True]).drop(columns=["Score"])
                        res_df.reset_index(drop=True, inplace=True)
                        st.success(f"تم تحديث البيانات بنجاح! إجمالي الأسهم المعروضة: {len(res_df)}")
                        st.dataframe(res_df, use_container_width=True)
                    else:
                        st.warning("لا توجد أسهم تطابق الفلاتر اللي اخترتها. جرب تختار 'عرض الكل'.")
                else:
                    st.warning("تأكد من اختيار أسهم صحيحة أو اتصالك بالإنترنت.")

"""

new_code = before_tab0 + "with tabs[0]:\n" + new_tab0 + after_tabs1

with open("app.py", "w", encoding="utf-8") as f:
    f.write(new_code)
print("Patch applied!")
