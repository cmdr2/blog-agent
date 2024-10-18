# blog-agent
Publish a blog to S3 automatically using text files in Dropbox.

**Tip:** If you save very frequently while writing text files (like I do), consider pausing Dropbox sync while you write and resuming after you've finished editing. This will avoid frequent republishes and Lambda calls.

## Configure
### Step 1: Create a Dropbox access token
1. Open the [Dropbox Apps Console](https://www.dropbox.com/developers/apps/).
2. Create a new app. Choose `Scoped access`, then `App folder` and then give it any name, like `blog-agent`.
3. Set the folder name to whatever you want. **Note:** This will always be *inside* the `/Apps` folder in Dropbox!
4. Click `Generate Access Token` and copy the generated token. Keep this safely, we'll need it later.
5. Also copy the `App Secret` and keep it safely for later.
6. Open the `Permissions` tab, and enable `files.content.read` and press `Save`.


### Step 2: Create an AWS Lambda function
You have two options for this step: an [automated script](create_lambda.py) or a manual approach. I recommend the automated script.

#### Option 1: Automated script
The [automated script](create_lambda.py) will create the Lambda function, IAM Roles, Permission Policies and link them together.

1. Ensure that you have the [AWS CLI](https://aws.amazon.com/cli/) installed and configured correctly.
2. Run `python create_lambda.py`. Enter the desired Lambda function name, e.g. 'blog-agent', the S3 bucket name, the S3 folder path, and the Dropbox folder name inside `/Apps/app-folder`
3. **Important:** Note down the function URL printed at the end.
4. Finally, open the lambda function in the AWS Console, open `Configuration` > `Environment Variables`, and set the `DROPBOX_TOKEN` and `DROPBOX_APP_SECRET` environment variables.

`DROPBOX_TOKEN` is the access token created in your Dropbox App Console. `DROPBOX_APP_SECRET` is the app secret copied from your Dropbox App Console.

#### Option 2: Manual approach
You can also do these steps manually, if you'd prefer.

Create a Lambda function with the latest Python runtime, HTTP Function URL, and no authentication. Then create the necessary IAM Roles to allow it to read buckets, read object and write object to the desired S3 Bucket at the desired S3 folder path.

Then set the following environment variables on the Lambda function in the AWS Console: `S3_BUCKET`, `S3_PREFIX`, `DROPBOX_FOLDER_PATH`, `DROPBOX_TOKEN` and `DROPBOX_APP_SECRET`.

`DROPBOX_TOKEN` is the access token created in your Dropbox App Console. `DROPBOX_APP_SECRET` is the app secret copied from your Dropbox App Console.


### Step 3: Configure the Dropbox webhook
1. Open the [Dropbox Apps Console](https://www.dropbox.com/developers/apps/), and open your app inside that.
2. Under the `Settings` tab, scroll down to the `Webhooks` entry, and set the newly created function's URL and press `Save`.
