def run(files, **kwargs):
    cms = kwargs.get("cms", "hugo")
    file_list = [process_file(filename, data, cms) for filename, data in files]
    return file_list


def process_file(filename: str, data: tuple, cms) -> list:
    post_time, tags, post_body, title = data
    post_id = filename.split("/")[-1]
    filepath = post_time.strftime("%Y-%m-%d") + "-" + post_id + ".md"

    content = format_content(post_id, post_time, tags, post_body, title, cms)

    return filepath, content


def format_content(post_id, post_time, tags, post_body, title, cms):
    if cms == "hugo":
        tag_label, post_date = get_hugo_frontmatter(post_time)
    elif cms == "jekyll":
        tag_label, post_date = get_jekyll_frontmatter(post_time)
    elif cms == "mkdocs":
        tag_label, post_date = get_mkdocs_frontmatter(post_time)
    else:
        raise ValueError(f"Unsupported CMS: {cms}")

    title = title or f"Post from {post_time.strftime('%b %d, %Y')}"

    front_matter = [
        f'title: "{title}"',
        f"date: {post_date}",
        f'slug: "{post_id}"',
    ]

    # Format tags for YAML front matter
    if tags:
        # Remove leading '#' from tags
        formatted_tags = [tag[1:] for tag in tags]
        tags_yaml = f"{tag_label}:\n" + "\n".join([f"  - {tag}" for tag in formatted_tags])
        front_matter.append(tags_yaml)

    if cms == "jekyll":
        front_matter.append("layout: post")

    # Construct the front matter
    front_matter = "\n".join(front_matter)
    front_matter = "---\n" + front_matter + "\n---\n"

    # Combine front matter and post body
    content = front_matter + "\n" + post_body

    return content


def get_hugo_frontmatter(post_time):
    return "tags", post_time.isoformat()


def get_jekyll_frontmatter(post_time):
    # Format the date for Jekyll's YYYY-MM-DD HH:MM:SS +/-TTTT format
    # Jekyll typically uses UTC or a specified timezone. For simplicity, we'll use UTC.
    post_date = post_time.strftime("%Y-%m-%d %H:%M:%S %z")
    if not post_date[-5:].startswith(("+", "-")):
        post_date += " +0000"  # Default to UTC if timezone info is missing

    return "tags", post_date


def get_mkdocs_frontmatter(post_time):
    return "categories", post_time.strftime("%Y-%m-%d")
