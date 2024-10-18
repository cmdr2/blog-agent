"Splits the text file into separate posts (one file per post), and formats each post using markdown"

import os
import re
from .markdown_to_html import MarkdownToHtmlConverter


def process_file(filename: str, file_contents: str) -> dict:
    dir_path = os.path.dirname(filename)
    name = os.path.basename(filename)
    name, ext = os.path.splitext(name)

    if ext.lower() != ".txt":
        return

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

    dir_name = os.path.dirname(__file__)
    styles_path = os.path.join(dir_name, "styles.css")

    with open(styles_path, "r") as f:
        post_dict[f"{dir_path}/styles.css"] = f.read()

    print(post_dict.keys())

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
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="../../styles.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-okaidia.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
    <title>Post</title>
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