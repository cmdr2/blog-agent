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


def run(files, bucket, prefix="", **kwargs):
    """
    Uploads all files to S3 in a batch operation using threading for concurrent uploads.
    - files: A list of tuples - (file path, file contents)
    """

    bucket = bucket or S3_BUCKET
    prefix = prefix or S3_PREFIX

    if not bucket:
        print("Error: No S3 bucket configured!")
        return

    threads = []

    for path, content in files:
        t = threading.Thread(target=upload_file, args=(path, content, bucket, prefix))
        t.start()
        threads.append(t)

    if kwargs.get("wait_for_uploads", False):
        for t in threads:
            t.join()

    return threads


def upload_file(file_path, file_content, bucket, prefix):
    """
    Upload a single file to S3.
    """
    mime_type = guess_type(file_path)[0]

    key = prefix + "/" + file_path if prefix else file_path

    print("uploading", key, mime_type)
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=file_content.encode(),
        ContentType=mime_type,
        ACL="public-read",
    )
    print("uploaded", file_path)
