import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace UI filter section
old_ui = """        st.subheader("🔎 4. فلاتر العرض السريعة")
        filter_signal = st.selectbox("تصفية حسب الإشارة:", ["عرض الكل", "فرص الشراء فقط", "الأسهم السلبية فقط"], index=None)

        if filter_signal:"""

new_ui = """        st.subheader("🔎 4. فلاتر العرض السريعة")
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            filter_signal = st.selectbox("تصفية حسب الإشارة:", ["عرض الكل", "فرص الشراء فقط", "الأسهم السلبية فقط"], index=0)
        with filter_col2:
            all_sectors = ["عرض الكل"] + sorted(list(set([s for s in stock_sectors.values() if s != "غير محدد"])))
            filter_sector = st.selectbox("تصفية حسب القطاع:", all_sectors, index=0)
        with filter_col3:
            filter_liquidity = st.selectbox("تصفية حسب السيولة:", ["عرض الكل", "T+0 فقط (أعلى سيولة)", "استبعاد السيولة الضعيفة", "سيولة انفجارية 🔥"], index=0)

        if True:"""

content = content.replace(old_ui, new_ui)

# Add logic implementation
old_logic = """                    if filter_signal == "فرص الشراء فقط":
                        res_df = res_df[res_df["Score"] >= 1]
                    elif filter_signal == "الأسهم السلبية فقط":
                        res_df = res_df[res_df["Score"] < 0]"""

new_logic = """                    if filter_signal == "فرص الشراء فقط":
                        res_df = res_df[res_df["Score"] >= 1]
                    elif filter_signal == "الأسهم السلبية فقط":
                        res_df = res_df[res_df["Score"] < 0]
                        
                    if filter_sector != "عرض الكل":
                        res_df = res_df[res_df["القطاع"] == filter_sector]
                        
                    if filter_liquidity == "T+0 فقط (أعلى سيولة)":
                        res_df = res_df[res_df["نظام التسوية"].str.contains("T\\+0")]
                    elif filter_liquidity == "استبعاد السيولة الضعيفة":
                        res_df = res_df[~res_df["نظام التسوية"].str.contains("T\\+2")]
                    elif filter_liquidity == "سيولة انفجارية 🔥":
                        res_df = res_df[res_df["السيولة"].str.contains("انفجار|عالية")]"""

content = content.replace(old_logic, new_logic)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
