import os
import threading
from mimetypes import guess_type


S3_BUCKET = os.environ.get("S3_BUCKET")  # "your-s3-bucket-name"
S3_PREFIX = os.environ.get("S3_PREFIX", "")  # "public/path/in/s3/"

S3_PREFIX = S3_PREFIX.strip("/")

s3_client = None
if "IS_LOCAL_TEST" not in os.environ:
    import boto3

    s3_client = boto3.client("s3")


def run(files, config={}):
    """
    Uploads all files to S3 in a batch operation using threading for concurrent uploads.
    - files: A list of tuples - (file path, file contents)
    """

    config["s3_bucket"] = config.get("s3_bucket") or S3_BUCKET
    config["s3_prefix"] = config.get("s3_prefix") or S3_PREFIX

    if not config["s3_bucket"]:
        print("Error: No S3 bucket configured!")
        return

    threads = []

    for path, content in files:
        t = threading.Thread(target=upload_file, args=(path, content, config))
        t.start()
        threads.append(t)

    if config.get("wait_for_uploads", False):
        for t in threads:
            t.join()

    return threads


def upload_file(file_path, file_content, config):
    """
    Upload a single file to S3.
    """
    mime_type = guess_type(file_path)[0]

    key = config["s3_prefix"] + "/" + file_path if config["s3_prefix"] else file_path

    print("uploading", key, mime_type)
    s3_client.put_object(
        Bucket=config["s3_bucket"],
        Key=key,
        Body=file_content.encode(),
        ContentType=mime_type,
        ACL="public-read",
    )
    print("uploaded", file_path)
