import sqlite3
import os

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(PROJECT_ROOT, "database", "data.db")

def view_users():
    """Connects to the database and prints all registered users."""
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("--- Registered Users ---")
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if cursor.fetchone() is None:
            print("The 'users' table does not exist in the database.")
            conn.close()
            return

        cursor.execute("SELECT id, username FROM users ORDER BY id;")
        users = cursor.fetchall()

        if not users:
            print("No users found in the database.")
        else:
            print(f"{'ID':<5} {'Username':<20}")
            print("-" * 27)
            for user in users:
                print(f"{user[0]:<5} {user[1]:<20}")
        
        conn.close()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    view_users()