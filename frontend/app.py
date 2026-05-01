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

st.set_page_config(page_title="ADHD AI Coach", layout="wide", initial_sidebar_state="expanded")

# Configure logging to output to console (stdout) for cloud platforms like Render.
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s')

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
import speech_recognition as sr
from deep_translator import GoogleTranslator
from gtts import gTTS
import io

# Initialize session and settings managers
session_manager = SessionManager()
settings_manager_instance = None  # Will be initialized after authentication
 
def generate_otp(length=6):
    """Generate a random numeric OTP."""
    return "".join(random.choices(string.digits, k=length))
 
def render_chat_text(text):
    return html.escape(str(text)).replace("\n", "<br>")

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
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(72, 187, 120, 0.2);
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
    transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
    cursor: default;
}

.habit-badge:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 10px rgba(240, 147, 251, 0.4);
    opacity: 0.9;
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
    transition: transform 0.2s ease, background 0.2s ease;
    cursor: default;
}

.goal-item:hover {
    transform: translateX(4px);
    background: #374151;
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
    transition: transform 0.2s ease, background 0.2s ease;
    cursor: default;
}

.task-item:hover {
    transform: translateX(4px);
    background: #374151;
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

if "update_email_flow" not in st.session_state:
    st.session_state.update_email_flow = None
if "pending_new_email" not in st.session_state:
    st.session_state.pending_new_email = None

# State for multi-step auth flows (OTP verification)
if "auth_flow" not in st.session_state:
    st.session_state.auth_flow = None # e.g., 'register_otp', 'forgot_password_otp'
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if "otp_sent_time" not in st.session_state:
    st.session_state.otp_sent_time = 0.0

# Settings state
if "show_settings" not in st.session_state:
    st.session_state.show_settings = False

if "user_settings" not in st.session_state:
    st.session_state.user_settings = {}

# -------- RESTORE SESSION FROM PERSISTENT STORAGE --------
# WARNING: Using local file storage for sessions on cloud platforms (like Render) 
# shares the session across all users! Disabled to ensure proper login functionality.
# if "authenticated" in st.session_state and not st.session_state.authenticated:
#     # Only check for persisted session if not already authenticated
#     persisted_session = session_manager.load_session()
#     if persisted_session:
#         user = get_user_by_username(persisted_session["username"])
#         if user:
#             st.session_state.authenticated = True
#             st.session_state.username = persisted_session["username"]
#             st.session_state.remember_me = True
#             st.session_state.contact_linked = bool(user.get('is_verified', False))
#             st.session_state.contact_info = user.get('contact_info')
#             # Initialize settings manager for this user
#             settings_manager_instance = SettingsManager(persisted_session["username"])
#             st.session_state.user_settings = settings_manager_instance.load_settings()
#         else:
#             session_manager.clear_session()

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>🧠 ADHD AI Coach Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.auth_flow == 'register_otp':
            st.subheader(f"Verify account for: {st.session_state.auth_user}")
            if not os.getenv("SMTP_SERVER"):
                user_db = get_user_by_username(st.session_state.auth_user)
                if user_db and user_db.get('otp_code'):
                    st.info(f"🛠️ **Demo Mode (No SMTP Setup):** Your OTP is `{user_db['otp_code']}`")
            with st.form("otp_verify_form"):
                otp_code = st.text_input("Enter the 6-digit OTP sent to your email", autocomplete="one-time-code")
                submitted = st.form_submit_button("Verify Account")
                if submitted:
                    user = get_user_by_username(st.session_state.auth_user)
                    exp_time = pd.to_datetime(user['otp_expires_at']).tz_localize(None) if user and user.get('otp_expires_at') else datetime.min
                    if user and str(user['otp_code']) == str(otp_code) and exp_time > datetime.now():
                        activate_user(st.session_state.auth_user)
                        
                        st.session_state.username = st.session_state.auth_user
                        st.session_state.contact_linked = True
                        st.session_state.contact_info = user.get('contact_info')
                        st.session_state.user_settings = SettingsManager(st.session_state.auth_user).load_settings()
                        
                        st.success("Account verified successfully! Logging you in...")
                        st.session_state.auth_flow = None
                        st.session_state.auth_user = None
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Invalid or expired OTP. Please try again.")
            
            # Add a button to escape the OTP screen
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Resend OTP", key="resend_reg_otp", use_container_width=True):
                    if time.time() - st.session_state.otp_sent_time < 30:
                        st.warning(f"Please wait {int(30 - (time.time() - st.session_state.otp_sent_time))}s.")
                    else:
                        user = get_user_by_username(st.session_state.auth_user)
                        if user:
                            new_otp = generate_otp()
                            set_user_otp(st.session_state.auth_user, new_otp, datetime.now() + timedelta(minutes=10))
                            if send_otp_email(user['contact_info'], new_otp):
                                st.session_state.otp_sent_time = time.time()
                                st.success("OTP resent!")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error("Failed to resend.")
            with col_b:
                if st.button("← Cancel & Start Over", key="cancel_reg_otp", use_container_width=True):
                    st.session_state.auth_flow = None
                    st.session_state.auth_user = None
                    st.rerun()
        
        elif st.session_state.auth_flow == 'forgot_password_otp':
            st.subheader(f"Reset password for: {st.session_state.auth_user}")
            if not os.getenv("SMTP_SERVER"):
                user_db = get_user_by_username(st.session_state.auth_user)
                if user_db and user_db.get('otp_code'):
                    st.info(f"🛠️ **Demo Mode (No SMTP Setup):** Your OTP is `{user_db['otp_code']}`")
            with st.form("reset_otp_form"):
                otp_code = st.text_input("Enter the 6-digit OTP from your email", autocomplete="one-time-code")
                new_pass = st.text_input("Enter New Password", type="password", autocomplete="new-password")
                if st.form_submit_button("Set New Password"):
                    user = get_user_by_username(st.session_state.auth_user)
                    exp_time = pd.to_datetime(user['otp_expires_at']).tz_localize(None) if user and user.get('otp_expires_at') else datetime.min
                    if user and str(user['otp_code']) == str(otp_code) and exp_time > datetime.now():
                        if len(new_pass) < 6:
                            st.error("Password must be at least 6 characters long.")
                        else:
                            # Use the original contact info for security
                            if reset_password(user['username'], user['contact_info'], new_pass):
                                
                                st.session_state.authenticated = True
                                st.session_state.contact_linked = True
                                st.session_state.contact_info = user.get('contact_info')
                                st.session_state.user_settings = SettingsManager(st.session_state.auth_user).load_settings()
                                
                                st.success("Password reset successfully! Logging you in...")
                                st.session_state.auth_flow = None
                                st.session_state.auth_user = None
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("An unexpected error occurred during password reset.")
                    else:
                        st.error("Invalid or expired OTP.")
            
            # Add a button to escape the OTP screen
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Resend OTP", key="resend_forgot_otp", use_container_width=True):
                    if time.time() - st.session_state.otp_sent_time < 30:
                        st.warning(f"Please wait {int(30 - (time.time() - st.session_state.otp_sent_time))}s.")
                    else:
                        user = get_user_by_username(st.session_state.auth_user)
                        if user:
                            new_otp = generate_otp()
                            set_user_otp(st.session_state.auth_user, new_otp, datetime.now() + timedelta(minutes=10))
                            if send_otp_email(user['contact_info'], new_otp):
                                st.session_state.otp_sent_time = time.time()
                                st.success("OTP resent!")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error("Failed to resend.")
            with col_b:
                if st.button("← Cancel & Start Over", key="cancel_forgot_otp", use_container_width=True):
                    st.session_state.auth_flow = None
                    st.session_state.auth_user = None
                    st.rerun()
                
        else:
            login_tab, register_tab, forgot_tab = st.tabs(["Login", "Register", "Forgot Password"])
            with login_tab:
                with st.form("login_form"):
                    log_user = st.text_input("Username or Email", autocomplete="username")
                    log_pass = st.text_input("Password", type="password", autocomplete="current-password")
                    remember_me = st.checkbox("Remember me")
                    if st.form_submit_button("Login", use_container_width=True):
                        log_user = log_user.strip()
                        if verify_user(log_user, log_pass):
                            user = get_user_by_username(log_user)
                            if user:
                                log_user = user['username'] # Reassign to username if email was used
                                has_valid_email = bool(user['contact_info'] and re.match(r"[^@]+@[^@]+\.[^@]+", user['contact_info']))
                                if not user['is_verified']:
                                    if not has_valid_email:
                                        # Legacy user without a valid email: Login but force them to link one
                                        st.session_state.authenticated = True
                                        st.session_state.username = log_user
                                        st.session_state.remember_me = remember_me
                                        st.session_state.contact_linked = False
                                        # Save session persistently
                                        # session_manager.save_session(log_user)
                                        # Initialize settings manager for this user
                                        settings_manager_instance = SettingsManager(log_user)
                                        st.session_state.user_settings = settings_manager_instance.load_settings()
                                        st.rerun()
                                    else:
                                        # New user who abandoned registration: Send fresh OTP
                                        otp = generate_otp()
                                        expires_at = datetime.now() + timedelta(minutes=10)
                                        set_user_otp(log_user, otp, expires_at)
                                        if send_otp_email(user['contact_info'], otp):
                                            st.session_state.otp_sent_time = time.time()
                                            st.session_state.auth_flow = 'register_otp'
                                            st.session_state.auth_user = log_user
                                            st.warning("Account verification required. An OTP has been sent to your email.")
                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.error("Failed to send verification email. Please check your SMTP settings.")
                                else:
                                    # Standard verified user
                                    st.session_state.authenticated = True
                                    st.session_state.username = log_user
                                    st.session_state.remember_me = remember_me
                                    st.session_state.contact_linked = True
                                    # Save session persistently
                                    # session_manager.save_session(log_user)
                                    # Initialize settings manager for this user
                                    settings_manager_instance = SettingsManager(log_user)
                                    st.session_state.user_settings = settings_manager_instance.load_settings()
                                    st.rerun()
                        else:
                            st.error("Invalid username or password.")
            with register_tab:
                    with st.form("register_form"):
                        reg_user = st.text_input("New Username", autocomplete="username")
                        reg_pass = st.text_input("New Password", type="password", autocomplete="new-password")
                        reg_contact = st.text_input("Email Address (Required for verification)", autocomplete="email")
                        if st.form_submit_button("Register", use_container_width=True):
                            reg_user = reg_user.strip()
                            if reg_user and reg_pass and reg_contact:
                                is_email = re.match(r"[^@]+@[^@]+\.[^@]+", reg_contact)
                                
                                if not is_email:
                                    st.error("Please enter a valid email address.")
                                elif len(reg_pass) < 6:
                                    st.error("Password must be at least 6 characters long.")
                                elif get_user_by_username(reg_user):
                                    st.error("This username is already taken. Please choose another one.")
                                elif get_user_by_username(reg_contact):
                                    st.error("This email is already registered. Please log in or use 'Forgot Password'.")
                                else:
                                    success, error_msg = create_user(reg_user, reg_pass, reg_contact)
                                    if success:
                                        st.success("Registration successful! You can now log in.")
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error(f"Database error occurred: {error_msg}")
                            else:
                                st.error("Please provide username, password, and a valid email.")
            with forgot_tab:
                    with st.form("forgot_form"):
                        for_user = st.text_input("Username", autocomplete="username")
                        if st.form_submit_button("Send Password Reset Email", use_container_width=True):
                            for_user = for_user.strip()
                            if for_user:
                                user = get_user_by_username(for_user)
                                if user and user['contact_info']:
                                    otp = generate_otp()
                                    expires_at = datetime.now() + timedelta(minutes=10)
                                    set_user_otp(for_user, otp, expires_at)
                                    if send_otp_email(user['contact_info'], otp):
                                        st.session_state.otp_sent_time = time.time()
                                        st.session_state.auth_flow = 'forgot_password_otp'
                                        st.session_state.auth_user = for_user
                                        st.success("Password reset email sent! Please check your inbox for an OTP.")
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error("Could not send password reset email. Please contact support or check SMTP configuration.")
                                else:
                                    st.error("Username not found or no contact info linked to this account.")
                            else:
                                st.error("Please enter your username.")
    st.stop()

# -------- MANDATORY CONTACT LINKING FOR EXISTING USERS --------
if st.session_state.authenticated and not st.session_state.get("contact_linked", False):
    st.markdown("<h2 style='text-align: center; margin-top: 50px;'>⚠️ Account Update Required</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #cbd5e1;'>To secure your account and enable real-time features, you must link and verify an email address to continue.</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.auth_flow == 'legacy_link_otp':
            if not os.getenv("SMTP_SERVER"):
                user_db = get_user_by_username(st.session_state.username)
                if user_db and user_db.get('otp_code'):
                    st.info(f"🛠️ **Demo Mode (No SMTP Setup):** Your OTP is `{user_db['otp_code']}`")
            with st.form("legacy_otp_form"):
                otp_code = st.text_input("Enter the 6-digit OTP sent to your email", autocomplete="one-time-code")
                if st.form_submit_button("Verify & Link", use_container_width=True):
                    user = get_user_by_username(st.session_state.username)
                    exp_time = pd.to_datetime(user['otp_expires_at']).tz_localize(None) if user and user.get('otp_expires_at') else datetime.min
                    if user and str(user['otp_code']) == str(otp_code) and exp_time > datetime.now():
                        activate_user(st.session_state.username)
                        st.session_state.contact_linked = True
                        st.session_state.contact_info = user['contact_info']
                        st.session_state.auth_flow = None
                        st.success("Account successfully linked and verified!")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("Invalid or expired OTP. Please try again.")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Resend OTP", key="resend_legacy_otp", use_container_width=True):
                    if time.time() - st.session_state.otp_sent_time < 30:
                        st.warning(f"Please wait {int(30 - (time.time() - st.session_state.otp_sent_time))}s.")
                    else:
                        user = get_user_by_username(st.session_state.username)
                        if user:
                            new_otp = generate_otp()
                            set_user_otp(st.session_state.username, new_otp, datetime.now() + timedelta(minutes=10))
                            if send_otp_email(user['contact_info'], new_otp):
                                st.session_state.otp_sent_time = time.time()
                                st.success("OTP resent!")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error("Failed to resend.")
            with col_b:
                if st.button("← Cancel & Use Different Email", use_container_width=True):
                    st.session_state.auth_flow = None
                    st.rerun()
        else:
            with st.form("link_contact_form"):
                contact_info = st.text_input("Email Address", autocomplete="email")
                if st.form_submit_button("Send Verification Code", use_container_width=True):
                    is_email = re.match(r"[^@]+@[^@]+\.[^@]+", contact_info)
                    if not is_email:
                        st.error("Please enter a valid email address.")
                    else:
                        update_user_contact(st.session_state.username, contact_info)
                        otp = generate_otp()
                        expires_at = datetime.now() + timedelta(minutes=10)
                        set_user_otp(st.session_state.username, otp, expires_at)
                        if send_otp_email(contact_info, otp):
                            st.session_state.otp_sent_time = time.time()
                            st.session_state.auth_flow = 'legacy_link_otp'
                            st.success("Verification code sent! Please check your email.")
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error("Could not send email. Please check your SMTP settings.")
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
    

    
    # Display current status
    if st.session_state.user_settings.get("theme") == "light":
        st.info("💡 Light Theme Active")
    
    # Logout button
    if st.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_settings = {}
        # session_manager.clear_session()
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
                        time.sleep(1.5)
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
                            time.sleep(1.5)
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
                                time.sleep(1.5)
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
                        time.sleep(1.5)
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
        theme = st.selectbox(
            "Theme",
            options=["dark", "light"],
            index=0 if settings.get("theme") == "dark" else 1,
            key="theme_select"
        )
        
        time_format = st.selectbox(
            "Time Format",
            options=["24-hour", "12-hour"],
            index=0 if not settings.get("use_12h_format") else 1,
            key="time_select"
        )
        st.checkbox("Enable UI Animations", value=True)
        if st.button("Apply Appearance", key="save_app", use_container_width=True):
            st.success("Appearance settings applied!")
            
    with settings_tabs[3]:
        st.markdown("**General Settings**")
        
        notif_enabled = st.checkbox(
            "Enable Notifications",
            value=settings.get("notifications_enabled", True),
            key="notif_check"
        )
        
        if notif_enabled:
            notif_freq = st.selectbox(
                "Notification Frequency",
                options=["hourly", "daily", "weekly"],
                index=["hourly", "daily", "weekly"].index(settings.get("notification_frequency", "daily")),
                key="notif_freq_select"
            )
        else:
            notif_freq = settings.get("notification_frequency", "daily")
            
        sound_enabled = st.checkbox(
            "Sound Notifications",
            value=settings.get("sound_enabled", True),
            key="sound_check"
        )
        
        timer_duration = st.slider(
            "Pomodoro Timer Duration (minutes)",
            min_value=5,
            max_value=60,
            value=settings.get("timer_duration", 25),
            step=5,
            key="timer_slider_settings"
        )
        
        auto_checkin = st.checkbox(
            "Enable Auto Check-in",
            value=settings.get("auto_check_in", True),
            key="checkin_check"
        )
        
        language = st.selectbox(
            "Language",
            options=["en", "es", "fr", "de"],
            index=["en", "es", "fr", "de"].index(settings.get("language", "en")),
            key="lang_select"
        )
        
        st.divider()
        st.checkbox("Share anonymous usage data to improve models", value=False)
        if st.button("Logout from all devices", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            # session_manager.clear_session()
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
                "theme": theme,
                "language": language,
                "notifications_enabled": notif_enabled,
                "notification_frequency": notif_freq,
                "timer_duration": timer_duration,
                "auto_check_in": auto_checkin,
                "sound_enabled": sound_enabled,
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
                time.sleep(1.5)
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
        initial = get_avatar_initials(st.session_state.username)
        bg_color = get_avatar_color(st.session_state.username)
        
        st.markdown(f"""
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
            """, unsafe_allow_html=True)
            
        if st.button(initial, key="top_right_avatar_btn", help="Toggle Settings"):
            st.session_state.show_settings = not st.session_state.show_settings
            st.rerun()

st.markdown("<div style='border-bottom: 1px solid #1e1e1e; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# -------- SHOW SETTINGS MODAL IF TRIGGERED --------
if st.session_state.show_settings:
    modal_col1, modal_col2, modal_col3 = st.columns([1, 2, 1])
    with modal_col2:
        with st.container():
            render_settings_modal()
    st.stop()

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
    chat_html = '<div class="chat-messages">'
    if is_thinking:
        chat_html += '<div class="thinking"><div class="thinking-bubble">⏳ Thinking...</div></div>'

    for msg in reversed(st.session_state.messages):
        content_to_render = msg.get("display", msg["content"])
        if msg["role"] == "user":
            chat_html += f'<div class="user-message"><div class="user-message-bubble">{render_chat_text(content_to_render)}</div></div>'
        else:
            chat_html += f'<div class="bot-message"><div class="bot-message-bubble">{render_chat_text(content_to_render)}</div></div>'
    chat_html += '</div>'
    chat_placeholder.markdown(chat_html, unsafe_allow_html=True)

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
            history = st.session_state.messages[:-1]
            
            request_data = ChatRequest(
                text=user_input_text,
                history=history,
                user_data=st.session_state.user_data
            )
            
            status.write("Evaluating productivity and stress levels...")
            # Call the API function directly instead of making an HTTP request
            data = chat(request_data)
            
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
                if target_lang != "en":
                    translated_reply = GoogleTranslator(source='en', target=target_lang).translate(reply)
                    display_reply = f"{translated_reply}\n\n*(English): {reply}*"
                    tts_text = translated_reply
                else:
                    tts_text = reply
                    
                # Generate Audio
                try:
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
