import subprocess
import io

# Get file from git directly in utf-8
result = subprocess.run(["git", "show", "0ae6eba:app.py"], capture_output=True, text=False)
content = result.stdout.decode('utf-8')

lines = content.splitlines()

data_lines = []

# Find start and end
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if "egx_stocks = {" in line:
        start_idx = i
    if "tab_names = [" in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    with io.open('data_assets.py', 'w', encoding='utf-8') as f:
        f.write("import streamlit as st\n\n")
        for line in lines[start_idx:end_idx]:
            f.write(line + "\n")
        f.write("\n")
        f.write("favorites_list = st.session_state['user_data'].get('favorites', []) if 'user_data' in st.session_state else []\n")
        f.write("portfolio_list = st.session_state['user_data'].get('portfolio', []) if 'user_data' in st.session_state else []\n")
        f.write("is_admin = st.session_state['user'].get('email', '').strip().lower() == 'ahmedsamy332@gmail.com' if 'user' in st.session_state and st.session_state['user'] else False\n")
