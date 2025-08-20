import os
import re
from datetime import datetime


def run(files, **kwargs):
    "Returns a list of tuples. Each tuple is (filename, (post_time, tags, post_body, title))"

    new_files = []

    for filename, file_contents in files:
        new_files += process_file(filename, file_contents)

    return new_files


def process_file(filename: str, file_contents: bytes) -> list:
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
            post_id, *data = process_post(post)
            key = f"{dir_path}/{year}/{month_int}/{post_id}"
            post_list.append((key, data))

    return post_list


def process_post(post_contents: str) -> str:
    # Split post contents into lines
    lines = post_contents.strip().splitlines()

    # Extract date and initialize variables
    post_date = lines[0]
    tags = []

    post_time = datetime.strptime(post_date, "%a %b %d %H:%M:%S %Y")
    post_id = int(post_time.timestamp())

    # Initialize variables
    tags = []
    title = None

    # Parse lines for tags and title
    idx = 1
    while idx < len(lines):
        line = lines[idx].strip()
        if not line:
            idx += 1
            continue
        # Only accept lines that start with '#' immediately followed by non-space text
        if re.match(r"^#\S+", line):
            tags += [tag for tag in line.split()]
            idx += 1
            continue
        if line.startswith("Title: "):
            title = line[len("Title: ") :].strip()
            idx += 1
            continue
        if line.startswith("Slug: "):
            post_id = line[len("Slug: ") :].strip()
            idx += 1
            continue
        # First non-tag/title/slug line is the start of the body
        break

    # Remaining lines are the post body
    post_body = "\n".join(lines[idx:]).strip()

    if title:
        post_body = f"# {title}\n\n{post_body}"

    return post_id, post_time, tags, post_body, title
