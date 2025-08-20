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


def filter_easy_diffusion_posts(files):
    # files is a list of tuples: (filename, (post_time, tags, post_body, title))
    new_files = []
    for entry in files:
        tags = entry[1][1]
        if "#easydiffusion" in tags or "#sdkit" in tags:
            new_files.append(entry)
    return new_files


def filter_freebird_posts(files):
    # files is a list of tuples: (filename, (post_time, tags, post_body, title))
    new_files = []
    for entry in files:
        tags = entry[1][1]
        if "#worklog" in tags:
            continue

        if "#freebird" in tags:
            new_files.append(entry)
    return new_files


def wait_for_threads(thread_groups):
    for thread_group in thread_groups:
        for thread in thread_group:
            thread.join()


def run():
    workflow = [
        download_from_dropbox,
        unzip_files,
        split_blog_entries,
        {  # feed the blog entries to the three publish pipelines in parallel
            (
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
