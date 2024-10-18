import os
import subprocess
import json

from create_lambda import validate_lambda_name, zip_lambda_files, save_blog_info, BLOG_INFO_DOTFILE


def update_lambda_function(function_name):
    # Zip the files
    zip_file_name = zip_lambda_files()

    # Upload the zip file to the specified Lambda function
    try:
        subprocess.run(
            [
                "aws",
                "lambda",
                "update-function-code",
                "--function-name",
                function_name,
                "--zip-file",
                f"fileb://{zip_file_name}",
            ],
            check=True,
        )

        print(f"Successfully updated the Lambda function: {function_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error updating Lambda function: {e}")


if __name__ == "__main__":
    if os.path.exists(BLOG_INFO_DOTFILE):
        with open(BLOG_INFO_DOTFILE, "r") as f:
            blog_info = json.load(f)
            function_name = blog_info["lambda_function_name"]
    else:
        # Get the Lambda function name from user input
        function_name = input("Enter the Lambda function name: ")

        # Validate the Lambda function name
        if not validate_lambda_name(function_name):
            raise ValueError(
                "Invalid Lambda function name. Must be 1-64 characters long, and can only contain a-z, A-Z, 0-9, hyphens (-), and underscores (_)."
            )

        save_blog_info({"lambda_function_name": function_name})

    # Update the Lambda function with the new code
    update_lambda_function(function_name)
