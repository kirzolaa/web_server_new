from google_auth_oauthlib.flow import InstalledAppFlow

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

# Run the OAuth2 flow
flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json', SCOPES
)
creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')

# Save the credentials (including the refresh token) to a file
with open('token.json', 'w') as token:
    token.write(creds.to_json())