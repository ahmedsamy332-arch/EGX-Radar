egx30_list = ["COMI.CA", "FWRY.CA", "EFIH.CA", "EGAL.CA", "ABUK.CA", "TMGH.CA", "HRHO.CA", "SWDY.CA", "ETEL.CA", "ESRS.CA", "AMOC.CA", "SKPC.CA", "HELI.CA", "PHDC.CA", "MFPC.CA", "MASR.CA", "ORAS.CA", "ORWE.CA", "ISPH.CA", "CIEB.CA", "ADIB.CA", "AUTO.CA", "CLHO.CA", "JUFO.CA", "SUGR.CA", "BTFH.CA", "DOMT.CA", "OIH.CA", "MTIE.CA", "CCAP.CA", "EMFD.CA", "RMDA.CA", "QNBA.CA", "HDBK.CA", "SAUD.CA"]
egx70_list = [t for t in stock_names.keys() if t not in egx30_list]
egx100_list = egx30_list + egx70_list

favorites_list = st.session_state['user_data'].get('favorites', [])
portfolio_list = st.session_state['user_data'].get('portfolio', [])
st.markdown('---')

is_admin = st.session_state['user'].get('email', '').strip().lower() == "ahmedsamy332@gmail.com"
