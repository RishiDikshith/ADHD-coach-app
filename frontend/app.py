import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import html
import sys
import logging
import random
import string
import re

# Fallback for st.fragment in older Streamlit versions
if hasattr(st, "fragment"):
    st_fragment = st.fragment
elif hasattr(st, "experimental_fragment"):
    st_fragment = st.experimental_fragment
else:
    def st_fragment(*args, **kwargs):
        if len(args) == 1 and callable(args[0]): return args[0]
        return lambda func: func

st.set_page_config(page_title="ADHD AI Coach", layout="wide", initial_sidebar_state="expanded")

# Configure logging for cloud platforms like Render.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Import utilities for session, settings, and avatar
from src.utils.session_manager import SessionManager
from src.utils.settings_manager import SettingsManager
from src.utils.avatar import render_avatar_html, get_avatar_initials, get_avatar_color

from src.database.db import create_user, verify_user, save_result, save_feedback, update_user_contact, reset_password, get_user_by_username, set_user_otp, activate_user
# OTP Email Sending Utility
from src.utils.email_sender import send_otp_email
# Import API directly to bypass network calls (Saves memory & prevents connection errors)
from src.api.main_api import chat, ChatRequest
import io

# Initialize session and settings managers
session_manager = SessionManager()
settings_manager_instance = None  # Will be initialized after authentication

# Initialize cookie manager with lazy loading to prevent SessionInfo errors
cookie_manager = None

def initialize_cookie_manager():
    """Lazily initialize cookie manager after session state is ready"""
    global cookie_manager
    if cookie_manager is not None:
        return
    
    try:
        import extra_streamlit_components as stx
        cookie_manager = stx.CookieManager(key="cookie_manager")
    except ImportError:
        logging.warning("extra_streamlit_components not found. 'Remember Me' functionality will be disabled.")
        class MockCookieManager:
            def get(self, cookie, *args, **kwargs): return None
            def set(self, cookie, val, *args, **kwargs): pass
            def delete(self, cookie, *args, **kwargs): pass
        cookie_manager = MockCookieManager()
 
def generate_otp(length=6):
    """Generate a random numeric OTP."""
    return "".join(random.choices(string.digits, k=length))
 
@st.cache_data(max_entries=500)
def render_chat_text(text):
    return html.escape(str(text)).replace("\n", "<br>")

@st.cache_data(max_entries=100)
def get_cached_avatar_info(username):
    return get_avatar_initials(username), get_avatar_color(username)

def generate_chat_pdf(messages):
    try:
        from fpdf import FPDF
    except ImportError:
        return None
        
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(0, 10, "ADHD AI Coach - Chat History", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(10)
    
    for msg in messages:
        role = "You" if msg["role"] == "user" else "AI Coach"
        # Latin-1 encoding gracefully replaces emojis with '?' to prevent FPDF text rendering crashes
        safe_text = str(msg.get("content", "")).encode('latin-1', 'replace').decode('latin-1')
        
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 8, f"{role}:", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", '', 11)
        pdf.multi_cell(0, 6, safe_text)
        pdf.ln(5)
        
    try:
        return bytes(pdf.output())
    except Exception:
        return pdf.output(dest='S').encode('latin-1')

def apply_theme():
    css_vars = """
    :root {
        --bg-color: #000000;
        --text-color: #ffffff;
        --chat-user-bg: #1f2937;
        --chat-bot-bg: #000000;
        --input-bg: #111827;
        --border-color: #374151;
        --btn-bg: #1f2937;
        --btn-hover: #374151;
        --muted-text: #9ca3af;
        --feedback-bg: linear-gradient(135deg, #111827 0%, #000000 100%);
        --feedback-border: #374151;
        --feedback-text: #ffffff;
        
        /* Sidebar remains constant (DARK) */
        --sidebar-bg: linear-gradient(135deg, #111827 0%, #0f172a 100%);
        --sidebar-text: #e2e7ff;
        --sidebar-subtext: #9ca3af;
        --item-bg: #1f2937;
        --item-hover: #374151;
        --status-bg: #1f2937;
        --stat-bg: linear-gradient(135deg, rgba(72, 187, 120, 0.15) 0%, rgba(56, 161, 105, 0.15) 100%);
        --stat-border: #48bb78;
        --stat-value: #6ee7b7;
        --stat-label: #9ca3af;
        --badge-text: #ffffff;
        --badge-bg: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --goal-border: #667eea;
        --task-border: #48bb78;
    }
    """
    
    st.markdown(f"""
    <style>
    {css_vars}
    
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}

    body {{
        background: var(--bg-color) !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 18px;
        color: var(--text-color) !important;
    }}

    [data-testid="stSidebar"] {{
        background: var(--sidebar-bg) !important;
    }}

    /* Make main containers match theme */
    .main, [data-testid="stAppViewContainer"] {{
        background: var(--bg-color) !important;
    }}

    .main .stMarkdown p, .main .stMarkdown h1, .main .stMarkdown h2, .main .stMarkdown h3, .main .stMarkdown h4, .main .stMarkdown li,
    .main label, .main .stWidgetLabel span {{
        color: var(--text-color) !important;
    }}

    /* Sidebar texts */
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] .stMarkdown h1, [data-testid="stSidebar"] .stMarkdown h2, [data-testid="stSidebar"] .stMarkdown h3, [data-testid="stSidebar"] .stMarkdown h4, [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stWidgetLabel span {{
        color: var(--sidebar-text) !important;
    }}

    /* Header */
    .header-container {{
        background: transparent;
        color: var(--text-color);
        padding: 16px 24px;
        box-shadow: none;
        margin-bottom: 0;
        text-align: left;
        border-bottom: 1px solid var(--border-color);
    }}

    .header-title {{
        font-size: 32px;
        font-weight: 500;
        margin-bottom: 8px;
        color: var(--text-color);
    }}

    .header-subtitle {{
        font-size: 20px;
        opacity: 0.95;
        font-weight: 500;
        color: var(--text-color);
    }}

    .chat-container {{
        display: flex;
        flex-direction: column;
        padding: 24px;
    }}

    .chat-messages {{
        height: 55vh; /* Adjusted for sticky form */
        flex: 1;
        overflow-y: auto;
        margin-bottom: 24px;
        padding-right: 12px;
        display: flex;
        flex-direction: column-reverse; /* Auto-scrolls to bottom */
        gap: 12px;
    }}

    .user-message {{
        display: flex;
        justify-content: flex-end;
    }}

    .user-message-bubble {{
        background: var(--chat-user-bg);
        color: var(--text-color);
        padding: 16px 20px;
        border-radius: 18px;
        max-width: 75%;
        word-wrap: break-word;
        font-size: 20px;
        font-weight: 500;
        line-height: 1.6;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}

    .bot-message {{
        display: flex;
        justify-content: flex-start;
    }}

    .bot-message-bubble {{
        background: var(--chat-bot-bg);
        color: var(--text-color);
        padding: 16px 20px;
        border-radius: 18px;
        max-width: 85%;
        word-wrap: break-word;
        font-size: 20px;
        font-weight: 500;
        line-height: 1.6;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}

    .thinking {{
        display: flex;
        justify-content: flex-start;
    }}

    .thinking-bubble {{
        background: var(--bg-color);
        color: var(--muted-text);
        padding: 16px 20px;
        border-radius: 12px;
        font-size: 20px;
        border: 1px solid var(--border-color);
        font-style: italic;
        font-weight: 500;
        line-height: 1.6;
    }}

    /* Sticky Form Container */
    div[data-testid="stForm"]:has(form[aria-label="chat_input_form"]) {{
        position: sticky;
        bottom: 50px; /* Space for the feedback expander */
        background: var(--bg-color);
        z-index: 999;
        padding: 10px 0;
        border: none;
    }}

    /* Pill Design for Chat Form */
    form[aria-label="chat_input_form"] {{
        background: var(--input-bg) !important;
        border-radius: 40px !important;
        border: 1px solid var(--border-color) !important;
        padding: 5px 15px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
    }}

    /* Force chat input and button to stay on one line on mobile */
    form[aria-label="chat_input_form"] [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 8px !important;
    }}

    form[aria-label="chat_input_form"] [data-testid="column"]:first-child {{
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }}

    form[aria-label="chat_input_form"] [data-testid="column"]:last-child {{
        width: auto !important;
        flex: 0 0 auto !important;
        min-width: max-content !important;
    }}

    /* Make inputs inside chat form transparent */
    form[aria-label="chat_input_form"] div[data-testid="stTextInput"] input {{
        background: transparent !important;
        border: none !important;
        color: var(--text-color) !important;
        box-shadow: none !important;
        font-size: 18px !important;
        padding: 14px 20px !important;
        font-family: sans-serif !important;
        -webkit-text-fill-color: var(--text-color) !important;
    }}
    
    form[aria-label="chat_input_form"] div[data-testid="stTextInput"] input:focus {{
        border: none !important;
        box-shadow: none !important;
    }}

    /* Submit button */
    form[aria-label="chat_input_form"] div[data-testid="stFormSubmitButton"] button {{
        background: var(--btn-bg) !important;
        border: none !important;
        color: var(--text-color) !important;
        font-size: 22px !important;
        width: 44px !important;
        height: 44px !important;
        border-radius: 50% !important;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 !important;
        margin: 0 !important;
    }}
    
    form[aria-label="chat_input_form"] div[data-testid="stFormSubmitButton"] button:hover {{
        background: var(--btn-hover) !important;
        color: var(--text-color) !important;
    }}

    /* Feedback Expander Sticky */
    .main div[data-testid="stExpander"]:last-of-type {{
        position: sticky !important;
        bottom: 0 !important;
        background: var(--bg-color) !important;
        z-index: 1000 !important;
        border-top: 1px solid var(--border-color);
        border-radius: 0;
        margin-bottom: 0;
    }}

    .stat-card {{
        background: var(--stat-bg);
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
        border-left: 4px solid var(--stat-border);
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}

    .stat-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(72, 187, 120, 0.2);
    }}

    .stat-value {{
        font-size: 40px;
        font-weight: bold;
        color: var(--stat-value);
    }}

    .stat-label {{
        font-size: 16px;
        color: var(--stat-label);
        text-transform: uppercase;
        font-weight: 600;
    }}

    .habit-badge {{
        display: inline-block;
        background: var(--badge-bg);
        color: var(--badge-text);
        padding: 8px 14px;
        border-radius: 20px;
        font-size: 16px;
        margin: 6px 4px;
        font-weight: 600;
        transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
        cursor: default;
    }}

    .habit-badge:hover {{
        transform: scale(1.05);
        box-shadow: 0 4px 10px rgba(240, 147, 251, 0.4);
        opacity: 0.9;
    }}

    .goal-item {{
        background: var(--item-bg);
        padding: 14px;
        border-radius: 10px;
        margin-bottom: 12px;
        color: var(--sidebar-text);
        border-left: 4px solid var(--goal-border);
        font-size: 18px;
        font-weight: 500;
        transition: transform 0.2s ease, background 0.2s ease;
        cursor: default;
    }}

    .goal-item:hover {{
        transform: translateX(4px);
        background: var(--item-hover);
    }}

    .task-item {{
        background: var(--item-bg);
        padding: 14px;
        border-radius: 10px;
        margin-bottom: 12px;
        color: var(--sidebar-text);
        border-left: 4px solid var(--task-border);
        font-size: 18px;
        font-weight: 500;
        transition: transform 0.2s ease, background 0.2s ease;
        cursor: default;
    }}

    .task-item:hover {{
        transform: translateX(4px);
        background: var(--item-hover);
    }}
    
    .sidebar-h2 {{
        color: var(--sidebar-text);
        text-align: center;
        font-size: 32px;
        margin-bottom: 0px;
        font-weight: 700;
    }}
    
    .sidebar-p {{
        color: var(--sidebar-subtext);
        text-align: center;
        font-size: 18px;
        margin-top: 5px;
    }}
    
    .focus-status-box {{
        background: var(--status-bg);
        padding: 16px;
        border-radius: 10px;
        color: var(--sidebar-text);
        text-align: center;
        margin-bottom: 12px;
        font-size: 18px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}

    .feedback-box {{
        background: var(--feedback-bg);
        border: 2px solid var(--feedback-border);
        border-radius: 16px;
        padding: 20px;
        margin-top: 24px;
    }}

    .feedback-title {{
        font-size: 24px;
        font-weight: bold;
        color: var(--feedback-text);
        margin-bottom: 12px;
    }}

    .feedback-description {{
        font-size: 18px;
        color: var(--feedback-text);
        margin-bottom: 16px;
        line-height: 1.5;
    }}

    div[data-testid="stTextArea"] textarea {{
        font-size: 18px !important;
        border-radius: 12px !important;
        border: 2px solid var(--feedback-border) !important;
        background: var(--input-bg) !important;
        color: var(--text-color) !important;
        padding: 12px 16px !important;
        min-height: 100px !important;
    }}

    /* Additional Streamlit overrides */
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {{
        background-color: var(--input-bg) !important;
        border-color: var(--border-color) !important;
        color: var(--text-color) !important;
    }}
    .stSelectbox div[data-baseweb="select"] * {{
        color: var(--text-color) !important;
    }}
    
    button[kind="secondary"] {{
        background-color: var(--btn-bg) !important;
        color: var(--text-color) !important;
        border-color: var(--border-color) !important;
    }}
    button[kind="secondary"]:hover {{
        background-color: var(--btn-hover) !important;
    }}

    /* Responsive Adjustments for Mobile */
    @media (max-width: 768px) {{
        .chat-messages {{ height: 60vh; }}
        .user-message-bubble, .bot-message-bubble, .thinking-bubble {{
            font-size: 16px;
            padding: 12px 16px;
            max-width: 90%;
        }}
        .header-title {{ font-size: 24px; }}
        .header-subtitle {{ font-size: 16px; }}
        form[aria-label="chat_input_form"] div[data-testid="stTextInput"] input {{
            font-size: 16px !important;
            padding: 10px 15px !important;
        }}
        form[aria-label="chat_input_form"] div[data-testid="stFormSubmitButton"] button {{
            width: 40px !important;
            height: 40px !important;
            font-size: 20px !important;
        }}
    }}
    </style>
    """,unsafe_allow_html=True)


# -------- STATE --------
if "messages" not in st.session_state:
    st.session_state.messages = []

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

if "progress" not in st.session_state:
    st.session_state.progress = [{"Time": datetime.now().strftime("%H:%M"), "Points": st.session_state.points}]

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

if "update_email_flow" not in st.session_state:
    st.session_state.update_email_flow = None
if "pending_new_email" not in st.session_state:
    st.session_state.pending_new_email = None

# State for multi-step auth flows (OTP verification)
if "auth_flow" not in st.session_state:
    st.session_state.auth_flow = None
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if "otp_sent_time" not in st.session_state:
    st.session_state.otp_sent_time = 0.0

# Settings state
if "show_settings" not in st.session_state:
    st.session_state.show_settings = False

if "user_settings" not in st.session_state:
    st.session_state.user_settings = {}

if "logout_requested" not in st.session_state:
    st.session_state.logout_requested = False

# -------- INITIALIZE COOKIE MANAGER --------
initialize_cookie_manager()

# -------- RESTORE SESSION FROM PERSISTENT STORAGE --------
if st.session_state.logout_requested:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_settings = {}
    st.session_state.contact_linked = False
    st.session_state.contact_info = None
    try:
        if cookie_manager:
            cookie_manager.delete("remembered_username")
    except (KeyError, Exception) as e:
        logging.debug(f"Cookie deletion error: {e}")
    st.session_state.logout_requested = False
    remembered_user = None
elif not st.session_state.authenticated:
    try:
        remembered_user = cookie_manager.get(cookie="remembered_username") if cookie_manager else None
    except Exception as e:
        logging.debug(f"Cookie retrieval error: {e}")
        remembered_user = None
    
    if remembered_user:
        user = get_user_by_username(remembered_user)
        if user:
            st.session_state.authenticated = True
            st.session_state.username = remembered_user
            st.session_state.remember_me = True
            st.session_state.contact_linked = True
            st.session_state.contact_info = user.get('contact_info')
            # Initialize settings manager for this user
            settings_manager_instance = SettingsManager(remembered_user)
            st.session_state.user_settings = settings_manager_instance.load_settings()
            st.rerun()
        else:
            try:
                if cookie_manager:
                    cookie_manager.delete("remembered_username")
            except (KeyError, Exception) as e:
                logging.debug(f"Cookie deletion error: {e}")

# Ensure settings manager is initialized for the active session
if st.session_state.get("username") and settings_manager_instance is None:
    settings_manager_instance = SettingsManager(st.session_state.username)
    if not st.session_state.user_settings:
        st.session_state.user_settings = settings_manager_instance.load_settings()

# Apply Custom Theme Dynamically
apply_theme()

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>ADHD AI Coach Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        login_tab, register_tab = st.tabs(["Login", "Register"])

        with login_tab:
            with st.form("login_form"):
                log_user = st.text_input("Username", autocomplete="username")
                log_pass = st.text_input("Password", type="password", autocomplete="current-password")
                remember_me = st.checkbox("Remember me")
                if st.form_submit_button("Login", use_container_width=True):
                    log_user = log_user.strip()
                    if verify_user(log_user, log_pass):
                        st.session_state.authenticated = True
                        st.session_state.username = log_user
                        st.session_state.remember_me = remember_me
                        st.session_state.contact_linked = True
                        st.session_state.contact_info = None

                        if remember_me:
                            try:
                                if cookie_manager:
                                    cookie_manager.set("remembered_username", log_user, expires_at=datetime.now() + timedelta(days=30))
                            except Exception as e:
                                logging.debug(f"Cookie set error: {e}")

                        settings_manager_instance = SettingsManager(log_user)
                        st.session_state.user_settings = settings_manager_instance.load_settings()
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

        with register_tab:
            with st.form("register_form"):
                reg_user = st.text_input("New Username", autocomplete="username")
                reg_pass = st.text_input("New Password", type="password", autocomplete="new-password")
                if st.form_submit_button("Register", use_container_width=True):
                    reg_user = reg_user.strip()
                    if not reg_user or not reg_pass:
                        st.error("Please provide username and password.")
                    elif len(reg_pass) < 6:
                        st.error("Password must be at least 6 characters long.")
                    elif get_user_by_username(reg_user):
                        st.error("This username is already taken. Please choose another one.")
                    else:
                        success, error_msg = create_user(reg_user, reg_pass)
                        if success:
                            st.success("Registration successful! You can now log in.")
                            time.sleep(0.6)
                            st.rerun()
                        else:
                            st.error(f"Database error occurred: {error_msg}")
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
    st.markdown('<div class="sidebar-h2">🧠 ADHD Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-p">Your productivity companion</div>', unsafe_allow_html=True)
    
    # Logout button
    if st.button("Logout", use_container_width=True):
        st.session_state.logout_requested = True
        st.rerun()

    @st_fragment
    def render_daily_checkin():
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
    render_daily_checkin()
    
    @st_fragment(run_every=1)
    def render_focus_timer():
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
                st.session_state.progress.append({"Time": datetime.now().strftime("%H:%M"), "Points": st.session_state.points})
                if st.session_state.tasks:
                    st.session_state.tasks.pop(0)
                
                st.toast(f"Focus session completed! Earned {points_earned} Points.", icon="🎯")
                st.rerun()
        mins = remaining // 60
        secs = remaining % 60
        st.markdown(f'<div class="focus-status-box"><b>{status_text}</b><br>Remaining: <b>{mins:02d}:{secs:02d}</b></div>', unsafe_allow_html=True)
        
        # Focus Controls
        col1, col2 = st.columns(2)
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
    render_focus_timer()
    
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
        <div class="stat-label" style="color: var(--sidebar-text); opacity: 0.8;">AI Detected Stress</div>
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
        
    # Progress Chart
    if st.session_state.progress and len(st.session_state.progress) > 1:
        st.markdown('### 📈 Progress (Points)')
        df = pd.DataFrame(st.session_state.progress).set_index("Time")
        st.line_chart(df, use_container_width=True)
        st.divider()
    
    # Reflection
    st.markdown('### 📝 Daily Reflection')
    reflection_input = st.text_area("Share your thoughts...", value=st.session_state.reflection, key="reflection_sidebar", height=80, label_visibility="collapsed")
    if reflection_input != st.session_state.reflection:
        st.session_state.reflection = reflection_input

    st.divider()
    
    # Export Data
    with st.expander("📥 Export Data"):
        st.markdown("Download a copy of your current chat history.")
        if not st.session_state.messages:
            st.info("No chat history to export yet.")
        else:
            pdf_bytes = generate_chat_pdf(st.session_state.messages)
            if pdf_bytes:
                st.download_button(
                    label="📄 Download Chat as PDF",
                    data=pdf_bytes,
                    file_name=f"ADHD_Coach_Chat_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            # Reliable text backup
            txt_content = "ADHD AI Coach - Chat History\n" + "="*30 + "\n\n"
            for msg in st.session_state.messages:
                role = "You" if msg["role"] == "user" else "AI Coach"
                txt_content += f"{role}:\n{msg.get('content', '')}\n\n"
                
            st.download_button(
                label="📝 Download Chat as Text",
                data=txt_content,
                file_name=f"ADHD_Coach_Chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )


# -------- SETTINGS MODAL RENDERER --------
@st_fragment
def render_settings_modal():
    """Render settings configuration panel"""
    st.markdown("<h2>⚙️ User Settings</h2>", unsafe_allow_html=True)
    
    settings = st.session_state.user_settings
    settings_tabs = st.tabs(["Account", "Personalization", "Appearance", "General"])
    
    with settings_tabs[0]:
        st.markdown(f"**Current Email:** `{st.session_state.contact_info}`")
        
        if st.session_state.update_email_flow == 'otp':
            with st.form("update_email_otp_form"):
                if not os.getenv("SMTP_SERVER"):
                    user_db = get_user_by_username(st.session_state.username)
                    if user_db and user_db.get('otp_code'):
                        st.info(f"🛠️ **Demo Mode:** Your OTP is `{user_db['otp_code']}`")
                st.markdown(f"Verify new email: **{st.session_state.pending_new_email}**")
                otp_code = st.text_input("Enter 6-digit OTP")
                if st.form_submit_button("Verify & Update", use_container_width=True):
                    user = get_user_by_username(st.session_state.username)
                    exp_time = pd.to_datetime(user['otp_expires_at']).tz_localize(None) if user and user.get('otp_expires_at') else datetime.min
                    if user and str(user['otp_code']) == str(otp_code) and exp_time > datetime.now():
                        update_user_contact(st.session_state.username, st.session_state.pending_new_email)
                        activate_user(st.session_state.username)
                        st.session_state.contact_info = st.session_state.pending_new_email
                        st.session_state.update_email_flow = None
                        st.session_state.pending_new_email = None
                        st.success("Email updated successfully!")
                        time.sleep(0.4)
                        st.rerun()
                    else:
                        st.error("Invalid or expired OTP.")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Resend OTP", key="resend_update_email_otp", use_container_width=True):
                    if time.time() - st.session_state.otp_sent_time < 30:
                        st.warning(f"Please wait {int(30 - (time.time() - st.session_state.otp_sent_time))}s.")
                    else:
                        new_otp = generate_otp()
                        set_user_otp(st.session_state.username, new_otp, datetime.now() + timedelta(minutes=10))
                        if send_otp_email(st.session_state.pending_new_email, new_otp):
                            st.session_state.otp_sent_time = time.time()
                            st.success("OTP resent!")
                            time.sleep(0.4)
                            st.rerun()
                        else:
                            st.error("Failed to resend.")
            with col_b:
                if st.button("← Cancel", use_container_width=True):
                    st.session_state.update_email_flow = None
                    st.session_state.pending_new_email = None
                    st.rerun()
        else:
            with st.form("update_email_form"):
                new_email = st.text_input("New Email Address")
                if st.form_submit_button("Change Email", use_container_width=True):
                    if re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                        if new_email == st.session_state.contact_info:
                            st.warning("This is already your current email.")
                        else:
                            otp = generate_otp()
                            expires_at = datetime.now() + timedelta(minutes=10)
                            set_user_otp(st.session_state.username, otp, expires_at)
                            if send_otp_email(new_email, otp):
                                st.session_state.otp_sent_time = time.time()
                                st.session_state.update_email_flow = 'otp'
                                st.session_state.pending_new_email = new_email
                                st.success("OTP sent! Check your new email.")
                                time.sleep(0.4)
                                st.rerun()
                            else:
                                st.error("Failed to send email. Check SMTP settings.")
                    else:
                        st.error("Please enter a valid email address.")
        
        st.divider()
        st.markdown("**Change Password**")
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Update Password", use_container_width=True):
                if not current_password or not new_password or not confirm_password:
                    st.error("Please fill in all fields.")
                elif new_password != confirm_password:
                    st.error("New passwords do not match.")
                elif not verify_user(st.session_state.username, current_password):
                    st.error("Incorrect current password.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long.")
                else:
                    if reset_password(st.session_state.username, st.session_state.contact_info, new_password):
                        st.success("Password updated successfully!")
                        time.sleep(0.4)
                        st.rerun()
                    else:
                        st.error("An unexpected error occurred.")
                        
    with settings_tabs[1]:
        st.markdown("**Personalization Options**")
        st.selectbox("AI Coach Tone", ["Empathetic & Gentle", "Direct & Firm", "Energetic & Motivating"], index=0)
        st.selectbox("Primary Focus Area", ["Time Management", "Task Initiation", "Emotional Regulation", "Organization"], index=0)
        if st.button("Save Preferences", key="save_pers", use_container_width=True):
            st.success("Preferences saved successfully!")
            
    with settings_tabs[2]:
        st.markdown("**Appearance Settings**")
        
        time_format = st.selectbox(
            "Time Format",
            options=["24-hour", "12-hour"],
            index=0 if not settings.get("use_12h_format") else 1,
            key="time_select"
        )
        if st.button("Apply Appearance", key="save_app", use_container_width=True):
            st.success("Appearance settings applied!")
            
    with settings_tabs[3]:
        st.markdown("**General Settings**")
        
        notif_freq = st.selectbox(
            "Notification Frequency",
            options=["hourly", "daily", "weekly"],
            index=["hourly", "daily", "weekly"].index(settings.get("notification_frequency", "daily")),
            key="notif_freq_select"
        )
        
        timer_duration = st.slider(
            "Pomodoro Timer Duration (minutes)",
            min_value=5,
            max_value=60,
            value=settings.get("timer_duration", 25),
            step=5,
            key="timer_slider_settings"
        )
        
        language = st.selectbox(
            "Language",
            options=["en", "es", "fr", "de"],
            index=["en", "es", "fr", "de"].index(settings.get("language", "en")),
            key="lang_select"
        )
        
        st.divider()
        if st.button("Logout from all devices", use_container_width=True):
            st.session_state.logout_requested = True
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Delete Account", type="primary", use_container_width=True):
            st.error("Account deletion requested. Please contact support.")
            
    st.divider()
    # Save Settings
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Changes", use_container_width=True, key="save_settings"):
            new_settings = {
                "theme": settings.get("theme", "dark"),
                "language": language,
                "notifications_enabled": settings.get("notifications_enabled", True),
                "notification_frequency": notif_freq,
                "timer_duration": timer_duration,
                "auto_check_in": settings.get("auto_check_in", True),
                "sound_enabled": settings.get("sound_enabled", True),
                "use_12h_format": time_format == "12-hour"
            }
            
            # Save to disk
            if settings_manager_instance:
                settings_manager_instance.save_settings(new_settings)
                st.session_state.user_settings = new_settings
                
                # Apply timer duration immediately
                st.session_state.timer_duration = timer_duration * 60
                st.session_state.timer_seconds = timer_duration * 60
                
                st.success("✅ Settings saved successfully!")
                st.session_state.show_settings = False
                time.sleep(0.4)
                st.rerun()
            else:
                st.error("Error: Settings manager not initialized")
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True, key="cancel_settings"):
            st.session_state.show_settings = False
            st.rerun()


# -------- MAIN GPT-STYLE CHAT INTERFACE --------
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown("""
    <div class="header-container" style="border-bottom: none; padding-bottom: 0;">
        <div class="header-title">💬 ADHD AI Coach</div>
        <div class="header-subtitle">Your AI-powered ADHD productivity assistant</div>
    </div>
    """, unsafe_allow_html=True)

with header_col2:
    if st.session_state.username:
        initial, bg_color = get_cached_avatar_info(st.session_state.username)
        
        st.html(f"""
        <div id="avatar-anchor" style="display:none;"></div>
        <style>
        /* Position the container instead of the button so the tooltip follows */
        div[data-testid="stElementContainer"]:has(#avatar-anchor) + div[data-testid="stElementContainer"],
        div.element-container:has(#avatar-anchor) + div.element-container {{
            position: fixed !important;
            right: 25px !important;
            top: 65px !important;
            z-index: 99999 !important;
            width: 56px !important;
            height: 56px !important;
        }}
        
        /* Style the button */
        div[data-testid="stElementContainer"]:has(#avatar-anchor) + div[data-testid="stElementContainer"] button,
        div.element-container:has(#avatar-anchor) + div.element-container button {{
            background-color: {bg_color} !important;
            color: white !important;
            border-radius: 50% !important;
            width: 56px !important;
            height: 56px !important;
            min-width: 56px !important;
            min-height: 56px !important;
            border: 2px solid rgba(255, 255, 255, 0.1) !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5) !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.2s ease !important;
            margin: 0 !important;
        }}
        div[data-testid="stElementContainer"]:has(#avatar-anchor) + div[data-testid="stElementContainer"] button p,
        div.element-container:has(#avatar-anchor) + div.element-container button p {{
            font-size: 24px !important;
            font-weight: bold !important;
            color: white !important;
            margin: 0 !important;
            line-height: 1 !important;
        }}
        div[data-testid="stElementContainer"]:has(#avatar-anchor) + div[data-testid="stElementContainer"] button:hover,
        div.element-container:has(#avatar-anchor) + div.element-container button:hover {{
            opacity: 0.85 !important;
            border-color: rgba(255, 255, 255, 0.4) !important;
            box-shadow: 0 6px 14px rgba(0,0,0,0.7) !important;
        }}
        </style>
            """)

st.markdown("<div style='border-bottom: 1px solid var(--border-color); margin-bottom: 20px;'></div>", unsafe_allow_html=True)



# Chat interface - make it expandable
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

chat_placeholder = st.empty()

LANGUAGES = {
    "English": "en", "Spanish": "es", "French": "fr", "German": "de", 
    "Hindi": "hi", "Chinese (Simplified)": "zh-CN", "Arabic": "ar", 
    "Portuguese": "pt", "Russian": "ru", "Japanese": "ja"
}

# Inline Chat Input Form - stays above feedback
with st.form("chat_input_form", clear_on_submit=True):
    cols = st.columns([10, 1])
    with cols[0]:
        user_input = st.text_input("Message", placeholder="Ask your ADHD Coach...", label_visibility="collapsed", autocomplete="off")
    with cols[1]:
        submit_btn = st.form_submit_button("↑", use_container_width=True)

with st.expander("🎙️ Voice Assistant (Multilingual)"):
    voice_lang_name = st.selectbox("Select your spoken language", options=list(LANGUAGES.keys()), index=0)
    audio_bytes = st.audio_input("Record your message")

if submit_btn and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input, "is_voice": False})
    # Do not call st.rerun() here so the UI updates immediately!

if audio_bytes and st.session_state.get("last_audio") != audio_bytes:
    st.session_state.last_audio = audio_bytes
    with st.spinner("Transcribing and translating audio..."):
        try:
            import speech_recognition as sr
            from deep_translator import GoogleTranslator
            r = sr.Recognizer()
            with sr.AudioFile(audio_bytes) as source:
                audio_data = r.record(source)
            
            voice_lang_code = LANGUAGES[voice_lang_name]
            native_text = r.recognize_google(audio_data, language=voice_lang_code)
            
            if voice_lang_code != "en":
                english_text = GoogleTranslator(source=voice_lang_code, target='en').translate(native_text)
                display_text = f"🗣️ {native_text}\n\n*(Translated to English): {english_text}*"
            else:
                english_text = native_text
                display_text = f"🗣️ {native_text}"
                
            st.session_state.messages.append({
                "role": "user", "content": english_text, "display": display_text, "is_voice": True, "lang": voice_lang_code
            })
        except sr.UnknownValueError:
            st.error("Could not understand the audio. Please try speaking clearly again.")
        except Exception as e:
            st.error(f"Audio Error: {e}")

is_thinking = st.session_state.messages and st.session_state.messages[-1]["role"] == "user"

if not st.session_state.messages:
    chat_placeholder.markdown('<div style="height: 30vh;"></div><div style="text-align:center; color:#aaaaaa; font-size:20px;">Start a conversation below!</div><div style="height: 10vh;"></div>', unsafe_allow_html=True)
else:
    chat_parts = ['<div class="chat-messages">']
    if is_thinking:
        chat_parts.append('<div class="thinking"><div class="thinking-bubble">⏳ Thinking...</div></div>')

    for msg in reversed(st.session_state.messages):
        content_to_render = msg.get("display", msg["content"])
        if msg["role"] == "user":
            chat_parts.append(f'<div class="user-message"><div class="user-message-bubble">{render_chat_text(content_to_render)}</div></div>')
        else:
            chat_parts.append(f'<div class="bot-message"><div class="bot-message-bubble">{render_chat_text(content_to_render)}</div></div>')
    chat_parts.append('</div>')
    chat_placeholder.markdown("".join(chat_parts), unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Play audio if the latest message was from the assistant and contains voice data
if not is_thinking and st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant" and st.session_state.messages[-1].get("audio"):
    st.audio(st.session_state.messages[-1]["audio"], format="audio/mp3", autoplay=True)

# Process the backend call if we are thinking
if is_thinking:
    with st.status("🧠 Analyzing your message...", expanded=True) as status:
        try:
            status.write("Extracting context and history...")
            user_input_text = st.session_state.messages[-1]["content"]
            
            # Clean history to only include essential fields to prevent serialization issues
            history = []
            for msg in st.session_state.messages[:-1]:
                try:
                    clean_msg = {
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    }
                    history.append(clean_msg)
                except Exception as e:
                    logging.debug(f"Error cleaning history message: {e}")
            
            # Ensure user_data has default values
            user_data = st.session_state.user_data or {}
            
            try:
                request_data = ChatRequest(
                    text=user_input_text,
                    history=history,
                    user_data=user_data
                )
            except Exception as validation_error:
                logging.error(f"ChatRequest validation error: {validation_error}")
                st.error(f"Message format error: {str(validation_error)[:100]}")
                st.rerun()
            
            status.write("Evaluating productivity and stress levels...")
            try:
                # Call the API function directly instead of making an HTTP request
                data = chat(request_data)
            except Exception as chat_error:
                logging.error(f"Chat API error: {chat_error}")
                st.error(f"AI processing error: {str(chat_error)[:100]}")
                st.session_state.messages[-1]["role"] = "user"  # Restore user message role
                st.rerun()
            
            status.write("Generating personalized coaching response...")
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
                        
            # Check if voice translation & TTS is needed
            last_msg = st.session_state.messages[-1]
            audio_data = None
            display_reply = reply
            
            if last_msg.get("is_voice"):
                status.write("Translating response and generating audio...")
                target_lang = last_msg.get("lang", "en")
                from deep_translator import GoogleTranslator
                if target_lang != "en":
                    translated_reply = GoogleTranslator(source='en', target=target_lang).translate(reply)
                    display_reply = f"{translated_reply}\n\n*(English): {reply}*"
                    tts_text = translated_reply
                else:
                    tts_text = reply
                    
                # Generate Audio
                try:
                    from gtts import gTTS
                    tts = gTTS(text=tts_text, lang=target_lang)
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0)
                    audio_data = fp.read()
                except Exception as e:
                    logging.error(f"TTS Error: {e}")
            
            status.update(label="✅ Response ready!", state="complete", expanded=False)
        except Exception as e:
            status.update(label="❌ Error generating response", state="error", expanded=False)
            reply = f"❌ Error: {str(e)}"
            display_reply = reply
            audio_data = None

    st.session_state.messages.append({"role": "assistant", "content": reply, "display": display_reply, "audio": audio_data})
    st.session_state.session_count += 1
    
    # Update gamification
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    if st.session_state.last_session_date == yesterday.isoformat():
        st.session_state.current_streak += 1
    elif st.session_state.last_session_date != today.isoformat():
        st.session_state.current_streak = 1
    
    if st.session_state.current_streak > st.session_state.longest_streak:
        st.session_state.longest_streak = st.session_state.current_streak
    st.session_state.last_session_date = today.isoformat()
    st.session_state.points += 5
    st.session_state.progress.append({"Time": datetime.now().strftime("%H:%M"), "Points": st.session_state.points})
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
@st_fragment
def render_feedback_section():
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
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
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
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.warning("Please enter some feedback before submitting.")
render_feedback_section()

# Display feedback summary
if st.session_state.feedback_list:
    with st.expander(f"📋 Feedback History ({len(st.session_state.feedback_list)})"):
        for i, feedback in enumerate(reversed(st.session_state.feedback_list), 1):
            st.markdown(f"""
            **#{i} - {feedback['timestamp']} | {feedback['rating']}**
            
            {feedback['text']}
            """)
