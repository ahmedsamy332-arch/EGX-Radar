import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace tab names to insert the new tab at index 3
content = content.replace(
    "tab_names = ['📊 رادار السوق', '🔥 الفرص الذهبية', '📉 قنص القيعان', '⭐ المفضلة', '💼 محفظتي الذكية']",
    "tab_names = ['📊 رادار السوق', '🔥 الفرص الذهبية', '📉 قنص القيعان', '📈 حصاد الجلسة', '⭐ المفضلة', '💼 محفظتي الذكية']"
)

# Fix indices from back to front
content = content.replace("with tabs[4]:", "with tabs[5]:")
content = content.replace("with tabs[3]:", "with tabs[4]:")

# The code to inject for the new tab
new_tab_code = """
with tabs[3]:
    st.subheader("📈 حصاد الجلسة (الأكثر صعوداً وهبوطاً)")
    st.write("البرنامج هيفحص أداء أسهم EGX100 لليوم الحالي ويطلعلك الأسهم الأكثر ربحاً والأكثر خسارة بنهاية الجلسة.")
    
    if st.button("📊 ابدأ فحص حصاد الجلسة (فحص سريع)", use_container_width=True):
        st.cache_data.clear()
        daily_results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total = len(egx100_list)
        from analyzer import get_daily_performance
        
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
                st.dataframe(top_gainers.style.applymap(lambda x: 'color: #28a745; font-weight: bold;', subset=['التغير (%)']), use_container_width=True)
                
            with col_lose:
                st.markdown("<h3 style='text-align: center; color: #dc3545;'>🔴 الأكثر هبوطاً (Top Losers)</h3>", unsafe_allow_html=True)
                st.dataframe(top_losers.style.applymap(lambda x: 'color: #dc3545; font-weight: bold;', subset=['التغير (%)']), use_container_width=True)
        else:
            st.warning("عفواً، لا توجد بيانات متاحة حالياً.")

with tabs[4]:"""

parts = content.split("with tabs[4]:", 1)
content = parts[0] + new_tab_code + parts[1]

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
