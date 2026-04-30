import streamlit as st
import requests
import pandas as pd
import datetime
import time
import os
import html

st.set_page_config(page_title="ADHD AI Coach", layout="wide")

API_URL = os.getenv("ADHD_API_URL", "http://127.0.0.1:8000/chat")


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
    background: linear-gradient(135deg, #f5f7fa 0%, #f0f4f8 100%);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 16px;
}

.main {
    background: linear-gradient(135deg, #f5f7fa 0%, #f0f4f8 100%);
    padding: 0;
}

/* Header */
.header-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 32px;
    border-radius: 0 0 20px 20px;
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.15);
    margin-bottom: 32px;
    text-align: center;
}

.header-title {
    font-size: 48px;
    font-weight: bold;
    margin-bottom: 12px;
}

.header-subtitle {
    font-size: 20px;
    opacity: 0.95;
    font-weight: 500;
}

/* Main Layout */
.main-container {
    display: grid;
    grid-template-columns: 1fr 1.5fr;
    gap: 32px;
    max-width: 1900px;
    margin: 0 auto;
    padding: 0 32px 32px 32px;
}

/* Left Panel - Dashboard */
.left-panel {
    background: linear-gradient(135deg, #111827 0%, #0f172a 100%);
    color: #e2e7ff;
    border-radius: 20px;
    padding: 32px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    height: fit-content;
    position: sticky;
    top: 20px;
}

.panel-title {
    font-size: 24px;
    font-weight: bold;
    color: #e2e7ff;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 3px solid #667eea;
    padding-bottom: 16px;
}

.panel-subtitle {
    font-size: 18px;
    color: #cbd5e1;
    margin-bottom: 24px;
    line-height: 1.6;
}

.activity-card {
    background: #111827;
    padding: 24px;
    border-radius: 16px;
    margin-bottom: 24px;
    border-left: 5px solid #2563eb;
    color: #e2e7ff;
    font-size: 20px;
    line-height: 1.6;
    font-weight: 500;
}

.activity-btn {
    background: #667eea;
    color: white;
    border: none;
    padding: 12px 20px;
    border-radius: 16px;
    cursor: pointer;
    font-weight: 600;
    font-size: 16px;
    margin-bottom: 12px;
    transition: all 0.3s ease;
}

.activity-btn:hover {
    background: #5a67d8;
    transform: translateY(-2px);
}

.activity-log-item {
    background: #0f172a;
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 12px;
    color: #e2e7ff;
    font-size: 16px;
}

.goal-card {
    background: #111827;
    border-left: 5px solid #667eea;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 12px;
    font-size: 18px;
    color: #e2e7ff;
    font-weight: 500;
    line-height: 1.5;
}

.task-item {
    background: #111827;
    padding: 20px;
    margin-bottom: 16px;
    border-radius: 12px;
    font-size: 18px;
    color: #e2e7ff;
    border-left: 5px solid #48bb78;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 500;
    line-height: 1.5;
}

.task-item:hover {
    background: #1f2937;
    transform: translateX(4px);
}
}

.activity-btn {
    background: #667eea;
    color: white;
    border: none;
    padding: 10px 14px;
    border-radius: 12px;
    cursor: pointer;
    font-weight: 600;
    margin-bottom: 8px;
}

.activity-log-item {
    background: #0f172a;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
    color: #e2e7ff;
    font-size: 14px;
}

.goal-card {
    background: #111827;
    border-left: 4px solid #667eea;
    padding: 16px;
    margin-bottom: 16px;
    border-radius: 8px;
    font-size: 16px;
    color: #e2e7ff;
    font-weight: 500;
}

.task-item {
    background: #111827;
    padding: 16px;
    margin-bottom: 12px;
    border-radius: 8px;
    font-size: 15px;
    color: #e2e7ff;
    border-left: 4px solid #48bb78;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 500;
}

.task-item:hover {
    background: #1f2937;
    transform: translateX(4px);
}

/* Chat Panel */
.chat-panel {
    background: transparent;
    border-radius: 20px;
    padding: 24px;
    box-shadow: none;
    display: flex;
    flex-direction: column;
    min-height: 750px;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    margin-bottom: 20px;
    padding-right: 12px;
}

.chat-messages::-webkit-scrollbar {
    width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 12px;
}

.chat-messages::-webkit-scrollbar-thumb {
    background: #667eea;
    border-radius: 12px;
}

.user-message {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 16px;
}

.user-message-bubble {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 18px 24px;
    border-radius: 20px;
    max-width: 85%;
    word-wrap: break-word;
    font-size: 20px;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
    font-weight: 500;
    line-height: 1.6;
}

.bot-message {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 16px;
}

.bot-message-bubble {
    background: #f0f4f8;
    color: #1a202c;
    padding: 18px 24px;
    border-radius: 20px;
    max-width: 85%;
    word-wrap: break-word;
    font-size: 20px;
    border: 1px solid #e2e8f0;
    font-weight: 500;
    line-height: 1.6;
}

.thinking {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 16px;
}

.thinking-bubble {
    background: #fef5e7;
    color: #744210;
    padding: 16px 20px;
    border-radius: 20px;
    font-size: 18px;
    border: 1px solid #f8d7a1;
    font-style: italic;
    font-weight: 500;
    line-height: 1.5;
}

/* Input Area */
.input-area {
    display: flex;
    gap: 12px;
}

div[data-testid="stChatInput"] {
    flex: 1;
}

div[data-testid="stChatInput"] textarea {
    font-size: 20px !important;
    border-radius: 16px !important;
    border: 2px solid #e2e8f0 !important;
    padding: 18px 24px !important;
    min-height: 80px !important;
}

div[data-testid="stChatInput"] textarea:focus {
    border: 2px solid #667eea !important;
}

/* Streamlit Button Styling */
div[data-testid="stButton"] button {
    font-size: 16px !important;
    padding: 12px 24px !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stButton"] button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}

/* Text Area Styling */
div[data-testid="stTextArea"] textarea {
    font-size: 16px !important;
    border-radius: 12px !important;
    border: 2px solid #e2e8f0 !important;
    padding: 12px 16px !important;
    min-height: 100px !important;
}

div[data-testid="stTextArea"] textarea:focus {
    border: 2px solid #667eea !important;
}

/* Right Panel - Analytics */
.right-panel {
    background: transparent;
    border-radius: 20px;
    padding: 32px;
    box-shadow: none;
    height: fit-content;
    position: sticky;
    top: 20px;
}

.stat-card {
    background: linear-gradient(135deg, #48bb7825 0%, #38a16925 100%);
    padding: 24px;
    border-radius: 16px;
    margin-bottom: 20px;
    border-left: 5px solid #48bb78;
    text-align: center;
}

.stat-value {
    font-size: 48px;
    font-weight: bold;
    color: #22543d;
    margin-bottom: 12px;
}

.stat-label {
    font-size: 20px;
    color: #276749;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
}

.habit-badge {
    display: inline-block;
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 10px 18px;
    border-radius: 24px;
    font-size: 16px;
    margin: 8px 8px 8px 0;
    font-weight: 600;
}

/* Responsive */
@media (max-width: 1200px) {
    .main-container {
        grid-template-columns: 1fr;
        gap: 20px;
    }
    
    .left-panel, .chat-panel {
        position: relative;
        top: 0;
    }
    
    .header-title {
        font-size: 36px;
    }
    
    .header-subtitle {
        font-size: 18px;
    }
    
    .panel-title {
        font-size: 20px;
    }
    
    .activity-card, .goal-card, .task-item {
        font-size: 16px;
        padding: 16px;
    }
    
    .stat-value {
        font-size: 32px;
    }
    
    .stat-label {
        font-size: 16px;
    }
    
    .user-message-bubble, .bot-message-bubble, .thinking-bubble {
        font-size: 16px;
        padding: 14px 18px;
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

# -------- HEADER --------
st.markdown("""
<div class="header-container">
    <div class="header-title">🧠 ADHD AI Coach</div>
    <div class="header-subtitle">Your Personal Productivity & Focus Companion</div>
</div>
""", unsafe_allow_html=True)

# -------- MAIN CONTENT --------
col_left, col_right = st.columns([1, 1.6], gap="medium")

# -------- LEFT PANEL: DASHBOARD --------
with col_left:
    st.markdown('<div class="left-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">📌 ADHD Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">Focus tools, task breakdown, and progress all in one place.</div>', unsafe_allow_html=True)

    st.markdown('<div class="activity-card">', unsafe_allow_html=True)
    status_text = "Active" if st.session_state.timer_active else "Inactive"
    st.markdown(f'<div style="font-weight:700; margin-bottom: 8px;">⏱️ Focus Session Status: {status_text}</div>', unsafe_allow_html=True)
    remaining = st.session_state.timer_seconds
    if st.session_state.timer_active and st.session_state.timer_start:
        elapsed = int(time.time() - st.session_state.timer_start)
        remaining = max(0, st.session_state.timer_seconds - elapsed)
        if remaining == 0:
            st.session_state.timer_active = False
            st.session_state.timer_start = None
            st.session_state.timer_seconds = st.session_state.timer_duration
            status_text = "Completed"
            # Update gamification
            today = datetime.date.today()
            yesterday = today - datetime.timedelta(days=1)
            if st.session_state.last_session_date == yesterday.isoformat():
                st.session_state.current_streak += 1
            elif st.session_state.last_session_date == today.isoformat():
                pass  # already counted today
            else:
                st.session_state.current_streak = 1
            if st.session_state.current_streak > st.session_state.longest_streak:
                st.session_state.longest_streak = st.session_state.current_streak
            st.session_state.last_session_date = today.isoformat()
            st.session_state.points += 10  # 10 points per session
            # Level up every 50 points
            new_level = (st.session_state.points // 50) + 1
            if new_level > st.session_state.level:
                st.session_state.level = new_level
            # Badges
            if st.session_state.current_streak >= 3 and "3-Day Streak" not in st.session_state.badges:
                st.session_state.badges.append("3-Day Streak")
            if st.session_state.current_streak >= 7 and "Week Warrior" not in st.session_state.badges:
                st.session_state.badges.append("Week Warrior")
            if st.session_state.points >= 100 and "Century Club" not in st.session_state.badges:
                st.session_state.badges.append("Century Club")
    mins = remaining // 60
    secs = remaining % 60
    st.markdown(f'<div style="margin-bottom: 8px;">Remaining: <strong>{mins:02d}:{secs:02d}</strong></div>', unsafe_allow_html=True)
    st.markdown(f'<div>Phone distractions: <strong>{st.session_state.phone_distractions}</strong></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel-title">🎯 Today\'s Goals</div>', unsafe_allow_html=True)
    for goal in st.session_state.goals:
        st.markdown(f'<div class="goal-card">{goal}</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel-title" style="margin-top: 20px;">✓ Tasks</div>', unsafe_allow_html=True)
    for task in st.session_state.tasks:
        st.markdown(f'<div class="task-item">□ {task}</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel-title">📝 Session Actions</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button('💻 Working', key='action_working'):
            st.session_state.activity_log.insert(0, {'time': datetime.datetime.now().strftime('%H:%M'), 'activity': 'Working'})
    with col2:
        if st.button('📱 Phone distraction', key='action_phone'):
            st.session_state.activity_log.insert(0, {'time': datetime.datetime.now().strftime('%H:%M'), 'activity': 'Phone distraction'})
            st.session_state.phone_distractions += 1

    col3, col4 = st.columns(2)
    with col3:
        if st.button('☕ Break', key='action_break'):
            st.session_state.activity_log.insert(0, {'time': datetime.datetime.now().strftime('%H:%M'), 'activity': 'Short break'})
    with col4:
        if st.button('🧘 Reset focus', key='action_reset_focus'):
            st.session_state.activity_log.insert(0, {'time': datetime.datetime.now().strftime('%H:%M'), 'activity': 'Refocusing'})

    st.markdown('<div class="panel-title" style="margin-top: 24px;">📊 Quick Stats</div>', unsafe_allow_html=True)
    stat_col1, stat_col2 = st.columns(2)
    with stat_col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{st.session_state.session_count}</div>
            <div class="stat-label">Chat Sessions</div>
        </div>
        """, unsafe_allow_html=True)
    with stat_col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{st.session_state.completion_rate}%</div>
            <div class="stat-label">Completion</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="panel-title" style="margin-top: 20px;">🔥 Active Habits</div>', unsafe_allow_html=True)
    habits_html = "".join([f'<div class="habit-badge">{habit}</div>' for habit in st.session_state.habits])
    st.markdown(f"""<div>{habits_html}</div>""", unsafe_allow_html=True)

    st.markdown('<div class="panel-title" style="margin-top: 24px;">🎖️ Gamification</div>', unsafe_allow_html=True)
    gam_col1, gam_col2 = st.columns(2)
    with gam_col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{st.session_state.current_streak}</div>
            <div class="stat-label">Current Streak</div>
        </div>
        """, unsafe_allow_html=True)
    with gam_col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{st.session_state.longest_streak}</div>
            <div class="stat-label">Longest Streak</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">Level {st.session_state.level}</div>
        <div class="stat-label">{st.session_state.points} Points</div>
    </div>
    """, unsafe_allow_html=True)
    if st.session_state.badges:
        badges_html = "".join([f'<div class="habit-badge">{badge}</div>' for badge in st.session_state.badges])
        st.markdown(f"""<div style="margin-top: 12px; font-size: 18px; font-weight: 600;">🏅 Earned Badges:</div>{badges_html}""", unsafe_allow_html=True)

    st.markdown('<div class="panel-title" style="margin-top: 20px;">📝 Daily Reflection</div>', unsafe_allow_html=True)
    reflection_input = st.text_area("How did your focus sessions go today? Any insights?", value=st.session_state.reflection, key="reflection_input", height=120, label_visibility="collapsed")
    if reflection_input != st.session_state.reflection:
        st.session_state.reflection = reflection_input

    if st.session_state.progress:
        st.markdown('<div class="panel-title" style="margin-top: 20px;">📈 This Week</div>', unsafe_allow_html=True)
        df = pd.DataFrame(st.session_state.progress, columns=["Productivity"])
        st.line_chart(df, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

# -------- RIGHT PANEL: CHAT --------
with col_right:
    st.markdown('<div class="chat-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">💬 Coach Chat</div>', unsafe_allow_html=True)

    timer_col1, timer_col2, timer_col3 = st.columns([1, 1, 1])
    if timer_col1.button('▶ Start focus'): 
        if not st.session_state.timer_active:
            st.session_state.timer_active = True
            st.session_state.timer_start = time.time()
    if timer_col2.button('⏸ Pause focus'):
        if st.session_state.timer_active and st.session_state.timer_start:
            elapsed = int(time.time() - st.session_state.timer_start)
            st.session_state.timer_seconds = max(0, st.session_state.timer_seconds - elapsed)
            st.session_state.timer_active = False
            st.session_state.timer_start = None
    if timer_col3.button('↻ Reset focus'):
        st.session_state.timer_active = False
        st.session_state.timer_seconds = st.session_state.timer_duration
        st.session_state.timer_start = None

    if st.session_state.timer_active and st.session_state.timer_start:
        elapsed = int(time.time() - st.session_state.timer_start)
        remaining = max(0, st.session_state.timer_seconds - elapsed)
        if remaining == 0:
            st.session_state.timer_active = False
            st.session_state.timer_start = None
            st.session_state.timer_seconds = st.session_state.timer_duration
            # Update gamification
            today = datetime.date.today()
            yesterday = today - datetime.timedelta(days=1)
            if st.session_state.last_session_date == yesterday.isoformat():
                st.session_state.current_streak += 1
            elif st.session_state.last_session_date == today.isoformat():
                pass  # already counted today
            else:
                st.session_state.current_streak = 1
            if st.session_state.current_streak > st.session_state.longest_streak:
                st.session_state.longest_streak = st.session_state.current_streak
            st.session_state.last_session_date = today.isoformat()
            st.session_state.points += 10  # 10 points per session
            # Level up every 50 points
            new_level = (st.session_state.points // 50) + 1
            if new_level > st.session_state.level:
                st.session_state.level = new_level
            # Badges
            if st.session_state.current_streak >= 3 and "3-Day Streak" not in st.session_state.badges:
                st.session_state.badges.append("3-Day Streak")
            if st.session_state.current_streak >= 7 and "Week Warrior" not in st.session_state.badges:
                st.session_state.badges.append("Week Warrior")
            if st.session_state.points >= 100 and "Century Club" not in st.session_state.badges:
                st.session_state.badges.append("Century Club")
    else:
        remaining = st.session_state.timer_seconds
    mins = remaining // 60
    secs = remaining % 60
    st.markdown(f'<div class="activity-card" style="font-size: 32px; text-align: center; font-weight: bold; background: linear-gradient(135deg, #667eea25 0%, #764ba225 100%); border-left: 5px solid #667eea; padding: 32px; margin: 24px 0;">⏱️ {mins:02d}:{secs:02d}</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <div class="user-message-bubble">{render_chat_text(msg["content"])}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="bot-message">
                <div class="bot-message-bubble">{render_chat_text(msg["content"])}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    user_input = st.chat_input("💬 Ask your ADHD coach anything...", key="main_input")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.markdown(f"""
        <div class="user-message">
            <div class="user-message-bubble">{user_input}</div>
        </div>
        """, unsafe_allow_html=True)

        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("""
        <div class="thinking">
            <div class="thinking-bubble">⏳ Thinking...</div>
        </div>
        """, unsafe_allow_html=True)

        try:
            response = requests.post(API_URL, json={
                "text": user_input,
                "history": st.session_state.messages
            }, timeout=35)
            if response.status_code != 200:
                reply = f"❌ Backend error ({response.status_code}): {response.text}"
            else:
                data = response.json()
                reply = data.get("reply", "⚠️ No response")
        except requests.exceptions.RequestException as e:
            reply = f"❌ Connection error: {str(e)}"
        except Exception as e:
            reply = f"❌ Error: {str(e)}"

        thinking_placeholder.empty()

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.markdown(f"""
        <div class="bot-message">
            <div class="bot-message-bubble">{render_chat_text(reply)}</div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.session_count += 1
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
