import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace tab names to insert the new tab at index 2
content = content.replace(
    "tab_names = ['📊 رادار السوق', '🔥 الفرص الذهبية', '⭐ المفضلة', '💼 محفظتي الذكية']",
    "tab_names = ['📊 رادار السوق', '🔥 الفرص الذهبية', '📉 قنص القيعان', '⭐ المفضلة', '💼 محفظتي الذكية']"
)

# Fix indices from back to front to avoid replacing twice
content = content.replace("with tabs[3]:", "with tabs[4]:")
content = content.replace("with tabs[2]:", "with tabs[3]:")

# The code to inject for the new tab
new_tab_code = """
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
            st.markdown(f\"\"\"
            <div style='background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 15px; margin-bottom: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h2 style='margin:0; color: #fff; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);'>🎯 سهم القاع (فرصة قنص)</h2>
                <h1 style='margin:10px 0; color: #4facfe;'>{top_stock['اسم السهم']}</h1>
                <h3 style='margin:0; color: #fff;'>السعر الحالي: {top_stock['السعر']} ج.م | نسبة التشبع: RSI {top_stock['الزخم (RSI)']}</h3>
                <p style='font-size:18px; margin-top:10px; color:#ddd; font-weight:bold;'>الدخول: {top_stock['الدخول المقترح']} | الهدف: {top_stock['الهدف الأول']} | الوقف: {top_stock['وقف الخسارة']}</p>
            </div>
            \"\"\", unsafe_allow_html=True)
            
            st.subheader("📋 باقي الأسهم في مرحلة القاع:")
            st.dataframe(oversold_df, use_container_width=True)
        else:
            st.warning("لا يوجد أسهم في حالة تشبع بيعي حالياً (السوق في حالة إيجابية غالباً).")

with tabs[3]:"""

parts = content.split("with tabs[3]:", 1)
content = parts[0] + new_tab_code + parts[1]

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
