import os
import json
import http.client
import zipfile
import io
import boto3

from hashlib import sha256
import hmac

S3_BUCKET = os.environ.get("S3_BUCKET", "your-s3-bucket-name")
DROPBOX_TOKEN = os.environ.get("DROPBOX_TOKEN", "your-dropbox-access-token")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET", "your-dropbox-app-secret")
DROPBOX_FOLDER_PATH = os.environ.get("DROPBOX_FOLDER_PATH", "/your-journal-folder-in-dropbox/")
S3_PREFIX = os.environ.get("S3_PREFIX", "public/path/in/s3/")


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


DROPBOX_FOLDER_PATH = ensure_slashes(DROPBOX_FOLDER_PATH, start=True, end=False)
S3_PREFIX = ensure_slashes(S3_PREFIX, start=False, end=False)

s3_client = boto3.client("s3")


def lambda_handler(event, context):
    print(event)
    print(context)
    httpMethod = event["requestContext"]["http"]["method"]
    queryParams = event.get("queryStringParameters", {})
    # Check for Dropbox challenge verification request
    if httpMethod == "GET" and "challenge" in queryParams:
        return {
            "statusCode": 200,
            "body": queryParams["challenge"],
            "headers": {"Content-Type": "text/plain", "X-Content-Type-Options": "nosniff"},
        }

    # Make sure this is a valid request from Dropbox
    signature = event["headers"].get("x-dropbox-signature")
    if httpMethod != "POST" or not hmac.compare_digest(
        signature, hmac.new(DROPBOX_APP_SECRET.encode(), event.get("body", "").encode(), sha256).hexdigest()
    ):
        print("Invalid signature")
        return {"statusCode": 404, "body": "Not found"}

    # Step 1: Download the journal folder as a zip file from Dropbox
    zip_data = download_journal_zip()

    # Step 2: Extract and copy files to S3
    with zipfile.ZipFile(io.BytesIO(zip_data), "r") as zip_ref:
        for file_info in zip_ref.infolist():
            with zip_ref.open(file_info.filename) as file:
                # Step 3: Upload files to S3
                s3_key = S3_PREFIX + "/" + file_info.filename
                upload_to_s3(s3_key, file.read())

    return {"statusCode": 200, "body": "Publish successful!"}


def download_journal_zip():
    conn = http.client.HTTPSConnection("content.dropboxapi.com")
    body = json.dumps({"path": DROPBOX_FOLDER_PATH})
    headers = {"Authorization": f"Bearer {DROPBOX_TOKEN}", "Dropbox-API-Arg": body}

    print("request", body)

    conn.request("POST", "/2/files/download_zip", headers=headers, body=body)
    response = conn.getresponse()

    if response.status != 200:
        raise Exception(f"Dropbox API request failed with status {response.status}: {response.reason}")

    return response.read()


def upload_to_s3(key, content):
    s3_client.put_object(Bucket=S3_BUCKET, Key=key, Body=content, ACL="public-read")
