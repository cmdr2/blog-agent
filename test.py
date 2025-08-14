import os

os.environ["IS_LOCAL_TEST"] = "1"

from blog_agent import get_file_list

base_dir = "~/Dropbox/Apps/journal-public/"
base_dir = os.path.expanduser(base_dir)

files = []
for file in os.listdir(base_dir + "/notes"):
    if file.lower().endswith(".txt"):
        files.append(f"notes/{file}")

files_iterator = []
for file in files:
    with open(base_dir + "/" + file, "rb") as f:
        files_iterator.append((file, f.read()))

config = {
    "blog_title": "cmdr2's notes",
    "blog_url": "https://cmdr2.org",
    "blog_author": "cmdr2",
    "blog_email": "dev@cmdr2.org",
    "social_github_username": "cmdr2",
    "social_discord_username": "cmdr2",
    "social_x_username": "cmdr2",
    "blog_posts_per_page": 10,
}

d = get_file_list(files_iterator, config)

for file_path, content in d:
    out_path = f"tmp/{file_path}"

    dir_name = os.path.dirname(out_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    with open(out_path, "w") as f2:
        print(out_path, len(content), "bytes")
        f2.write(content)
