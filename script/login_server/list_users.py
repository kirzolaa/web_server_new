import sqlite3
import os
import sys
from datetime import datetime

def list_users():
    """List all registered users from the SQLite database"""
    # Get the path to the database file
    DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')
    
    # Check if database file exists
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        print("Ensure the login server has been run at least once to create the database.")
        sys.exit(1)
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Fetch all users
        cursor.execute('SELECT id, username, email, created_at, last_login FROM users')
        users = cursor.fetchall()
        
        # Print users in a formatted way
        print("\n=== Registered Users ===")
        print(f"Database Location: {DB_PATH}")
        print("-" * 110)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Created At':<25} {'Last Login':<25}")
        print("-" * 110)
        
        if not users:
            print("No users registered yet.")
        else:
            for user in users:
                user_id, username, email, created_at, last_login = user
                # Convert timestamps to a readable format
                created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S') if created_at else "N/A"
                last_login = datetime.strptime(last_login, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S') if last_login else "Never"
                
                print(f"{user_id:<5} {username:<20} {email:<30} {created_at:<25} {last_login:<25}")
        
        print(f"\nTotal users: {len(users)}")
    
    except sqlite3.Error as e:
        print(f"Error accessing database: {e}")
        print("Possible reasons:")
        print("1. Database is locked")
        print("2. Database file is corrupted")
        print("3. Login server is currently running")
    finally:
        # Always close the connection
        conn.close()

if __name__ == '__main__':
    list_users()
