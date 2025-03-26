import json
import os

class UserDataHandler:
    def __init__(self, filename='UserData.json'):
        self.filename = filename
        self.load_data()

    def load_data(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as file:
                self.data = json.load(file)
        else:
            self.data = {}

    def save_data(self):
        with open(self.filename, 'w') as file:
            json.dump(self.data, file, indent=4)

    def register_user(self, username, password):
        if username in self.data:
            return False  # User already exists
        self.data[username] = password  # Store password (consider hashing in production)
        self.save_data()
        return True

    def authenticate_user(self, username, password):
        return self.data.get(username) == password

    def user_exists(self, username):
        return username in self.data
