import streamlit as st
import requests
import pandas as pd
import datetime
import time
import os
import html
import sys
import logging

st.set_page_config(page_title="ADHD AI Coach", layout="wide", initial_sidebar_state="expanded")

# Configure logging to output to console (stdout) for cloud platforms like Render.
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.database.db import create_user, verify_user, save_result, save_feedback, update_user_contact
# Import API directly to bypass network calls (Saves memory & prevents connection errors)
from src.api.main_api import chat, ChatRequest


def render_chat_text(text):
    return html.escape(str(text)).replace("\n", "<br>")

st.markdown("""
<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    background: #000000 !important;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 18px;
    color: #ffffff;
}

[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #111827 0%, #0f172a 100%) !important;
}

/* Make main containers purely black */
.main, [data-testid="stAppViewContainer"] {
    background: #000000 !important;
}

/* Header */
.header-container {
    background: transparent;
    color: white;
    padding: 16px 24px;
    box-shadow: none;
    margin-bottom: 0;
    text-align: left;
    border-bottom: 1px solid #1e1e1e;
}

.header-title {
    font-size: 32px;
    font-weight: 500;
    margin-bottom: 8px;
    color: #e0e0e0;
}

.header-subtitle {
    font-size: 20px;
    opacity: 0.95;
    font-weight: 500;
}

.chat-container {
    display: flex;
    flex-direction: column;
    padding: 24px;
}

.chat-messages {
    height: 55vh; /* Adjusted for sticky form */
    flex: 1;
    overflow-y: auto;
    margin-bottom: 24px;
    padding-right: 12px;
    display: flex;
    flex-direction: column-reverse; /* Auto-scrolls to bottom */
    gap: 12px;
}

.user-message {
    display: flex;
    justify-content: flex-end;
}

.user-message-bubble {
    background: #2a2a2e; /* Charcoal grey */
    color: #e0e0e0;
    padding: 16px 20px;
    border-radius: 18px;
    max-width: 75%;
    word-wrap: break-word;
    font-size: 20px;
    font-weight: 500;
    line-height: 1.6;
}

.bot-message {
    display: flex;
    justify-content: flex-start;
}

.bot-message-bubble {
    background: #1e1e1e; /* Darker charcoal */
    color: #e0e0e0;
    padding: 16px 20px;
    border-radius: 18px;
    max-width: 85%;
    word-wrap: break-word;
    font-size: 20px;
    font-weight: 500;
    line-height: 1.6;
}

.thinking {
    display: flex;
    justify-content: flex-start;
}

.thinking-bubble {
    background: #000000;
    color: #aaaaaa;
    padding: 16px 20px;
    border-radius: 12px;
    font-size: 20px;
    border: 1px solid #333333;
    font-style: italic;
    font-weight: 500;
    line-height: 1.6;
}

/* Sticky Form Container */
div[data-testid="stForm"]:has(form[aria-label="chat_input_form"]) {
    position: sticky;
    bottom: 50px; /* Space for the feedback expander */
    background: #000000;
    z-index: 999;
    padding: 10px 0;
    border: none;
}

/* Pill Design for Chat Form */
form[aria-label="chat_input_form"] {
    background: #1e1e1e !important;
    border-radius: 40px !important;
    border: 1px solid #333 !important;
    padding: 5px 15px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.5) !important;
}

/* Force chat input and button to stay on one line on mobile */
form[aria-label="chat_input_form"] [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 8px !important;
}

form[aria-label="chat_input_form"] [data-testid="column"]:last-child {
    flex-grow: 0 !important;
    min-width: 50px !important;
}

/* Make inputs inside chat form transparent */
form[aria-label="chat_input_form"] div[data-testid="stTextInput"] input {
    background: transparent !important;
    border: none !important;
    color: #e0e0e0 !important;
    box-shadow: none !important;
    font-size: 18px !important;
    padding: 14px 20px !important;
    font-family: sans-serif !important;
}
form[aria-label="chat_input_form"] div[data-testid="stTextInput"] input:focus {
    border: none !important;
    box-shadow: none !important;
}

/* Submit button */
form[aria-label="chat_input_form"] div[data-testid="stFormSubmitButton"] button {
    background: #333 !important;
    border: none !important;
    color: #fff !important;
    font-size: 22px !important;
    width: 44px !important;
    height: 44px !important;
    border-radius: 50% !important;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 !important;
    margin: 0 !important;
}
form[aria-label="chat_input_form"] div[data-testid="stFormSubmitButton"] button:hover {
    background: #555 !important;
    color: #fff !important;
}

/* Feedback Expander Sticky */
.main div[data-testid="stExpander"]:last-of-type {
    position: sticky !important;
    bottom: 0 !important;
    background: #000000 !important;
    z-index: 1000 !important;
    border-top: 1px solid #333;
    border-radius: 0;
    margin-bottom: 0;
}

.stat-card {
    background: linear-gradient(135deg, #48bb7825 0%, #38a16925 100%);
    padding: 16px;
    border-radius: 12px;
    margin-bottom: 12px;
    border-left: 4px solid #48bb78;
    text-align: center;
}

.stat-value {
    font-size: 40px;
    font-weight: bold;
    color: #22543d;
}

.stat-label {
    font-size: 16px;
    color: #276749;
    text-transform: uppercase;
    font-weight: 600;
}

.habit-badge {
    display: inline-block;
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 8px 14px;
    border-radius: 20px;
    font-size: 16px;
    margin: 6px 4px;
    font-weight: 600;
}

.goal-item {
    background: #1f2937;
    padding: 14px;
    border-radius: 10px;
    margin-bottom: 12px;
    color: #e2e7ff;
    border-left: 4px solid #667eea;
    font-size: 18px;
    font-weight: 500;
}

.task-item {
    background: #1f2937;
    padding: 14px;
    border-radius: 10px;
    margin-bottom: 12px;
    color: #e2e7ff;
    border-left: 4px solid #48bb78;
    font-size: 18px;
    font-weight: 500;
}

.feedback-box {
    background: linear-gradient(135deg, #e0f2fe 0%, #f0f9ff 100%);
    border: 2px solid #0284c7;
    border-radius: 16px;
    padding: 20px;
    margin-top: 24px;
}

.feedback-title {
    font-size: 24px;
    font-weight: bold;
    color: #0c4a6e;
    margin-bottom: 12px;
}

.feedback-description {
    font-size: 18px;
    color: #0c4a6e;
    margin-bottom: 16px;
    line-height: 1.5;
}

div[data-testid="stTextArea"] textarea {
    font-size: 18px !important;
    border-radius: 12px !important;
    border: 2px solid #0284c7 !important;
    padding: 12px 16px !important;
    min-height: 100px !important;
}

/* Responsive Adjustments for Mobile */
@media (max-width: 768px) {
    .chat-messages { height: 60vh; }
    .user-message-bubble, .bot-message-bubble, .thinking-bubble {
        font-size: 16px;
        padding: 12px 16px;
        max-width: 90%;
    }
    .header-title { font-size: 24px; }
    .header-subtitle { font-size: 16px; }
    form[aria-label="chat_input_form"] div[data-testid="stTextInput"] input {
        font-size: 16px !important;
        padding: 10px 15px !important;
    }
    form[aria-label="chat_input_form"] div[data-testid="stFormSubmitButton"] button {
        width: 40px !important;
        height: 40px !important;
        font-size: 20px !important;
    }
}

</style>
""", unsafe_allow_html=True)


# -------- STATE --------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "progress" not in st.session_state:
    st.session_state.progress = []

if "analysis" not in st.session_state:
    st.session_state.analysis = {}

if "goals" not in st.session_state:
    st.session_state.goals = [
        "📚 Improve focus sessions",
        "✅ Complete daily tasks",
        "💪 Build consistency"
    ]

if "tasks" not in st.session_state:
    st.session_state.tasks = [
        "Review medication schedule",
        "Practice time blocking",
        "Reflect on productivity"
    ]

if "habits" not in st.session_state:
    st.session_state.habits = ["Morning Routine", "Exercise", "Meditation"]

if "session_count" not in st.session_state:
    st.session_state.session_count = 0

if "completion_rate" not in st.session_state:
    st.session_state.completion_rate = 72

if "timer_active" not in st.session_state:
    st.session_state.timer_active = False

if "timer_seconds" not in st.session_state:
    st.session_state.timer_seconds = 25 * 60

if "timer_duration" not in st.session_state:
    st.session_state.timer_duration = 25 * 60

if "timer_start" not in st.session_state:
    st.session_state.timer_start = None

if "activity_log" not in st.session_state:
    st.session_state.activity_log = []

if "phone_distractions" not in st.session_state:
    st.session_state.phone_distractions = 0

if "current_streak" not in st.session_state:
    st.session_state.current_streak = 0

if "longest_streak" not in st.session_state:
    st.session_state.longest_streak = 0

if "badges" not in st.session_state:
    st.session_state.badges = []

if "level" not in st.session_state:
    st.session_state.level = 1

if "points" not in st.session_state:
    st.session_state.points = 0

if "last_session_date" not in st.session_state:
    st.session_state.last_session_date = None

if "reflection" not in st.session_state:
    st.session_state.reflection = ""

if "feedback_list" not in st.session_state:
    st.session_state.feedback_list = []

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "username" not in st.session_state:
    st.session_state.username = None

if "contact_linked" not in st.session_state:
    st.session_state.contact_linked = False

if "contact_info" not in st.session_state:
    st.session_state.contact_info = None

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>🧠 ADHD AI Coach Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        login_tab, register_tab = st.tabs(["Login", "Register"])
        with login_tab:
            with st.form("login_form"):
                log_user = st.text_input("Username")
                log_pass = st.text_input("Password", type="password")
                remember_me = st.checkbox("Remember me")
                if st.form_submit_button("Login", use_container_width=True):
                    if verify_user(log_user, log_pass):
                        st.session_state.authenticated = True
                        st.session_state.username = log_user
                        st.session_state.remember_me = remember_me
                        st.session_state.contact_linked = False # Force check for existing users
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        with register_tab:
            with st.form("register_form"):
                reg_user = st.text_input("New Username")
                reg_pass = st.text_input("New Password", type="password")
                reg_contact = st.text_input("Email or Phone Number (Required)")
                if st.form_submit_button("Register", use_container_width=True):
                    if reg_user and reg_pass and reg_contact:
                        import re
                        is_email = re.match(r"[^@]+@[^@]+\.[^@]+", reg_contact)
                        is_phone = re.match(r"^\+?[\d\s-]{10,}$", reg_contact)
                        
                        if not (is_email or is_phone):
                            st.error("Please enter a valid email or phone number.")
                        elif len(reg_pass) < 8 or not re.search(r"[A-Z]", reg_pass) or not re.search(r"[a-z]", reg_pass) or not re.search(r"[0-9]", reg_pass) or not re.search(r"[@$!%*?&#\-_]", reg_pass):
                            st.error("Password must be at least 8 characters long, include an uppercase letter, a lowercase letter, a number, and a special character.")
                        else:
                            if create_user(reg_user, reg_pass, reg_contact):
                                st.session_state.contact_info = reg_contact
                                st.success("Registration successful! You can now log in.")
                            else:
                                st.error("Username already exists.")
                    else:
                        st.error("Please provide username, password, and contact info")
    st.stop()

# -------- MANDATORY CONTACT LINKING FOR EXISTING USERS --------
if st.session_state.authenticated and not st.session_state.get("contact_linked", False):
    st.markdown("<h2 style='text-align: center; margin-top: 50px;'>⚠️ Account Update Required</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #cbd5e1;'>To secure your account and enable real-time features, you must link an email or phone number to continue.</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("link_contact_form"):
            contact_info = st.text_input("Email or Phone Number")
            if st.form_submit_button("Link Account", use_container_width=True):
                import re
                is_email = re.match(r"[^@]+@[^@]+\.[^@]+", contact_info)
                is_phone = re.match(r"^\+?[\d\s-]{10,}$", contact_info)
                
                if not (is_email or is_phone):
                    st.error("Please enter a valid email or phone number.")
                else:
                    update_user_contact(st.session_state.username, contact_info)
                    st.session_state.contact_info = contact_info
                    st.session_state.contact_linked = True
                    st.success("Account successfully linked!")
                    time.sleep(1)
                    st.rerun()
    st.stop()

if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "sleep_hours": 0,
        "stress_level": 0,
        "phone_distractions": 0
    }

if "check_in_completed" not in st.session_state:
    st.session_state.check_in_completed = False

# -------- SIDEBAR DASHBOARD --------
with st.sidebar:
    st.markdown('<h2 style="color: #e2e7ff; text-align: center; font-size: 32px;">🧠 ADHD Dashboard</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: #cbd5e1; text-align: center; font-size: 18px;">Your productivity companion</p>', unsafe_allow_html=True)
    
    st.markdown(f'<div style="text-align:center; margin-bottom: 10px; color:#cbd5e1;">Logged in as: <b>{st.session_state.username}</b></div>', unsafe_allow_html=True)
    if st.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

    if not st.session_state.check_in_completed:
        st.warning("⚠️ Please complete your daily check-in below for personalized coaching!")

    # Daily Check-in
    with st.expander("📝 Daily Check-in", expanded=not st.session_state.check_in_completed):
        st.session_state.user_data["sleep_hours"] = st.slider(
            "Sleep Hours", 0, 12, st.session_state.user_data["sleep_hours"],
            help="How many hours of sleep did you get last night?"
        )
        st.session_state.user_data["phone_distractions"] = st.slider(
            "Phone Distractions (Hours)", 0, 24, st.session_state.user_data["phone_distractions"],
            help="Estimate how many hours your phone distracted you yesterday. Tip: Check 'Screen Time' or 'Digital Wellbeing' in your phone settings!"
        )
        
        if not st.session_state.check_in_completed:
            if st.button("Save Check-in", use_container_width=True):
                # Calculate initial stress immediately from check-in data
                calc_stress = 5
                sleep = st.session_state.user_data["sleep_hours"]
                phone = st.session_state.user_data["phone_distractions"]
                
                # Sleep impact
                if sleep < 4:
                    calc_stress += 4  # Severe sleep deprivation
                elif sleep < 6:
                    calc_stress += 2  # Moderate sleep deprivation
                elif sleep >= 8:
                    calc_stress -= 2  # Well rested
                
                # Phone distraction impact
                if phone > 8:
                    calc_stress += 3  # Very high distraction
                elif phone > 4:
                    calc_stress += 1  # High distraction
                elif phone < 2:
                    calc_stress -= 1  # Low distraction
                
                st.session_state.user_data["stress_level"] = max(1, min(10, calc_stress))
                st.session_state.check_in_completed = True
                st.rerun()
    
    # Focus Session Status
    st.markdown('### ⏱️ Focus Session')
    
    if not st.session_state.timer_active:
        selected_mins = st.slider("Set Timer (minutes)", 5, 120, st.session_state.timer_duration // 60, 5, key="timer_slider")
        if selected_mins * 60 != st.session_state.timer_duration:
            st.session_state.timer_duration = selected_mins * 60
            st.session_state.timer_seconds = st.session_state.timer_duration
            
    status_text = "🟢 Active" if st.session_state.timer_active else "⚪ Inactive"
    remaining = st.session_state.timer_seconds
    if st.session_state.timer_active and st.session_state.timer_start:
        elapsed = int(time.time() - st.session_state.timer_start)
        remaining = max(0, st.session_state.timer_seconds - elapsed)
        if remaining == 0:
            st.session_state.timer_active = False
            st.session_state.timer_start = None
            st.session_state.timer_seconds = st.session_state.timer_duration
            status_text = "✅ Completed"
            
            # Award points based on duration (1 point per minute)
            points_earned = st.session_state.timer_duration // 60
            st.session_state.points += points_earned
            if st.session_state.tasks:
                st.session_state.tasks.pop(0)
            
            st.toast(f"Focus session completed! Earned {points_earned} Points.", icon="🎯")
    mins = remaining // 60
    secs = remaining % 60
    st.markdown(f'<div style="background: #1f2937; padding: 16px; border-radius: 10px; color: #e2e7ff; text-align: center; margin-bottom: 12px; font-size: 18px;"><b>{status_text}</b><br>Remaining: <b>{mins:02d}:{secs:02d}</b></div>', unsafe_allow_html=True)
    
    # Focus Controls
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button('▶ Start', key='start_focus_sidebar', use_container_width=True):
            if not st.session_state.timer_active:
                st.session_state.timer_active = True
                st.session_state.timer_start = time.time()
                st.rerun()
    with col2:
        if st.button('⏹ Stop', key='stop_focus_sidebar', use_container_width=True):
            if st.session_state.timer_active:
                st.session_state.timer_active = False
                st.session_state.timer_seconds = st.session_state.timer_duration
                st.rerun()
    
    st.divider()
    
    # Quick Stats
    st.markdown('### 📊 Quick Stats')
    stat_col1, stat_col2 = st.sidebar.columns(2)
    with stat_col1:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{st.session_state.current_streak}</div><div class="stat-label">Streak</div></div>', unsafe_allow_html=True)
    with stat_col2:
        st.markdown(f'<div class="stat-card"><div class="stat-value">Lvl {st.session_state.level}</div><div class="stat-label">Level</div></div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="stat-card"><div class="stat-value">{st.session_state.points}</div><div class="stat-label">Points</div></div>', unsafe_allow_html=True)
    
    # AI Detected Stress Status
    detected_stress = st.session_state.user_data.get('stress_level', 0)
    if detected_stress == 0:
        stress_label, s_color, s_bg, s_dark = "Pending", "#9ca3af", "#9ca3af25", "#4b5563" # Gray
    elif detected_stress <= 3:
        stress_label, s_color, s_bg, s_dark = "Low", "#10b981", "#10b98125", "#047857" # Green
    elif detected_stress <= 7:
        stress_label, s_color, s_bg, s_dark = "Moderate", "#f59e0b", "#f59e0b25", "#b45309" # Amber
    else:
        stress_label, s_color, s_bg, s_dark = "High", "#ef4444", "#ef444425", "#b91c1c" # Red
        
    st.markdown(f'''
    <div class="stat-card" style="border-left-color: {s_color}; background: linear-gradient(135deg, {s_bg} 0%, {s_dark}25 100%);">
        <div class="stat-value" style="color: {s_color}; font-size: 32px;">{stress_label} ({detected_stress}/10)</div>
        <div class="stat-label" style="color: {s_dark};">AI Detected Stress</div>
    </div>''', unsafe_allow_html=True)
    
    if detected_stress >= 8:
        st.error("🚨 High stress detected! Your AI Coach has adjusted to prioritize gentle support over productivity today.")

    st.divider()
    
    # Goals
    st.markdown('### 🎯 Today\'s Goals')
    for goal in st.session_state.goals:
        st.markdown(f'<div class="goal-item">{goal}</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Tasks
    st.markdown('### ✓ Tasks')
    for task in st.session_state.tasks:
        st.markdown(f'<div class="task-item">□ {task}</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Active Habits
    st.markdown('### 🔥 Active Habits')
    habits_html = "".join([f'<div class="habit-badge">{habit}</div>' for habit in st.session_state.habits])
    st.markdown(f'<div>{habits_html}</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Badges
    if st.session_state.badges:
        st.markdown('### 🏅 Earned Badges')
        badges_html = "".join([f'<div class="habit-badge">{badge}</div>' for badge in st.session_state.badges])
        st.markdown(f'<div>{badges_html}</div>', unsafe_allow_html=True)
        st.divider()
    
    # Reflection
    st.markdown('### 📝 Daily Reflection')
    reflection_input = st.text_area("Share your thoughts...", value=st.session_state.reflection, key="reflection_sidebar", height=80, label_visibility="collapsed")
    if reflection_input != st.session_state.reflection:
        st.session_state.reflection = reflection_input


# -------- MAIN GPT-STYLE CHAT INTERFACE --------
st.markdown("""
<div class="header-container">
    <div class="header-title">💬 ADHD AI Coach</div>
    <div class="header-subtitle">Your AI-powered ADHD productivity assistant</div>
</div>
""", unsafe_allow_html=True)

# Chat interface - make it expandable
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

chat_placeholder = st.empty()

# Inline Chat Input Form - stays above feedback
with st.form("chat_input_form", clear_on_submit=True):
    cols = st.columns([10, 1])
    with cols[0]:
        user_input = st.text_input("Message", placeholder="Ask your ADHD Coach...", label_visibility="collapsed")
    with cols[1]:
        submit_btn = st.form_submit_button("↑", use_container_width=True)

if submit_btn and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    # Do not call st.rerun() here so the UI updates immediately!

is_thinking = st.session_state.messages and st.session_state.messages[-1]["role"] == "user"

if not st.session_state.messages:
    chat_placeholder.markdown('<div style="height: 30vh;"></div><div style="text-align:center; color:#aaaaaa; font-size:20px;">Start a conversation below!</div><div style="height: 10vh;"></div>', unsafe_allow_html=True)
else:
    chat_html = '<div class="chat-messages">'
    if is_thinking:
        chat_html += '<div class="thinking"><div class="thinking-bubble">⏳ Thinking...</div></div>'

    for msg in reversed(st.session_state.messages):
        if msg["role"] == "user":
            chat_html += f'<div class="user-message"><div class="user-message-bubble">{render_chat_text(msg["content"])}</div></div>'
        else:
            chat_html += f'<div class="bot-message"><div class="bot-message-bubble">{render_chat_text(msg["content"])}</div></div>'
    chat_html += '</div>'
    chat_placeholder.markdown(chat_html, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Process the backend call if we are thinking
if is_thinking:
    with st.spinner("AI Coach is typing..."):
        try:
            user_input_text = st.session_state.messages[-1]["content"]
            history = st.session_state.messages[:-1]
            
            request_data = ChatRequest(
                text=user_input_text,
                history=history,
                user_data=st.session_state.user_data
            )
            
            # Call the API function directly instead of making an HTTP request
            data = chat(request_data)
            
            reply = data.get("reply", "⚠️ No response")
            analysis = data.get("analysis", {})
            scores = data.get("scores", {})
            
            # Extract current stress level from session
            current_stress = st.session_state.user_data.get("stress_level", 5)
            
            # Make an adjustment based on the current message's emotion
            is_stressed_in_text = analysis.get("emotion") == "stress"
            
            # Fallback heuristic
            stress_keywords = ["stress", "overwhelm", "anxious", "panic", "too much", "hard", "stuck", "tired", "sad", "depressed"]
            if any(kw in user_input_text.lower() for kw in stress_keywords):
                is_stressed_in_text = True
                
            if is_stressed_in_text:
                new_stress = min(10, current_stress + 2) # Nudge up stronger
            else:
                new_stress = max(1, current_stress - 1) # Nudge down when calm
            
            st.session_state.user_data["stress_level"] = new_stress
            
            # Dynamic Updates based on AI analysis
            interventions = data.get("interventions", [])
            if interventions:
                st.session_state.goals = []
                st.session_state.tasks = []
                
                timer_triggered = False
                for inv in interventions:
                    st.session_state.goals.append(f"🎯 {inv['title']}")
                    st.session_state.tasks.append(inv['action'])
                    
                    # Auto-start focus timer if suggested
                    if inv['category'] == 'focus' and not st.session_state.timer_active and not timer_triggered:
                        st.session_state.timer_active = True
                        st.session_state.timer_start = time.time()
                        timer_triggered = True
                        st.toast("Auto-started focus timer based on AI suggestion!", icon="⏱️")
        except Exception as e:
            reply = f"❌ Error: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.session_count += 1
    
    # Update gamification
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    if st.session_state.last_session_date == yesterday.isoformat():
        st.session_state.current_streak += 1
    elif st.session_state.last_session_date != today.isoformat():
        st.session_state.current_streak = 1
    
    if st.session_state.current_streak > st.session_state.longest_streak:
        st.session_state.longest_streak = st.session_state.current_streak
    st.session_state.last_session_date = today.isoformat()
    st.session_state.points += 5
    new_level = (st.session_state.points // 50) + 1
    
    if new_level > st.session_state.level:
        st.session_state.level = new_level
    if st.session_state.current_streak >= 3 and "3-Day Streak" not in st.session_state.badges:
        st.session_state.badges.append("3-Day Streak")
    if st.session_state.current_streak >= 7 and "Week Warrior" not in st.session_state.badges:
        st.session_state.badges.append("Week Warrior")
    if st.session_state.points >= 100 and "Century Club" not in st.session_state.badges:
        st.session_state.badges.append("Century Club")
    
    st.rerun()

# Feedback Section - collapsed by default
with st.expander("💡 Help Us Improve"):
    st.markdown("Your feedback helps us make the ADHD AI Coach better. Share your thoughts, suggestions, or issues you encountered.")
    
    with st.form("feedback_form", clear_on_submit=True):
        feedback_col1, feedback_col2 = st.columns([3, 1])
        with feedback_col1:
            feedback_text = st.text_area("📝 Your Feedback", placeholder="Tell us what you think...", height=100, label_visibility="collapsed")
        with feedback_col2:
            feedback_rating = st.selectbox("Rating", ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"], index=4, label_visibility="collapsed")

        submit_feedback = st.form_submit_button("💬 Submit Feedback", use_container_width=True)
        
        if submit_feedback:
            if feedback_text:
                feedback_entry = {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "rating": feedback_rating,
                    "text": feedback_text
                }
                st.session_state.feedback_list.append(feedback_entry)
                
                # Save feedback to Database
                try:
                    save_feedback(st.session_state.username, feedback_rating, feedback_text)
                except Exception:
                    pass
                
                st.success("✅ Thank you! Your feedback has been recorded.")
                st.balloons()
                time.sleep(1.5)
                st.rerun()
            else:
                st.warning("Please enter some feedback before submitting.")

# Display feedback summary
if st.session_state.feedback_list:
    with st.expander(f"📋 Feedback History ({len(st.session_state.feedback_list)})"):
        for i, feedback in enumerate(reversed(st.session_state.feedback_list), 1):
            st.markdown(f"""
            **#{i} - {feedback['timestamp']} | {feedback['rating']}**
            
            {feedback['text']}
            """)
