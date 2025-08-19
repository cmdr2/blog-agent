def run(files, config={}):
    file_list = [process_file(filename, data) for filename, data in files]
    return file_list


def process_file(filename: str, data: tuple) -> list:
    post_time, tags, post_body = data
    post_id = filename.split("/")[-1]
    filepath = post_time.strftime("%Y-%m-%d") + "-" + post_id + ".md"

    jekyll_content = format_jekyll_content(post_id, post_time, tags, post_body)

    return filepath, jekyll_content


def format_jekyll_content(post_id, post_time, tags, post_body):
    # Format the date for Jekyll's YYYY-MM-DD HH:MM:SS +/-TTTT format
    # Jekyll typically uses UTC or a specified timezone. For simplicity, we'll use UTC.
    post_date_jekyll = post_time.strftime("%Y-%m-%d %H:%M:%S %z")
    if not post_date_jekyll[-5:].startswith(("+", "-")):
        post_date_jekyll += " +0000"  # Default to UTC if timezone info is missing

    # Format tags for Jekyll's YAML front matter
    tags_yaml = ""
    if tags:
        # Remove leading '#' from tags and join them with commas
        formatted_tags = [tag[1:] for tag in tags]
        tags_yaml = f"tags: [{', '.join(formatted_tags)}]\n"

    # Construct the Jekyll front matter
    front_matter = f"""---
layout: post
title: "Post from {post_time.strftime('%b %d, %Y')}"
date: {post_date_jekyll}
slug: {post_id}
{tags_yaml}---

"""

    # Combine front matter and post body
    jekyll_content = front_matter + post_body

    return jekyll_content
