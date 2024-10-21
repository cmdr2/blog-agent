"Splits the text file into separate posts (one file per post), and formats each post using markdown"

import os
import re
import time
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from .markdown_to_html import MarkdownToHtmlConverter

HEAD = """
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-okaidia.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@300..700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <title>Post</title>
"""


def process_files(file_iterator, config={}):
    file_dict = {}
    dir_name = os.path.dirname(__file__)

    # process the text files
    for filename, content in file_iterator:
        files = process_file(filename, content, config)
        if files:
            file_dict.update(files)

    # generate index.html and atom.xml
    atom_xml = generate_atom_feed(file_dict, config)
    index_html = generate_index(file_dict, config)

    # include index.html and atom.xml
    file_dict["index.html"] = index_html
    file_dict["atom.xml"] = atom_xml

    # flatten the content
    file_dict = {k: v[0] for k, v in file_dict.items()}

    # include styles.css
    styles_path = os.path.join(dir_name, "styles.css")
    with open(styles_path, "r") as f:
        file_dict[f"styles.css"] = f.read()

    print(file_dict.keys())

    return file_dict


def process_file(filename: str, file_contents: bytes, config: dict) -> dict:
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
            post_id, *data = process_post(post, config)
            key = f"{dir_path}/{year}/{month_int}/{post_id}.html"
            post_dict[key] = data

    return post_dict


def process_post(post_contents: str, config) -> str:
    md_to_html = MarkdownToHtmlConverter()

    # Split post contents into lines
    lines = post_contents.strip().splitlines()

    # Extract date and initialize variables
    post_date = lines[0]
    tags = []

    blog_title = config.get("blog_title", "Blog")
    post_id = sha256_hash(post_date)[:16]

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

    t = time.time()

    # Construct the HTML file
    article_html = f"""
    <article class="post">
        <time class="date">{post_date}</time>
        {tags_html}
        {html_body}
    </article>
"""

    # social
    social_links, social_footer, social_script_tag = get_social_content(config)

    if social_footer:
        social_footer = "<footer>" + social_footer + "</footer>"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
{HEAD}
    <link rel="stylesheet" href="../../../styles.css?v={t}">
    <link rel="alternate" type="application/atom+xml" href="../../../atom.xml" title="Your Blog Title">
</head>
<body>
    <header>
        <h1>
            <a href="../../../index.html">{blog_title}</a>{social_links}
        </h1>
    </header>
    <script>
        Prism.plugins.autoloader.languages_path = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/';
    </script>
    {article_html}

    {social_footer}

    {social_script_tag}
</body>
</html>
"""
    return post_id, html_content, article_html, post_date


def generate_index(file_dict, config):
    filenames = list(file_dict.keys())
    filenames.reverse()

    t = time.time()
    blog_title = config.get("blog_title", "Blog")

    post_list = []
    for filename in filenames:
        # for filename, content in file_dict.items():
        content = file_dict[filename]
        article_html = content[1]
        article_html = article_html.replace('<time class="date">', f'<time class="date"><a href="{filename}">')
        article_html = article_html.replace("</time>", "</a></time>")

        post_list.append(f"{article_html}")

    posts_html = "\n        ".join(post_list)

    format_entries_html = """
    <script>
        document.addEventListener("DOMContentLoaded", function() {
            document.querySelectorAll('.post_list article').forEach(article => {
                const computedStyle = window.getComputedStyle(article)
                const maxHeight = parseInt(computedStyle.maxHeight, 10) + 100

                // Check if content fits within the max height
                if (article.scrollHeight > maxHeight) {
                    // Create a "more..." link
                    const postUrl = article.querySelector('.date a').getAttribute('href')
                    const moreLink = document.createElement('a')
                    moreLink.textContent = 'more...'
                    moreLink.href = postUrl
                    moreLink.classList.add('more-link')

                    // Append the "more..." link to the article
                    article.appendChild(moreLink)
                } else {
                    // Remove fade and "more..." link if not overflowing
                    article.classList.add('no-overflow')
                }
            });
        });
    </script>
"""

    # social
    social_links, social_footer, social_script_tag = get_social_content(config)

    if social_footer:
        social_footer = "<footer>" + social_footer + "</footer>"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
{HEAD}
    <link rel="stylesheet" href="styles.css?v={t}">
    <link rel="alternate" type="application/atom+xml" href="atom.xml" title="Your Blog Title">
</head>
<body>
    <header>
        <h1>
            {blog_title}{social_links}
        </h1>
    </header>
    
    <script>
        Prism.plugins.autoloader.languages_path = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/';
    </script>
    <div class="post_list">
    {posts_html}
    </div>

    {format_entries_html}

    {social_footer}

    {social_script_tag}
</body>
</html>
"""

    return html_content, "", ""


def generate_atom_feed(file_dict, config):
    # Create the root feed element
    feed = ET.Element("feed", xmlns="http://www.w3.org/2005/Atom")

    # Feed title
    title = ET.SubElement(feed, "title")
    title.text = config.get("blog_title", "Your Feed Title")

    # Link element
    feed_link = config.get("blog_url", "https://yourwebsite.com")
    link = ET.SubElement(feed, "link", href=f"{feed_link}/atom.xml", rel="self")

    # Feed id
    feed_id = ET.SubElement(feed, "id")
    feed_id.text = feed_link

    # Updated element with the current time
    updated = ET.SubElement(feed, "updated")
    updated.text = datetime.now(timezone.utc).isoformat()

    # Author element
    if "blog_author" in config or "blog_email" in config:
        author = ET.SubElement(feed, "author")

        if "blog_author" in config:
            name = ET.SubElement(author, "name")
            name.text = config["blog_author"]

        if "blog_email" in config:
            email = ET.SubElement(author, "email")
            email.text = config["blog_email"]

    # Create entries for each article
    for filename, content in file_dict.items():
        _, article_content, article_date_str = content
        article_link = feed_link + "/" + filename

        # Parse the date string into a datetime object
        article_date = datetime.strptime(article_date_str, "%a %b %d %H:%M:%S %Y")

        # Convert to ISO 8601 format
        article_date_iso = article_date.isoformat() + "Z"

        entry = ET.SubElement(feed, "entry")

        # Generate a unique ID for each article
        entry_id = ET.SubElement(entry, "id")
        entry_id.text = article_link

        # Title can be derived from the article date
        entry_title = ET.SubElement(entry, "title")
        entry_title.text = f"Post from {article_date_str}"

        # Link element for the article
        entry_link = ET.SubElement(entry, "link", href=article_link)

        # Updated date for the entry
        entry_updated = ET.SubElement(entry, "updated")
        entry_updated.text = article_date_iso

        # Summary (content) of the article
        summary = ET.SubElement(entry, "summary")
        summary.text = article_content

    # Convert the feed element to a string
    feed_xml = ET.tostring(feed, encoding="unicode", method="xml")

    return feed_xml, "", ""


def sha256_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def get_social_content(config):
    social_x = config.get("social_x_username")
    social_github = config.get("social_github_username")
    social_discord = config.get("social_discord_username")

    social_script_tag = ""
    social_links = ""
    social_footer = []
    if social_discord:
        social_script_tag += (
            """
        <script>
            const links = document.querySelectorAll('.discord-link')
            links.forEach(link => {
                link.addEventListener('click', function(event) {
                    event.preventDefault(); // Prevent the default link behavior
                    alert('"""
            + social_discord
            + """ is the discord username'); // Show the alert
                });
            })
        </script>
    """
        )

    if social_x or social_discord or social_github:
        if social_github:
            social_links += f"""
            <a href="https://github.com/{social_github}" target="_blank" class="social-icon">
                <i class="fab fa-github"></i>
            </a>"""

            social_footer.append(
                f"""
            <a href="https://github.com/{social_github}" target="_blank">
                [github]
            </a>"""
            )
        if social_x:
            social_links += f"""
            <a href="https://x.com/{social_x}" target="_blank" class="social-icon">
                <i class="fab fa-x"></i>
            </a>"""

            social_footer.append(
                f"""
            <a href="https://x.com/{social_x}" target="_blank">
                [x]
            </a>"""
            )
        if social_discord:
            social_links += f"""
            <a href="#" class="social-icon discord-link" target="_blank">
                <i class="fab fa-discord"></i>
            </a>"""

            social_footer.append(
                f"""
            <a href="#" class="discord-link" target="_blank">
                [discord]
            </a>"""
            )

    return social_links, "".join(social_footer), social_script_tag
