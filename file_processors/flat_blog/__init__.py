"Splits the text file into separate posts (one file per post), and formats each post using markdown"

import os
import re
from .markdown_to_html import MarkdownToHtmlConverter

HEAD = """
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-okaidia.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
    <title>Post</title>
"""

def process_files(file_iterator):
    file_dict = {}
    dir_name = os.path.dirname(__file__)

    # process the text files
    for filename, content in file_iterator:
        files = process_file(filename, content)
        if files:
            file_dict.update(files)

    # include index.html
    file_dict["index.html"] = generate_index(file_dict)

    # include styles.css
    styles_path = os.path.join(dir_name, "styles.css")
    with open(styles_path, "r") as f:
        file_dict[f"styles.css"] = f.read()

    print(file_dict.keys())

    return file_dict


def process_file(filename: str, file_contents: bytes) -> dict:
    dir_path = os.path.dirname(filename)
    name = os.path.basename(filename)
    name, ext = os.path.splitext(name)

    if ext.lower() != ".txt":
        return

    file_contents = file_contents.decode()

    # Extract month and year from the filename
    month_name, year = name.split(" ")
    month_int = f"{['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].index(month_name[:3]) + 1:02}"

    # Split file contents into posts
    posts = re.split(r"\n\s*--\s*\n", file_contents.strip())

    # Create dictionary for posts
    post_dict = {}
    for i, post in enumerate(posts):
        post = post.strip()
        if post:
            post_id = str(i)  # str(uuid.uuid4())
            key = f"{dir_path}/{year}/{month_int}/{post_id}.html"
            post_dict[key] = process_post(post)

    return post_dict


def process_post(post_contents: str) -> str:
    md_to_html = MarkdownToHtmlConverter()

    # Split post contents into lines
    lines = post_contents.strip().splitlines()

    # Extract date and initialize variables
    post_date = lines[0]
    tags = []

    # Check for tags line
    if len(lines) > 2 and lines[2].startswith("#"):
        tags_line = lines[2]
        tags = tags_line.strip().split()  # Extract tags, including the leading '#'
        post_body = "\n".join(lines[3:]).strip()  # Post body starts from the fourth line
    else:
        post_body = "\n".join(lines[2:]).strip()  # Post body starts from the third line

    # Convert post body from markdown to HTML
    html_body = md_to_html.convert(post_body)

    # Process tags into HTML, including leading '#'
    tags_html = (
        '<ul class="tags">' + "".join(f'<li class="tag">{tag[1:]}</li>' for tag in tags) + "</ul>" if tags else ""
    )

    # Construct the HTML file
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
{HEAD}
    <link rel="stylesheet" href="../../../styles.css">
</head>
<body>
    <script>
        Prism.plugins.autoloader.languages_path = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/';
    </script>
    <article class="post">
        <time class="date">{post_date}</time>
        {tags_html}
        {html_body}
    </article>
</body>
</html>
"""
    return html_content


def generate_index(file_dict):
    post_list = []
    for filename in file_dict.keys():
        post_list.append(f'<li><a href="{filename}">{filename}</a></li>')

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
{HEAD}
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <script>
        Prism.plugins.autoloader.languages_path = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/';
    </script>
    <ul id="posts">
        {"\n        ".join(post_list)}
    </ul>
</body>
</html>
"""

    return html_content
