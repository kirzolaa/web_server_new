import re
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config_setting.py')
MAX_MINOR = 5
MAX_PATCH = 3

def update_version():
    with open(CONFIG_FILE, 'r') as f:
        content = f.read()
    
    # Find current version
    version_match = re.search(r'VERSION\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
    if not version_match:
        print("Could not find version in config_setting.py")
        return False
    
    major, minor, patch = map(int, version_match.groups())
    
    # Increment version following niceversion logic
    if patch < MAX_PATCH:
        next_major, next_minor, next_patch = major, minor, patch + 1
    elif minor < MAX_MINOR:
        next_major, next_minor, next_patch = major, minor + 1, 0
    else:
        next_major, next_minor, next_patch = major + 1, 0, 0
    
    new_version = f'{next_major}.{next_minor}.{next_patch}'
    
    # Update version in file
    new_content = re.sub(
        r'(VERSION\s*=\s*)"[\d\.]+"',
        f'\\1"{new_version}"',
        content
    )
    
    with open(CONFIG_FILE, 'w') as f:
        f.write(new_content)
    
    print(f"Updated version to {new_version}")
    return True

if __name__ == '__main__':
    update_version()
