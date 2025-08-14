import os
import re
from datetime import datetime


def process_files(files, config={}):
    new_files = []

    for filename, file_contents in files:
        new_files += process_file(filename, file_contents, config)

    return new_files


def process_file(filename: str, file_contents: bytes, config: dict) -> list:
    dir_path = os.path.dirname(filename)
    name = os.path.basename(filename)
    name, ext = os.path.splitext(name)

    if ext.lower() != ".txt":
        return []

    file_contents = file_contents.decode()

    # Extract month and year from the filename
    month_name, year = name.split(" ")
    month_int = f"{['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].index(month_name[:3]) + 1:02}"

    # Split file contents into posts
    posts = re.split(r"\n\s*--\s*\n", file_contents.strip())

    # Create list for posts
    post_list = []
    for i, post in enumerate(posts):
        post = post.strip()
        if post:
            post_id, *data = process_post(post, config)
            key = f"{dir_path}/{year}/{month_int}/{post_id}"
            post_list.append((key, data))

    return post_list


def process_post(post_contents: str, config) -> str:
    # Split post contents into lines
    lines = post_contents.strip().splitlines()

    # Extract date and initialize variables
    post_date = lines[0]
    tags = []

    post_time = datetime.strptime(post_date, "%a %b %d %H:%M:%S %Y")
    post_id = int(post_time.timestamp())

    # Check for tags line
    if len(lines) > 2 and lines[2].startswith("#"):
        tags_line = lines[2]
        tags = tags_line.strip().split()  # Extract tags, including the leading '#'
        post_body = "\n".join(lines[3:]).strip()  # Post body starts from the fourth line
    else:
        post_body = "\n".join(lines[2:]).strip()  # Post body starts from the third line

    return post_id, post_time, tags, post_body
