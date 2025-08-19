def run(files, config={}):
    file_list = [process_file(filename, data) for filename, data in files]
    return file_list


def process_file(filename: str, data: tuple) -> list:
    post_time, tags, post_body, title = data
    post_id = filename.split("/")[-1]
    filepath = post_time.strftime("%Y-%m-%d") + "-" + post_id + ".md"

    mkdocs_content = format_mkdocs_content(post_id, post_time, tags, post_body, title)

    return filepath, mkdocs_content


def format_mkdocs_content(post_id, post_time, tags, post_body, title):
    post_date = post_time.strftime("%Y-%m-%d")

    # Format tags for MkDocs Material YAML front matter
    tags_yaml = ""
    if tags:
        formatted_tags = [tag[1:] for tag in tags]
        tags_yaml = "categories:\n" + "\n".join([f"  - {tag}" for tag in formatted_tags]) + "\n"

    title = title or f"Post from {post_time.strftime('%b %d, %Y')}"

    # Construct the MkDocs Material front matter
    front_matter = f"""---
title: "{title}"
date: {post_date}
slug: "{post_id}"
{tags_yaml}---
"""

    # Combine front matter and post body
    mkdocs_content = front_matter + post_body

    return mkdocs_content
