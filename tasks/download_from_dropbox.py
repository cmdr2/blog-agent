import os
import io
import json
import http.client

DROPBOX_REFRESH_TOKEN = os.environ.get("DROPBOX_REFRESH_TOKEN", "your-dropbox-refresh-token")
DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY", "your-dropbox-app-key")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET", "your-dropbox-app-secret")
DROPBOX_FOLDER_PATH = os.environ.get("DROPBOX_FOLDER_PATH", "/your-journal-folder-in-dropbox/")


def run(data, **kwargs):
    # Step 1: Refresh the access token using the refresh token
    new_access_token = refresh_access_token()

    # Step 2: Use the new access token to download the zip
    dropbox_folder_path = ensure_slashes(DROPBOX_FOLDER_PATH, start=True, end=False)

    conn = http.client.HTTPSConnection("content.dropboxapi.com")
    body = json.dumps({"path": dropbox_folder_path})
    headers = {"Authorization": f"Bearer {new_access_token}", "Dropbox-API-Arg": body}

    conn.request("POST", "/2/files/download_zip", headers=headers, body=body)
    response = conn.getresponse()

    if response.status != 200:
        raise Exception(f"Dropbox API request failed with status {response.status}: {response.reason}")

    zip_data = response.read()
    return io.BytesIO(zip_data)


def refresh_access_token():
    """
    Requests a new access token from Dropbox using the refresh token.
    """
    conn = http.client.HTTPSConnection("api.dropbox.com")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    body = (
        f"grant_type=refresh_token&"
        f"refresh_token={DROPBOX_REFRESH_TOKEN}&"
        f"client_id={DROPBOX_APP_KEY}&"
        f"client_secret={DROPBOX_APP_SECRET}"
    )

    conn.request("POST", "/oauth2/token", body=body, headers=headers)
    response = conn.getresponse()

    if response.status != 200:
        raise Exception(f"Failed to refresh Dropbox access token: {response.status} {response.reason}")

    data = json.loads(response.read())
    return data["access_token"]


def ensure_slashes(path, start=True, end=True):
    """
    Ensures that the path contains or does not contain leading/trailing slashes as specified.
    - start: True if the path should start with a forward slash, False if it shouldn't.
    - end: True if the path should end with a forward slash, False if it shouldn't.
    """
    if start and not path.startswith("/"):
        path = "/" + path
    if not start and path.startswith("/"):
        path = path[1:]
    if end and not path.endswith("/"):
        path += "/"
    if not end and path.endswith("/"):
        path = path[:-1]
    return path
