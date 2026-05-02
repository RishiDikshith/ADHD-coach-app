import re

with open('d:\\ADHD_Productivity_MVP\\frontend\\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the avatar button that toggles the settings
content = re.sub(r'\s*if st\.button\(initial, key="top_right_avatar_btn", help="Toggle Settings"\):\s*st\.session_state\.show_settings = not st\.session_state\.show_settings\s*st\.rerun\(\)', '', content)

# Remove the settings modal display block
content = re.sub(r'# -------- SHOW SETTINGS MODAL IF TRIGGERED --------\s*if st\.session_state\.show_settings:\s*modal_col1, modal_col2, modal_col3 = st\.columns\(\[1, 2, 1\]\)\s*with modal_col2:\s*with st\.container\(\):\s*render_settings_modal\(\)\s*st\.stop\(\)', '', content)

with open('d:\\ADHD_Productivity_MVP\\frontend\\app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("SUCCESS")
