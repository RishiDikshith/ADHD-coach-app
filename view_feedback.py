import sqlite3
import os

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(PROJECT_ROOT, "database", "data.db")

def view_feedback():
    """Connects to the database and prints all user feedback."""
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("--- User Feedback ---")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback';")
        if cursor.fetchone() is None:
            print("No feedback submitted yet (table does not exist).")
            conn.close()
            return

        cursor.execute("SELECT username, rating, feedback_text, created_at FROM feedback ORDER BY created_at DESC;")
        feedbacks = cursor.fetchall()

        if not feedbacks:
            print("No feedback found in the database.")
        else:
            for f in feedbacks:
                print(f"[{f[3]}] {f[0]} ({f[1]}): {f[2]}")
                print("-" * 50)
        
        conn.close()

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    view_feedback()