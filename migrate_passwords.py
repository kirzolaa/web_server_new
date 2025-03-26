import sqlite3
import bcrypt

# Connect to database
db_path = 'database.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Remove password_salt column
cursor.execute('ALTER TABLE users DROP COLUMN password_salt')

# Update existing password hashes
cursor.execute('SELECT id, password FROM users')
users = cursor.fetchall()

for user_id, password in users:
    # Rehash password with bcrypt
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute('UPDATE users SET password = ? WHERE id = ?', 
                  (hashed.decode('utf-8'), user_id))

# Commit changes
conn.commit()
conn.close()

print('Password migration complete!')
