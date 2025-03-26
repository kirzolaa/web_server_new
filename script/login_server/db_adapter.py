
import os
import json
import sqlite3
from replit import db as replit_db

class DatabaseAdapter:
    """Adapter that can work with both SQLite and Repl DB"""
    
    def __init__(self, use_replit_db=True):
        self.use_replit_db = use_replit_db and os.getenv('REPLIT_DB_URL') is not None
        if not self.use_replit_db:
            # Use regular SQLite when not deployed or when specified
            self.db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    
    def get_connection(self):
        """Get the appropriate database connection"""
        if self.use_replit_db:
            return ReplitDBConnection()
        else:
            return sqlite3.connect(self.db_path)

class ReplitDBConnection:
    """A wrapper to make Replit DB act similar to SQLite connections"""
    
    def execute(self, query, params=()):
        """Simulate executing a query against Replit DB"""
        # Parse the operation from the query
        operation = query.strip().split(' ')[0].upper()
        
        if operation == 'INSERT':
            # Handle INSERT operations
            if 'users' in query:
                # Extract table name from the query
                username = params[0]
                data = {
                    'name': params[1],
                    'email': params[2],
                    'password_hash': params[3],
                    'role_id': params[4],
                    'bio': params[5] if len(params) > 5 else None,
                    'profile_picture': params[6] if len(params) > 6 else None
                }
                replit_db[f"user:{username}"] = json.dumps(data)
            elif 'user_activity' in query:
                # Handle user activity logging
                activity_id = len([k for k in replit_db.keys() if k.startswith("activity:")])
                replit_db[f"activity:{activity_id}"] = json.dumps({
                    'username': params[0],
                    'type': params[1],
                    'description': params[2],
                    'created_at': params[3] if len(params) > 3 else None
                })
            elif 'roles' in query:
                # Handle roles
                role_id = params[0]
                replit_db[f"role:{role_id}"] = json.dumps({
                    'role_name': params[1],
                    'permissions': params[2]
                })
        
        elif operation == 'SELECT':
            # This is a simplified approach - in a real implementation, 
            # you would need to parse the query properly
            if 'users' in query and 'username' in query:
                # Return a cursor-like object with fetchone capability
                username = params[0]
                key = f"user:{username}"
                if key in replit_db:
                    data = json.loads(replit_db[key])
                    return ReplitDBCursor([data])
                return ReplitDBCursor([])
        
        # Return a cursor by default
        return ReplitDBCursor([])
    
    def commit(self):
        """No-op for Replit DB as changes are immediate"""
        pass
        
    def close(self):
        """No-op for Replit DB"""
        pass

class ReplitDBCursor:
    """A cursor-like wrapper for Replit DB results"""
    
    def __init__(self, results):
        self.results = results
        self.index = 0
    
    def fetchone(self):
        """Fetch one result"""
        if self.index < len(self.results):
            result = self.results[self.index]
            self.index += 1
            return result
        return None
    
    def fetchall(self):
        """Fetch all results"""
        return self.results

def get_db_adapter():
    """Get the database adapter instance"""
    return DatabaseAdapter(use_replit_db=os.getenv('REPLIT_DEPLOYMENT') == '1')
