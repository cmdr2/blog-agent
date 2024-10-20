import webbrowser
import http.client
import urllib.parse
import getpass
import time
import base64
import json

# Get user input for App Key
app_key = input("Enter your App Key: ")

# Open the authorization URL in the browser
auth_url = f"https://www.dropbox.com/oauth2/authorize?client_id={app_key}&response_type=code&token_access_type=offline"
print(f"Opening URL: {auth_url}")
try:
    webbrowser.open(auth_url)
except:
    pass

time.sleep(2)

# Get the Authorization Code and App Secret from the user
auth_code = input("Enter the Authorization Code: ")
app_secret = getpass.getpass("Enter your App Secret (input will be hidden): ")

# Prepare the HTTP request to exchange the authorization code for an access token and refresh token
conn = http.client.HTTPSConnection("api.dropbox.com")

# Encode the App Key and App Secret as base64 for basic authentication
auth = f"{app_key}:{app_secret}"
auth_encoded = base64.b64encode(auth.encode()).decode()

headers = {"Authorization": f"Basic {auth_encoded}", "Content-Type": "application/x-www-form-urlencoded"}

params = urllib.parse.urlencode({"code": auth_code, "grant_type": "authorization_code"})

# Make the HTTP request
conn.request("POST", "/oauth2/token", params, headers)

# Get the response
response = conn.getresponse()
data = response.read().decode()

# Parse and print the refresh token from the response
tokens = json.loads(data)
refresh_token = tokens.get("refresh_token")

if refresh_token:
    print("Refresh Token:", refresh_token)
    print("Next step: Set this refresh token as the DROPBOX_REFRESH_TOKEN environment variable in your Lambda function")
else:
    print("Failed to retrieve tokens.")

conn.close()
