import os
import sys

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.database.db import get_connection, DATABASE_URL

def view_users():
    """Connects to the active database (Cloud or Local) and prints all users."""
    print("--- Registered Users ---")
    try:
        with get_connection() as conn:
            if DATABASE_URL:
                print("🌍 Connected to CLOUD PostgreSQL (NeonTech)")
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, username, contact_info, is_verified FROM users ORDER BY id;")
                    users = cursor.fetchall()
            else:
                print("💻 Connected to LOCAL SQLite")
                cursor = conn.execute("SELECT id, username, contact_info, is_verified FROM users ORDER BY id;")
                users = cursor.fetchall()

            if not users:
                print("No users found in the database.")
            else:
                print(f"{'ID':<5} | {'Username':<20} | {'Email/Contact':<30} | {'Verified'}")
                print("-" * 80)
                for user in users:
                    print(f"{user[0]:<5} | {str(user[1]):<20} | {str(user[2]):<30} | {bool(user[3])}")
                    
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    view_users()