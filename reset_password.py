import sqlite3
import bcrypt

# Connect to database
db_path = 'database.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Hash the new password
new_password = 'A0ZzaE=asC#3'
hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

# Update password for TerminalThor
cursor.execute('UPDATE users SET password = ? WHERE username = ?', 
              (hashed.decode('utf-8'), 'TerminalThor'))

# Commit changes
conn.commit()
conn.close()

print('Password reset complete! Use A0ZzaE=asC#3 to login')
