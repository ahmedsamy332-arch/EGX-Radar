import sys

with open('analyzer.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_func = """
@st.cache_data(ttl=120, show_spinner=False)
def get_daily_performance(ticker, arabic_name):
    tv = get_tv()
    if not tv: return None
    
    try:
        tv_ticker = ticker.replace('.CA', '')
        df_tv = tv.get_hist(symbol=tv_ticker, exchange='EGX', interval=Interval.in_daily, n_bars=2)
        if df_tv is not None and len(df_tv) >= 2:
            close_today = float(df_tv['close'].iloc[-1])
            close_yest = float(df_tv['close'].iloc[-2])
            vol_today = float(df_tv['volume'].iloc[-1])
            
            change_perc = ((close_today - close_yest) / close_yest) * 100
            
            return {
                "اسم السهم": arabic_name if arabic_name else tv_ticker,
                "الكود": ticker,
                "السعر": round(close_today, 3),
                "التغير (%)": round(change_perc, 2),
                "حجم التداول": int(vol_today),
                "قيمة التداول (تقريبية)": int(vol_today * close_today)
            }
    except Exception as e:
        pass
    return None
"""

if "get_daily_performance" not in content:
    content += "\n" + new_func

with open('analyzer.py', 'w', encoding='utf-8') as f:
    f.write(content)
