import os
import subprocess
import json
import re
import time

FUNCTION_FILE = "blog_agent.py"


def create_lambda_function(lambda_name, s3_bucket, s3_prefix, dropbox_folder_path):
    # Get AWS account ID
    account_id = get_account_id()

    print("Creating a role for Lambda with the necessary permissions..")
    role_name = f"{lambda_name}_role"
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}
        ],
    }

    trust_policy_json = json.dumps(trust_policy)
    create_role_command = [
        "aws",
        "iam",
        "create-role",
        "--role-name",
        role_name,
        "--assume-role-policy-document",
        trust_policy_json,
    ]
    subprocess.run(create_role_command, check=True)

    print("Waiting for the role to be created..")
    time.sleep(5)

    print("Attaching CloudWatch Logs permission policies to the role..")
    attach_basic_policy_command = [
        "aws",
        "iam",
        "attach-role-policy",
        "--role-name",
        role_name,
        "--policy-arn",
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    ]
    subprocess.run(attach_basic_policy_command, check=True)

    print("Attaching S3 permission policies to the role..")
    s3_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:ListBucket", "s3:GetObject", "s3:PutObject", "s3:PutObjectAcl"],
                "Resource": [f"arn:aws:s3:::{s3_bucket}", f"arn:aws:s3:::{s3_bucket}/{s3_prefix}/*"],
            }
        ],
    }

    s3_policy_json = json.dumps(s3_policy)
    policy_name = f"{lambda_name}_s3_policy"
    create_policy_command = [
        "aws",
        "iam",
        "create-policy",
        "--policy-name",
        policy_name,
        "--policy-document",
        s3_policy_json,
    ]
    subprocess.run(create_policy_command, check=True)

    print("Waiting for the policy to be attached..")
    time.sleep(5)

    attach_policy_command = [
        "aws",
        "iam",
        "attach-role-policy",
        "--role-name",
        role_name,
        "--policy-arn",
        f"arn:aws:iam::{account_id}:policy/{policy_name}",
    ]
    subprocess.run(attach_policy_command, check=True)

    # Set environment variables
    environment_vars = {
        "Variables": {"S3_BUCKET": s3_bucket, "S3_PREFIX": s3_prefix, "DROPBOX_FOLDER_PATH": dropbox_folder_path}
    }

    print(f"Creating the Lambda function from {FUNCTION_FILE}..")
    function_name = os.path.splitext(FUNCTION_FILE)[0]

    create_lambda_command = [
        "aws",
        "lambda",
        "create-function",
        "--function-name",
        lambda_name,
        "--runtime",
        "python3.12",
        "--role",
        f"arn:aws:iam::{account_id}:role/{role_name}",
        "--handler",
        f"{function_name}.lambda_handler",
        "--zip-file",
        "fileb://function.zip",
        "--environment",
        json.dumps(environment_vars),
    ]

    # Zip the function file
    subprocess.run(["zip", "function.zip", FUNCTION_FILE], check=True)

    subprocess.run(create_lambda_command, check=True)

    print("Enabling the function URL..")
    create_url_command = [
        "aws",
        "lambda",
        "create-function-url-config",
        "--function-name",
        lambda_name,
        "--auth-type",
        "NONE",
    ]
    subprocess.run(create_url_command, check=True)

    # Wait for the function URL to be created
    time.sleep(5)

    print("Adding policy for public access..")
    add_policy_command = [
        "aws",
        "lambda",
        "add-permission",
        "--function-name",
        lambda_name,
        "--statement-id",
        "PublicAccess",
        "--action",
        "lambda:InvokeFunctionUrl",
        "--principal",
        "*",
        "--function-url-auth-type",
        "NONE",
    ]
    subprocess.run(add_policy_command, check=True)

    # Get the function URL
    get_url_command = ["aws", "lambda", "get-function-url-config", "--function-name", lambda_name]
    result = subprocess.run(get_url_command, check=True, capture_output=True)
    url = json.loads(result.stdout)["FunctionUrl"]

    print("Success!")
    print("")

    print(f"Lambda function URL: {url}")
    print("")

    return url


def get_account_id():
    # Fetch the AWS account ID
    result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


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


def validate_lambda_name(lambda_name):
    # Check if the name is 1 to 64 characters long
    if len(lambda_name) < 1 or len(lambda_name) > 64:
        return False

    # Check if the name contains only valid characters
    if not re.match(r"^[a-zA-Z0-9_-]+$", lambda_name):
        return False

    return True


if __name__ == "__main__":
    lambda_name = input("Enter the Lambda function name: ")
    s3_bucket = input("Enter the S3 bucket name: ")
    s3_prefix = input("Enter the S3 path prefix: ")
    dropbox_folder_path = input("Enter the Dropbox folder path (do *not* include /Apps/blog-agent at the start): ")

    if not validate_lambda_name(lambda_name):
        raise RuntimeError(
            "Function name must be 1 to 64 characters, must be unique to the Region, and can't include spaces. Valid characters are a-z, A-Z, 0-9, hyphens (-), and underscores (_)."
        )

    dropbox_folder_path = ensure_slashes(dropbox_folder_path, start=True, end=False)
    s3_prefix = ensure_slashes(s3_prefix, start=False, end=False)

    url = create_lambda_function(lambda_name, s3_bucket, s3_prefix, dropbox_folder_path)

    print(
        f"""Next steps:
1. Please open the lambda function in the AWS Console, and set these environment variables:
 a. DROPBOX_TOKEN as the access token created in your Dropbox App Console.
 b. DROPBOX_APP_SECRET as the app secret copied from your Dropbox App Console.

2. Please open the Dropbox app console, and set this URL as the webhook: {url}
"""
    )
