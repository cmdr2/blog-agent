def run(files, config={}):
    file_list = [process_file(filename, data) for filename, data in files]
    return file_list


def process_file(filename: str, data: tuple) -> list:
    post_time, tags, post_body = data
    post_id = filename.split("/")[-1]
    filepath = post_time.strftime("%Y-%m-%d") + "-" + post_id + ".md"

    hugo_content = format_hugo_content(post_id, post_time, tags, post_body)

    return filepath, hugo_content


def format_hugo_content(post_id, post_time, tags, post_body):
    # Format the date in ISO 8601 format for Hugo
    post_date_hugo = post_time.isoformat()

    # Format tags for Hugo's YAML front matter
    tags_yaml = ""
    if tags:
        # Remove leading '#' from tags
        formatted_tags = [tag[1:] for tag in tags]
        tags_yaml = "tags:\n" + "\n".join([f"  - {tag}" for tag in formatted_tags]) + "\n"

    # Construct the Hugo front matter
    front_matter = f"""---
title: "Post from {post_time.strftime('%b %d, %Y')}"
date: {post_date_hugo}
slug: {post_id}
{tags_yaml}---
"""

    # Combine front matter and post body
    hugo_content = front_matter + post_body

    return hugo_content
