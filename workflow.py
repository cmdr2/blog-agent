import os

from tasks import (
    download_from_dropbox,
    unzip_files,
    split_blog_entries,
)
from tasks.convert_to_frontmatter import run as convert_to_frontmatter
from tasks.publish_to_github import run as publish_to_github
from liteflow import run as _run

from functools import partial
from dataclasses import replace

EASY_DIFFUSION_GH_CONFIG = {
    "owner": "easydiffusion",
    "repo": "easydiffusion.github.io",
    "branch": "main",
    "prefix": "content/blog",
    "token": os.environ.get("EASYDIFFUSION_BLOG_GITHUB_TOKEN"),
}
FREEBIRD_GH_CONFIG = {
    "owner": "freebirdxr",
    "repo": "freebird-website",
    "branch": "main",
    "prefix": "docs/blog/posts",
    "token": os.environ.get("FREEBIRD_BLOG_GITHUB_TOKEN"),
}
CMDR2_BLOG_GH_CONFIG = {
    "owner": "cmdr2",
    "repo": "cmdr2.github.io",
    "branch": "main",
    "prefix": "content/posts",
    "token": os.environ.get("CMDR2_BLOG_GITHUB_TOKEN"),
}


def classify_posts_by_project(files):
    for _, post in files:
        post.project = None
        if "#easydiffusion" in post.tags or "#sdkit" in post.tags:
            post.project = "easydiffusion"
        elif "#freebird" in post.tags:
            post.project = "freebird"
    return files


def filter_easy_diffusion_posts(files):
    return list(filter(lambda entry: entry[1].project == "easydiffusion", files))


def filter_freebird_posts(files):
    return list(filter(lambda entry: entry[1].project == "freebird" and "#worklog" not in entry[1].tags, files))


def insert_project_crosspost_links_in_cmdr2_blog(files):
    new_files = []
    for entry in files:
        filename, post = entry

        if post.project == "easydiffusion":
            new_post_body = (
                f"Cross-posted from [Easy Diffusion's blog](https://easydiffusion.github.io/blog/{post.id}).\n\n"
                + post.body
            )
            new_post = replace(post, body=new_post_body)
            new_files.append((filename, new_post))
        elif post.project == "freebird":
            post_uri = post.time.strftime("%Y/%m/%d") + "/" + post.id
            new_post_body = (
                f"Cross-posted from [Freebird's blog](https://freebirdxr.com/blog/{post_uri}).\n\n" + post.body
            )
            new_post = replace(post, body=new_post_body)
            new_files.append((filename, new_post))
        else:
            new_files.append(entry)

    return new_files


# def wait_for_threads(thread_groups):
#     for thread_group in thread_groups:
#         for thread in thread_group:
#             thread.join()


def run():
    workflow = [
        download_from_dropbox,
        unzip_files,
        split_blog_entries,
        classify_posts_by_project,
        {  # feed the blog entries to the three publish pipelines in parallel
            (
                insert_project_crosspost_links_in_cmdr2_blog,
                partial(convert_to_frontmatter, cms="hugo"),
                partial(publish_to_github, **CMDR2_BLOG_GH_CONFIG),
            ),
            (
                filter_easy_diffusion_posts,
                partial(convert_to_frontmatter, cms="hugo"),
                partial(publish_to_github, **EASY_DIFFUSION_GH_CONFIG),
            ),
            (
                filter_freebird_posts,
                partial(convert_to_frontmatter, cms="mkdocs"),
                partial(publish_to_github, **FREEBIRD_GH_CONFIG),
            ),
        },
        # wait_for_threads,
    ]

    _run(workflow)
