import os
import hashlib
from contextlib import contextmanager
from dotenv import load_dotenv
import csv
from datetime import datetime

# 🔥 Load .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# ✅ DEBUG LINE (add here)
print("DATABASE_URL:", DATABASE_URL)

def _append_feedback_to_csv(username, rating, text):
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "feedback.csv")
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["username", "rating", "feedback_text", "created_at"])
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([username, rating, text, created_at])

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# CLOUD DATABASE (POSTGRESQL)
# ==========================================
if DATABASE_URL:
    import psycopg2
    
    @contextmanager
    def get_connection():
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
                break
            except psycopg2.OperationalError as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ DB connection attempt {attempt + 1} failed. Retrying...")
                    time.sleep(2)
                else:
                    raise e
        try:
            yield conn
        finally:
            conn.close()

    def init_db():
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id SERIAL PRIMARY KEY,
                    final_score REAL,
                    level TEXT,
                    username TEXT DEFAULT 'anonymous',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    contact_info TEXT,
                    is_verified BOOLEAN DEFAULT FALSE,
                    otp_code TEXT,
                    otp_expires_at TIMESTAMP
                )
                """)
                cur.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    username TEXT,
                    rating TEXT,
                    feedback_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
            conn.commit()

            try:
                with conn.cursor() as cur:
                    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_info TEXT")
                    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE")
                    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_code TEXT")
                    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_expires_at TIMESTAMP")
                conn.commit()
            except Exception:
                conn.rollback()

    def create_user(username, password, contact_info=None):
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (username, password_hash, contact_info, is_verified) VALUES (%s, %s, %s, TRUE)",
                        (username, hash_password(password), contact_info)
                    )
                conn.commit()
            return True, ""
        except Exception as e:
            print(f"Database error creating user: {e}")
            return False, str(e)

    def verify_user(username, password):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
                row = cur.fetchone()
                return bool(row and row[0] == hash_password(password))

    def update_user_contact(username, contact_info):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET contact_info = %s WHERE username = %s",
                    (contact_info, username)
                )
            conn.commit()

    def get_user_by_username(username):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT username, contact_info, otp_code, otp_expires_at, is_verified FROM users WHERE username = %s", (username,))
                row = cur.fetchone()
                if row:
                    return {"username": row[0], "contact_info": row[1], "otp_code": row[2], "otp_expires_at": row[3], "is_verified": row[4]}
        return None

    def set_user_otp(username, otp, expires_at):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET otp_code = %s, otp_expires_at = %s WHERE username = %s",
                    (otp, expires_at, username)
                )
            conn.commit()

    def activate_user(username):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET is_verified = TRUE, otp_code = NULL, otp_expires_at = NULL WHERE username = %s",
                    (username,)
                )
            conn.commit()

    def reset_password(username, contact_info, new_password):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    cur.execute("UPDATE users SET password_hash = %s, otp_code = NULL, otp_expires_at = NULL WHERE username = %s", (hash_password(new_password), username))
                    conn.commit()
                    return True
        return False

    def save_result(score, level, username="anonymous"):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO results (final_score, level, username) VALUES (%s, %s, %s)",
                    (score, level, username)
                )
            conn.commit()

    def save_feedback(username, rating, text):
        _append_feedback_to_csv(username, rating, text)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO feedback (username, rating, feedback_text) VALUES (%s, %s, %s)",
                    (username, rating, text)
                )
            conn.commit()

# ==========================================
# LOCAL DATABASE (SQLITE)
# ==========================================
else:
    import sqlite3
    
    db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "database")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "data.db")

    @contextmanager
    def get_connection():
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            yield conn
        finally:
            conn.close()

    def init_db():
        with get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                final_score REAL,
                level TEXT
            )
            """)
            try:
                conn.execute("ALTER TABLE results ADD COLUMN username TEXT DEFAULT 'anonymous'")
                conn.execute("ALTER TABLE results ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            except sqlite3.OperationalError:
                pass

            conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                contact_info TEXT,
                is_verified BOOLEAN DEFAULT 0,
                otp_code TEXT,
                otp_expires_at TIMESTAMP
            )
            """)
            
            for col in ["contact_info TEXT", "is_verified BOOLEAN DEFAULT 0", "otp_code TEXT", "otp_expires_at TIMESTAMP"]:
                try:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col}")
                except sqlite3.OperationalError:
                    pass

            conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                rating TEXT,
                feedback_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()

    def create_user(username, password, contact_info=None):
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash, contact_info, is_verified) VALUES (?, ?, ?, TRUE)",
                    (username, hash_password(password), contact_info)
                )
                conn.commit()
            return True, ""
        except Exception as e:
            print(f"Database error creating user: {e}")
            return False, str(e)

    def verify_user(username, password):
        with get_connection() as conn:
            cursor = conn.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return bool(row and row[0] == hash_password(password))

    def update_user_contact(username, contact_info):
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET contact_info = ? WHERE username = ?",
                (contact_info, username)
            )
            conn.commit()

    def get_user_by_username(username):
        with get_connection() as conn:
            cursor = conn.execute("SELECT username, contact_info, otp_code, otp_expires_at, is_verified FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                return {"username": row[0], "contact_info": row[1], "otp_code": row[2], "otp_expires_at": row[3], "is_verified": row[4]}
        return None

    def set_user_otp(username, otp, expires_at):
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET otp_code = ?, otp_expires_at = ? WHERE username = ?",
                (otp, expires_at, username)
            )
            conn.commit()

    def activate_user(username):
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET is_verified = TRUE, otp_code = NULL, otp_expires_at = NULL WHERE username = ?",
                (username,)
            )
            conn.commit()

    def reset_password(username, contact_info, new_password):
        with get_connection() as conn:
            cursor = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.execute("UPDATE users SET password_hash = ?, otp_code = NULL, otp_expires_at = NULL WHERE username = ?", (hash_password(new_password), username))
                conn.commit()
                return True
        return False

    def save_result(score, level, username="anonymous"):
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO results (final_score, level, username) VALUES (?, ?, ?)",
                (score, level, username)
            )
            conn.commit()

    def save_feedback(username, rating, text):
        _append_feedback_to_csv(username, rating, text)
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO feedback (username, rating, feedback_text) VALUES (?, ?, ?)",
                (username, rating, text)
            )
            conn.commit()

try:
    init_db()
except Exception as e:
    print(f"⚠️ Warning: Could not initialize database on import: {e}")
