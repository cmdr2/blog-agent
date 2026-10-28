def run(files, **kwargs):
    cms = kwargs.get("cms", "hugo")
    file_list = [process_file(filename, post, cms) for filename, post in files]
    return file_list


def process_file(filename: str, post, cms) -> list:
    filepath = post.time.strftime("%Y-%m-%d") + "-" + post.id + ".md"

    content = format_content(post, cms)

    return filepath, content


EXCERPT_MARKER = "<!-- more -->"


def format_content(post, cms):
    if cms == "hugo":
        tag_label, post_date = get_hugo_frontmatter(post.time)
    elif cms == "jekyll":
        tag_label, post_date = get_jekyll_frontmatter(post.time)
    elif cms == "mkdocs":
        tag_label, post_date = get_mkdocs_frontmatter(post.time)
    elif cms == "zensical":
        tag_label, post_date = get_zensical_frontmatter(post.time)
    else:
        raise ValueError(f"Unsupported CMS: {cms}")

    title = post.title or f"Post from {post.time.strftime('%b %d, %Y')}"

    front_matter = [
        f'title: "{title}"',
        f"date: {post_date}",
        f'slug: "{post.id}"',
    ]

    # Format tags for YAML front matter
    if post.tags:
        # Remove leading '#' from tags
        formatted_tags = [tag[1:] for tag in post.tags]
        tags_yaml = f"{tag_label}:\n" + "\n".join([f"  - {tag}" for tag in formatted_tags])
        front_matter.append(tags_yaml)

    if cms == "jekyll":
        front_matter.append("layout: post")

    # Construct the front matter
    front_matter = "\n".join(front_matter)
    front_matter = "---\n" + front_matter + "\n---\n"

    body = post.body
    if cms == "zensical":
        # Zensical renders the front matter title as the page heading, so drop
        # the duplicate H1 that split_blog_entries adds for explicit titles.
        body = remove_title_heading(body, post.title)
        # Zensical/Material's blog uses an explicit excerpt marker. Match the
        # existing posts on the site by placing it after the first paragraph.
        body = insert_excerpt_marker(body)

    # Combine front matter and post body
    content = front_matter + "\n" + body

    return content


def remove_title_heading(body, title):
    if not title:
        return body

    heading = f"# {title}"
    if body.startswith(heading) and body[len(heading) :][:1] in ("", "\n"):
        return body[len(heading) :].lstrip("\n")

    return body


def insert_excerpt_marker(body):
    if EXCERPT_MARKER in body:
        return body

    paragraphs = body.split("\n\n", 1)
    if len(paragraphs) == 1:
        return body

    return paragraphs[0] + "\n\n" + EXCERPT_MARKER + "\n\n" + paragraphs[1]


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


def get_zensical_frontmatter(post_time):
    # Zensical is Material for MkDocs under the hood, so posts use `categories`
    # (not Hugo's `tags`). The site's existing posts keep the full timestamp.
    return "categories", post_time.isoformat()
