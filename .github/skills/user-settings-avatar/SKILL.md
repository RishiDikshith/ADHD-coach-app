---
name: user-settings-avatar
description: "Implement username-based avatar logo (first letter initial) with persistent settings panel. Configure theme, notifications, language, and other preferences. Includes authentication persistence fix using Streamlit session files and comprehensive testing checklist."
---

# User Avatar & Settings Panel Implementation Skill

## Overview
This skill packages a complete workflow for adding a clickable user avatar (with username initials) that opens a settings panel, plus fixes for authentication persistence across browser refreshes.

## Problem Statement
- Users don't have a visual identity (avatar) in the app
- Settings are scattered or missing
- Every browser refresh requires re-login (authentication not persistent)
- User preferences don't persist across sessions

## Solution Architecture
1. **Avatar Component**: Generate colored badge from username's first letter
2. **Settings Persistence**: Store user preferences in Streamlit's session file storage
3. **Auth Persistence**: Store authentication token/session in filesystem to survive browser refreshes
4. **Settings UI**: Modal or sidebar section for configuration
5. **Settings Scope**: Theme, notifications, language, productivity settings

---

## Implementation Steps

### Phase 1: Fix Authentication Persistence (CRITICAL - Do First)

#### 1.1 Create Session Manager Utility
**File**: `src/utils/session_manager.py`

Create a utility to persist authentication tokens to the filesystem:

```python
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

class SessionManager:
    def __init__(self, session_dir=".session_data"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        self.session_file = self.session_dir / "user_session.json"
    
    def save_session(self, username, token=None, expires_at=None):
        """Save authentication session to persistent storage"""
        if expires_at is None:
            expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        
        session_data = {
            "username": username,
            "token": token or username,  # Simple token; enhance with JWT in production
            "login_time": datetime.now().isoformat(),
            "expires_at": expires_at
        }
        
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f)
    
    def load_session(self):
        """Load authentication session from persistent storage"""
        if not self.session_file.exists():
            return None
        
        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check if session is still valid
            expires_at = datetime.fromisoformat(session_data.get("expires_at", datetime.min.isoformat()))
            if expires_at > datetime.now():
                return session_data
            else:
                self.clear_session()
                return None
        except Exception as e:
            print(f"Error loading session: {e}")
            return None
    
    def clear_session(self):
        """Clear authentication session"""
        if self.session_file.exists():
            self.session_file.unlink()
```

#### 1.2 Integrate Session Manager into app.py
At the top of `frontend/app.py` (after imports, before state initialization):

```python
from src.utils.session_manager import SessionManager

session_manager = SessionManager()

# IMPORTANT: Restore session from disk on app load
if "authenticated" not in st.session_state:
    persisted_session = session_manager.load_session()
    if persisted_session:
        st.session_state.authenticated = True
        st.session_state.username = persisted_session["username"]
        st.session_state.remember_me = True
    else:
        st.session_state.authenticated = False
        st.session_state.username = None
```

#### 1.3 Update Login Logic
In the login form success handler:
```python
if st.form_submit_button("Login", use_container_width=True):
    log_user = log_user.strip()
    if verify_user(log_user, log_pass):
        # ... existing verification logic ...
        
        # ADD THIS: Save session persistently
        st.session_state.authenticated = True
        st.session_state.username = log_user
        st.session_state.remember_me = remember_me
        session_manager.save_session(log_user)  # <-- NEW LINE
        st.rerun()
```

#### 1.4 Update Logout Logic
```python
if st.button("Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.username = None
    session_manager.clear_session()  # <-- NEW LINE
    st.rerun()
```

---

### Phase 2: Create User Avatar Component

#### 2.1 Create Avatar Utility
**File**: `src/utils/avatar.py`

```python
import hashlib

def get_avatar_color(username):
    """Generate consistent color from username hash"""
    hash_obj = hashlib.md5(username.encode())
    hash_hex = hash_obj.hexdigest()
    
    # Predefined color palette for consistency
    colors = [
        "#667eea", "#764ba2", "#f093fb", "#4facfe", "#43e97b",
        "#fa709a", "#fee140", "#30cfd0", "#a8edea", "#fed6e3"
    ]
    
    # Use hash to pick a color
    color_index = int(hash_hex, 16) % len(colors)
    return colors[color_index]

def get_avatar_initials(username):
    """Get first letter of username (uppercase)"""
    return username[0].upper() if username else "?"

def render_avatar_html(username, size="40px"):
    """Generate HTML for avatar badge"""
    initials = get_avatar_initials(username)
    color = get_avatar_color(username)
    
    return f"""
    <div style="
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: {size};
        height: {size};
        border-radius: 50%;
        background: {color};
        color: white;
        font-weight: bold;
        font-size: calc({size} * 0.5);
        font-family: Arial, sans-serif;
        cursor: pointer;
        user-select: none;
    ">
        {initials}
    </div>
    """
```

---

### Phase 3: Implement Settings Panel

#### 3.1 Create Settings Manager
**File**: `src/utils/settings_manager.py`

```python
import json
from pathlib import Path
from datetime import datetime

class SettingsManager:
    """Manage user settings persistence"""
    
    DEFAULT_SETTINGS = {
        "theme": "dark",
        "language": "en",
        "notifications_enabled": True,
        "notification_frequency": "daily",
        "timer_duration": 25,
        "auto_check_in": True,
        "sound_enabled": True,
        "use_12h_format": False
    }
    
    def __init__(self, username, settings_dir=".settings_data"):
        self.username = username
        self.settings_dir = Path(settings_dir)
        self.settings_dir.mkdir(exist_ok=True)
        self.settings_file = self.settings_dir / f"{username}_settings.json"
    
    def load_settings(self):
        """Load user settings with fallback to defaults"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    saved = json.load(f)
                # Merge with defaults (in case new settings were added)
                return {**self.DEFAULT_SETTINGS, **saved}
            except Exception as e:
                print(f"Error loading settings: {e}")
                return self.DEFAULT_SETTINGS.copy()
        return self.DEFAULT_SETTINGS.copy()
    
    def save_settings(self, settings):
        """Save user settings to disk"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def update_setting(self, key, value):
        """Update a single setting"""
        settings = self.load_settings()
        settings[key] = value
        return self.save_settings(settings)
```

#### 3.2 Integrate Settings into app.py
After session manager initialization, add:

```python
# Initialize settings manager
if st.session_state.username:
    settings_manager = SettingsManager(st.session_state.username)
    
    # Load settings into session on first authentication
    if "user_settings" not in st.session_state:
        st.session_state.user_settings = settings_manager.load_settings()
else:
    settings_manager = None
```

---

### Phase 4: Build Settings UI

#### 4.1 Create Settings Modal/Sidebar Section
In `frontend/app.py` sidebar (after logout button):

```python
# -------- USER AVATAR & SETTINGS --------
with st.sidebar:
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Display avatar
        avatar_html = render_avatar_html(st.session_state.username, size="45px")
        st.markdown(avatar_html, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"**{st.session_state.username}**", unsafe_allow_html=True)
        st.caption("User Account")
    
    # Settings button
    if st.button("⚙️ Settings", use_container_width=True, key="settings_btn"):
        st.session_state.show_settings = True
```

#### 4.2 Create Settings Modal
Add this function in `frontend/app.py`:

```python
def render_settings_modal():
    """Render settings configuration panel"""
    st.markdown("<h2>⚙️ User Settings</h2>", unsafe_allow_html=True)
    
    settings = st.session_state.user_settings
    
    # Theme Settings
    st.subheader("🎨 Appearance")
    theme = st.selectbox(
        "Theme",
        options=["dark", "light"],
        index=0 if settings["theme"] == "dark" else 1,
        key="theme_select"
    )
    
    time_format = st.selectbox(
        "Time Format",
        options=["24-hour", "12-hour"],
        index=0 if not settings["use_12h_format"] else 1,
        key="time_select"
    )
    
    # Notification Settings
    st.subheader("🔔 Notifications")
    notif_enabled = st.checkbox(
        "Enable Notifications",
        value=settings["notifications_enabled"],
        key="notif_check"
    )
    
    if notif_enabled:
        notif_freq = st.selectbox(
            "Notification Frequency",
            options=["hourly", "daily", "weekly"],
            index=["hourly", "daily", "weekly"].index(settings["notification_frequency"]),
            key="notif_freq_select"
        )
    else:
        notif_freq = settings["notification_frequency"]
    
    sound_enabled = st.checkbox(
        "Sound Notifications",
        value=settings["sound_enabled"],
        key="sound_check"
    )
    
    # Productivity Settings
    st.subheader("⏱️ Productivity")
    timer_duration = st.slider(
        "Pomodoro Timer Duration (minutes)",
        min_value=5,
        max_value=60,
        value=settings["timer_duration"],
        step=5,
        key="timer_slider"
    )
    
    auto_checkin = st.checkbox(
        "Enable Auto Check-in",
        value=settings["auto_check_in"],
        key="checkin_check"
    )
    
    # Language Settings
    st.subheader("🌐 Language")
    language = st.selectbox(
        "Language",
        options=["en", "es", "fr", "de"],
        index=0 if settings["language"] == "en" else ["en", "es", "fr", "de"].index(settings["language"]),
        key="lang_select"
    )
    
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
            settings_manager.save_settings(new_settings)
            st.session_state.user_settings = new_settings
            
            st.success("✅ Settings saved successfully!")
            st.session_state.show_settings = False
            time.sleep(1.5)
            st.rerun()
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True, key="cancel_settings"):
            st.session_state.show_settings = False
            st.rerun()
```

#### 4.3 Add Settings State and Modal Trigger
In state initialization section:
```python
if "show_settings" not in st.session_state:
    st.session_state.show_settings = False
```

After authentication check, before main content:
```python
# Show settings modal if triggered
if st.session_state.show_settings:
    # Create a modal container
    modal_col1, modal_col2, modal_col3 = st.columns([1, 2, 1])
    with modal_col2:
        with st.container():
            render_settings_modal()
    st.stop()  # Prevent main content from rendering while settings are open
```

---

### Phase 5: Apply Settings Throughout App

Update styling and behavior to use settings:

#### 5.1 Theme Application
```python
def apply_theme_setting():
    """Apply theme setting to page CSS"""
    theme = st.session_state.user_settings.get("theme", "dark")
    
    if theme == "light":
        # Light mode CSS overrides
        st.markdown("""
        <style>
        body { background: #ffffff !important; color: #000000 !important; }
        [data-testid="stSidebar"] { background: #f5f5f5 !important; }
        </style>
        """, unsafe_allow_html=True)
```

#### 5.2 Timer Duration Update
```python
def initialize_timer_from_settings():
    """Set timer duration from user settings"""
    duration_minutes = st.session_state.user_settings.get("timer_duration", 25)
    st.session_state.timer_duration = duration_minutes * 60
    st.session_state.timer_seconds = duration_minutes * 60
```

---

## Testing Checklist

### ✅ Authentication Persistence Tests
- [ ] **T1**: Login → Refresh browser → Verify still logged in (no login screen)
- [ ] **T2**: Logout → Refresh browser → Verify back at login screen
- [ ] **T3**: Login with "Remember me" → Close/reopen browser → Still logged in
- [ ] **T4**: Wait 7+ days → Session expired, must re-login

### ✅ Avatar Component Tests
- [ ] **T5**: Avatar displays first letter of username
- [ ] **T6**: Avatar color is consistent for same username
- [ ] **T7**: Different usernames get different avatar colors
- [ ] **T8**: Avatar is clickable and opens settings

### ✅ Settings Panel Tests
- [ ] **T9**: Click avatar → Settings panel opens
- [ ] **T10**: All 8 settings display with current values
- [ ] **T11**: Change each setting individually
- [ ] **T12**: Click "Save Changes" → Settings saved to disk
- [ ] **T13**: Refresh browser → Settings retained
- [ ] **T14**: Logout & login with different user → New user has default settings
- [ ] **T15**: Cancel button → Modal closes without saving

### ✅ Settings Application Tests
- [ ] **T16**: Change theme → Page background updates
- [ ] **T17**: Change time format → Timestamps display correctly (24/12 hour)
- [ ] **T18**: Disable notifications → No notification alerts appear
- [ ] **T19**: Change timer duration → Pomodoro timer uses new value
- [ ] **T20**: Toggle sound → Sound enabled/disabled in notifications
- [ ] **T21**: Change language → UI text updates (requires i18n setup)

### ✅ Edge Cases
- [ ] **T22**: Settings file corrupted → App loads defaults gracefully
- [ ] **T23**: Multiple browser tabs → Settings sync across tabs
- [ ] **T24**: Settings > 8 fields added → Old settings preserved
- [ ] **T25**: Network offline → Settings still persist locally

---

## File Structure After Implementation

```
frontend/
├── app.py (updated)
src/
├── utils/
│   ├── session_manager.py (NEW)
│   ├── settings_manager.py (NEW)
│   └── avatar.py (NEW)
.session_data/ (auto-created)
├── user_session.json
.settings_data/ (auto-created)
├── username1_settings.json
├── username2_settings.json
└── ...
```

---

## Import Statements Required in app.py

```python
from src.utils.session_manager import SessionManager
from src.utils.settings_manager import SettingsManager
from src.utils.avatar import render_avatar_html, get_avatar_color, get_avatar_initials
import time  # For delays after save/delete actions
```

---

## Security Considerations

1. **Token Storage**: Current implementation uses simple file storage. For production:
   - Use JWT tokens with expiry
   - Encrypt session files
   - Implement secure HTTP-only cookies

2. **Settings Privacy**: User settings files contain preferences (not sensitive data) and are per-user

3. **Logout Cleanup**: Always clear session file on logout to prevent session hijacking

---

## Success Criteria

✅ User sees avatar with their initial in header  
✅ Clicking avatar opens settings modal  
✅ All settings save and persist across page refreshes  
✅ Browser refresh doesn't trigger re-login  
✅ Logging out properly clears all session data  
✅ Each user has isolated settings  
✅ Settings are applied throughout the application  

---

## Example Usage After Implementation

```
1. User logs in with username "Alice"
2. Browser shows avatar "A" in header (colored #667eea)
3. Click avatar → Settings panel opens
4. Change theme to "light" + timer to "45 min"
5. Click "Save Changes"
6. Page immediately updates to light theme
7. Refresh browser → Still logged in as Alice, light theme active
8. Close browser + reopen → Still logged in, settings preserved
9. Click logout → Session cleared
10. Try to refresh → Back at login screen
```

