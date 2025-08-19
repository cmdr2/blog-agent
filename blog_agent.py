import os
import hmac
from hashlib import sha256

import workflow

DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET", "your-dropbox-app-secret")


def lambda_handler(event, context):
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

    # Run the workflow
    workflow.run()

    return {"statusCode": 200, "body": "Publish successful!"}
