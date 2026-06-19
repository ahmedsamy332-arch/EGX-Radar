import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Imports
content = content.replace("from streamlit_local_storage import LocalStorage", "import firebase_client as fb")

# 2. Add Login Logic at the beginning (after css/title)
login_logic = """
# Session State Variables
if "user" not in st.session_state:
    st.session_state["user"] = None
if "user_data" not in st.session_state:
    st.session_state["user_data"] = {"favorites": [], "portfolio": []}

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
                                st.success("تم إنشاء الحساب بنجاح! جاري الدخول...")
                                st.rerun()
                            except Exception as e:
                                st.error(f"خطأ في الإنشاء: {str(e)}")
                else:
                    st.warning("أدخل الإيميل والباسورد")
    
    st.stop() # إيقاف عرض باقي الصفحة حتى الدخول

# زر تسجيل الخروج
with st.sidebar:
    st.write(f"👤 {st.session_state['user']['email']}")
    if st.button("تسجيل الخروج"):
        st.session_state["user"] = None
        st.session_state["user_data"] = {"favorites": [], "portfolio": []}
        st.rerun()

"""

# Insert login logic after rights banner
content = content.replace('</div>\\n""", unsafe_allow_html=True)', '</div>\\n""", unsafe_allow_html=True)\\n\\n' + login_logic)

# 3. Replace LocalStorage with Firebase for favorites
old_favorites = '''localS = LocalStorage()
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
    favorites_list = new_favorites'''

new_favorites = '''favorites_list = st.session_state["user_data"].get("favorites", [])

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
    favorites_list = new_favorites'''

content = content.replace(old_favorites, new_favorites)

# 4. Smart Portfolio Tracker Logic
portfolio_logic = """
st.markdown("---")
st.subheader("💼 محفظتي الذكية (Smart Portfolio Tracker)")
st.write("أضف الأسهم التي اشتريتها بمتوسط السعر لمراقبة الربح/الخسارة وتحديد أهداف الخروج ووقف الخسارة بشكل ديناميكي.")

portfolio_list = st.session_state["user_data"].get("portfolio", [])

col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
with col_p1:
    new_p_ticker = st.selectbox("اختر السهم للإضافة:", options=[""] + list(stock_names.keys()), format_func=lambda x: f"{x.replace('.CA', '')} - {stock_names[x]}" if x else "اختر سهم...")
with col_p2:
    new_p_price = st.number_input("متوسط سعر الشراء:", min_value=0.0, format="%.3f")
with col_p3:
    st.write("")
    st.write("")
    if st.button("➕ إضافة للمحفظة"):
        if new_p_ticker and new_p_price > 0:
            # Check if exists
            exists = False
            for p in portfolio_list:
                if p["ticker"] == new_p_ticker:
                    p["buy_price"] = new_p_price
                    exists = True
            if not exists:
                portfolio_list.append({"ticker": new_p_ticker, "buy_price": new_p_price})
            
            st.session_state["user_data"]["portfolio"] = portfolio_list
            fb.update_user_data(st.session_state["user"]["localId"], st.session_state["user"]["idToken"], st.session_state["user_data"])
            st.rerun()

if portfolio_list:
    st.write("📊 **تفاصيل المحفظة:**")
    for p in portfolio_list:
        ticker = p["ticker"]
        buy_price = p["buy_price"]
        
        arabic_name = stock_names.get(ticker, "")
        sector_name = stock_sectors.get(ticker, "غير محدد")
        index_name = "EGX30" if ticker in egx30_list else ("EGX70" if ticker in egx70_list else "-")
        
        res = analyze_stock_cached(ticker, "60d", "15m", arabic_name, sector_name, index_name)
        if res:
            current_price = res['السعر الحالي']
            pnl_perc = ((current_price - buy_price) / buy_price) * 100
            
            res_live = analyze_stock_cached(ticker, yf_period, yf_interval, arabic_name, sector_name, index_name)
            if res_live:
                current_price = res_live['السعر الحالي']
                pnl_perc = ((current_price - buy_price) / buy_price) * 100
                
                radar_sl = res_live['وقف الخسارة']
                radar_tp = res_live['الهدف المتوقع']
                
                if radar_sl != "-":
                    sl_val = float(radar_sl)
                    tp_val = float(radar_tp)
                    if sl_val < buy_price:
                        act_sl = sl_val
                    else:
                        act_sl = buy_price * 0.95 # Fallback 5%
                else:
                    act_sl = buy_price * 0.95
                    tp_val = buy_price * 1.05
                
                # Action Logic
                if current_price <= act_sl:
                    action = "🛑 فعل وقف الخسارة!"
                    card_color = "#ffebee"
                elif current_price >= tp_val:
                    action = "🎯 جني أرباح!"
                    card_color = "#e8f5e9"
                else:
                    if pnl_perc > 0:
                        action = "🛡️ احتفاظ (ربح)"
                        card_color = "#f0fdf4"
                    else:
                        action = "⏳ احتفاظ (انتظار)"
                        card_color = "#fffbeb"
                
                pnl_str = f"+{pnl_perc:.1f}%" if pnl_perc > 0 else f"{pnl_perc:.1f}%"
                pnl_color = "green" if pnl_perc > 0 else "red"
                
                st.markdown(f\"\"\"
                <div style='background:{card_color}; border:1px solid #ddd; padding:15px; border-radius:10px; margin-bottom:10px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <h4 style='margin:0;color:#1e3c72;'>{ticker.replace('.CA', '')} {arabic_name}</h4>
                            <span style='font-size:14px;color:#555;'>شراء: {buy_price} | الحالي: <b>{current_price}</b></span>
                        </div>
                        <div style='text-align:right;'>
                            <h3 style='margin:0;color:{pnl_color};'>{pnl_str}</h3>
                            <span style='font-size:14px;font-weight:bold;'>{action}</span>
                        </div>
                    </div>
                    <hr style='margin:8px 0;'/>
                    <div style='font-size:13px; color:#666; display:flex; justify-content:space-between;'>
                        <span>🎯 الهدف: {tp_val:.2f}</span>
                        <span>🛑 وقف الخسارة: {act_sl:.2f}</span>
                    </div>
                </div>
                \"\"\", unsafe_allow_html=True)
                
                if st.button(f"❌ بيع/حذف من المحفظة", key=f"del_{ticker}"):
                    st.session_state["user_data"]["portfolio"] = [x for x in portfolio_list if x["ticker"] != ticker]
                    fb.update_user_data(st.session_state["user"]["localId"], st.session_state["user"]["idToken"], st.session_state["user_data"])
                    st.rerun()
"""

# Insert Portfolio after Favorites
content = content.replace('st.markdown("---")\\n\\nspecific_search_stocks', portfolio_logic + '\\n\\nst.markdown("---")\\n\\nspecific_search_stocks')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
