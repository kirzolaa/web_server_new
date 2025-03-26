from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import re

# Authenticate and create the PyDrive client
gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Authenticates the user
drive = GoogleDrive(gauth)

# Define the parent folder name in Google Drive
FOLDER_NAME = "versions"
VERSION_FILE = "version.txt"
MAX_MINOR = 5  # Max value for x in 1.x.y
MAX_PATCH = 3  # Max value for y in 1.x.y

def get_folder_id(folder_name):
    """Retrieve folder ID from Google Drive, or create it if not found."""
    query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    folder_list = drive.ListFile({'q': query}).GetList()

    if folder_list:
        return folder_list[0]['id']  # Return the first matching folder ID

    # If folder does not exist, create it
    folder_metadata = {
        'title': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder['id']

def get_next_version(folder_id):
    """Finds the next version number in 1.x.y format."""
    query = f"'{folder_id}' in parents and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()

    versions = []
    pattern = re.compile(r"modern_analytics-(\d+)\.(\d+)\.(\d+)\.exe")  # Matches 1.x.y format

    for file in file_list:
        match = pattern.match(file['title'])
        if match:
            major, minor, patch = map(int, match.groups())
            versions.append((major, minor, patch))

    if not versions:
        return "modern_analytics-1.0.0.exe"  # First file uploaded

    # Sort versions to find the latest one
    versions.sort()
    last_major, last_minor, last_patch = versions[-1]

    # Increment logic
    if last_patch < MAX_PATCH:
        next_major, next_minor, next_patch = last_major, last_minor, last_patch + 1
    elif last_minor < MAX_MINOR:
        next_major, next_minor, next_patch = last_major, last_minor + 1, 0
    else:
        next_major, next_minor, next_patch = last_major + 1, 0, 0  # Major version increment

    return f"modern_analytics-{next_major}.{next_minor}.{next_patch}.exe"

def save_version(version):
    """Saves the current version number to a text file."""
    with open(VERSION_FILE, "w") as f:
        f.write(version)
    print(f"Saved version to {VERSION_FILE}: {version}")

def upload_file():
    """Uploads modern_analytics.exe with a versioned name."""
    folder_id = get_folder_id(FOLDER_NAME)
    new_filename = get_next_version(folder_id)

    file_metadata = {
        'title': new_filename,
        'parents': [{'id': folder_id}]
    }
    
    file = drive.CreateFile(file_metadata)
    file.SetContentFile("modern_analytics.exe")
    file.Upload()
    
    print(f"Uploaded as {new_filename}")

    # Save version to a text file
    save_version(new_filename.replace("modern_analytics-", "").replace(".exe", ""))

if __name__ == "__main__":
    upload_file()
