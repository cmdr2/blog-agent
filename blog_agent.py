import os
import json
import http.client
import zipfile
import io
import importlib
import threading
from mimetypes import guess_type

from hashlib import sha256
import hmac

VALID_FILE_PROCESSORS = ("blog", "custom_cms", "passthrough")
FILE_INDEX_PATH = ".dropbox_index.json"

S3_BUCKET = os.environ.get("S3_BUCKET", "your-s3-bucket-name")
DROPBOX_REFRESH_TOKEN = os.environ.get("DROPBOX_REFRESH_TOKEN", "your-dropbox-refresh-token")
DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY", "your-dropbox-app-key")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET", "your-dropbox-app-secret")
DROPBOX_FOLDER_PATH = os.environ.get("DROPBOX_FOLDER_PATH", "/your-journal-folder-in-dropbox/")
S3_PREFIX = os.environ.get("S3_PREFIX", "public/path/in/s3/")

FILE_PROCESSORS = os.environ.get("FILE_PROCESSORS", "blog,custom_cms").split(",")
BLOG_TITLE = os.environ.get("BLOG_TITLE", "Blog")
BLOG_URL = os.environ.get("BLOG_URL", "https://your-blog-address.com")
BLOG_AUTHOR = os.environ.get("BLOG_AUTHOR")
BLOG_EMAIL = os.environ.get("BLOG_EMAIL")
SOCIAL_GITHUB_USERNAME = os.environ.get("SOCIAL_GITHUB_USERNAME")
SOCIAL_X_USERNAME = os.environ.get("SOCIAL_X_USERNAME")
SOCIAL_DISCORD_USERNAME = os.environ.get("SOCIAL_DISCORD_USERNAME")
BLOG_POSTS_PER_PAGE = int(os.environ.get("BLOG_POSTS_PER_PAGE", 20))

if set(FILE_PROCESSORS).difference(VALID_FILE_PROCESSORS):
    raise RuntimeError(f"Invalid FILE_PROCESSOR in config! Should be one of: {VALID_FILE_PROCESSORS}")

file_processors = [importlib.import_module("file_processors." + p) for p in FILE_PROCESSORS]

file_index = {}  # populated from S3


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
BLOG_URL = ensure_slashes(BLOG_URL, start=False, end=False)

s3_client = None
if "IS_LOCAL_TEST" not in os.environ:
    import boto3

    s3_client = boto3.client("s3")


def lambda_handler(event, context):
    global file_index

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

    # gather config
    config = {"blog_title": BLOG_TITLE, "blog_url": BLOG_URL, "blog_posts_per_page": BLOG_POSTS_PER_PAGE}
    if BLOG_AUTHOR:
        config["blog_author"] = BLOG_AUTHOR
    if BLOG_EMAIL:
        config["blog_email"] = BLOG_EMAIL
    if SOCIAL_DISCORD_USERNAME:
        config["social_discord_username"] = SOCIAL_DISCORD_USERNAME
    if SOCIAL_GITHUB_USERNAME:
        config["social_github_username"] = SOCIAL_GITHUB_USERNAME
    if SOCIAL_X_USERNAME:
        config["social_x_username"] = SOCIAL_X_USERNAME

    # Step 1: Get the file index from S3
    # file_index = get_json_file(FILE_INDEX_PATH)

    # Step 2: Download the journal folder as a zip file from Dropbox
    zip_data = download_journal_zip()

    # Step 3: Extract and copy files to S3
    zip_files_iterator = unzip_files(io.BytesIO(zip_data))
    file_list = get_file_list(zip_files_iterator, config)

    # Step 4: Set the new file_index
    # file_index_entry = (FILE_INDEX_PATH, json.dumps(file_index))
    # file_list.append(file_index_entry)

    # Step 5: Batch upload files to S3
    batch_upload_to_s3(file_list)

    return {"statusCode": 200, "body": "Publish successful!"}


def get_file_list(files_iterator, config={}):
    file_list = []

    for filename, content in files_iterator:
        file_list.append((filename, content))

    for file_processor in file_processors:
        print(file_processor)
        file_list = file_processor.process_files(file_list, config)

    return file_list


def download_journal_zip():
    # Step 1: Refresh the access token using the refresh token
    new_access_token = refresh_access_token()

    # Step 2: Use the new access token to download the zip
    conn = http.client.HTTPSConnection("content.dropboxapi.com")
    body = json.dumps({"path": DROPBOX_FOLDER_PATH})
    headers = {"Authorization": f"Bearer {new_access_token}", "Dropbox-API-Arg": body}

    conn.request("POST", "/2/files/download_zip", headers=headers, body=body)
    response = conn.getresponse()

    if response.status != 200:
        raise Exception(f"Dropbox API request failed with status {response.status}: {response.reason}")

    return response.read()


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


def unzip_files(zip_path):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        for file_info in zip_ref.infolist():
            file_name = file_info.filename

            # Read the modified timestamp as a tuple
            file_modified_time = file_info.date_time

            # Check if the file is in the file_index and its modified time
            last_modified = file_index.get(file_name)

            if last_modified is None or file_modified_time > tuple(last_modified):
                with zip_ref.open(file_info) as file:
                    yield file_name, file.read()

                # Update the file_index with the new modified time
                # file_index[file_name] = file_modified_time


def batch_upload_to_s3(file_list):
    """
    Uploads all files to S3 in a batch operation using threading for concurrent uploads.
    - file_list: A list of tuples - (S3 file path, file contents)
    """

    threads = []

    for path, content in file_list:
        t = threading.Thread(target=upload_file, args=(path, content))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


def upload_file(file_path, file_content):
    """
    Upload a single file to S3.
    """
    mime_type = guess_type(file_path)[0]

    key = S3_PREFIX + "/" + file_path if S3_PREFIX else file_path

    print("uploading", key, mime_type)
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=file_content.encode(),
        ContentType=mime_type,
        ACL="public-read",
    )
    print("uploaded", file_path)


def get_json_file(file_path):
    key = S3_PREFIX + "/" + file_path if S3_PREFIX else file_path

    try:
        print("fetching", key)
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
        data = response["Body"].read()
        return json.loads(data)
    except Exception as e:
        print(f"Error fetching JSON from S3: {e}")
        return {}
