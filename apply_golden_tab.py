import re

with open("app.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update tab names
code = code.replace(
    "tab_names = ['📊 رادار السوق', '⭐ المفضلة', '💼 محفظتي الذكية']",
    "tab_names = ['📊 رادار السوق', '🔥 الفرص الذهبية', '⭐ المفضلة', '💼 محفظتي الذكية']"
)

# 2. Shift tabs indices
# We have `with tabs[1]:`, `with tabs[2]:`, `with tabs[3]:`
code = code.replace("with tabs[3]:", "with tabs[4]:")
code = code.replace("with tabs[2]:", "with tabs[3]:")
code = code.replace("with tabs[1]:", "with tabs[2]:")

golden_tab_code = """
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
            res_1h = analyze_stock_cached(ticker, "730d", "1h", arabic_name, sector_name, "EGX30")
            
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
            st.markdown(f\"\"\"
            <div style='background: linear-gradient(135deg, #FFD700 0%, #FDB931 100%); padding: 20px; border-radius: 15px; margin-bottom: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h2 style='margin:0; color: #fff; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);'>🏆 سهم اليوم (الأعلى تقييماً)</h2>
                <h1 style='margin:10px 0; color: #1e3c72;'>{top_stock['اسم السهم']}</h1>
                <h3 style='margin:0; color: #fff;'>السعر الحالي: {top_stock['السعر']} ج.م | التوجيه: {top_stock['المؤشر اليومي']}</h3>
                <p style='font-size:18px; margin-top:10px; color:#333; font-weight:bold;'>الدخول: {top_stock['الدخول']} | الهدف: {top_stock['الهدف']} | الوقف: {top_stock['وقف الخسارة']}</p>
            </div>
            \"\"\", unsafe_allow_html=True)
            
            st.subheader("📋 باقي الفرص المتاحة:")
            st.dataframe(golden_df, use_container_width=True)
        else:
            st.warning("للأسف مفيش أسهم مطابقة للشروط القوية حالياً. السوق قد يكون سلبي أو في مرحلة هبوط.")

"""

# Insert golden_tab_code right before `with tabs[2]:`
code = code.replace("with tabs[2]:", golden_tab_code + "with tabs[2]:")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(code)
print("Golden tab applied!")
