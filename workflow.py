import os

from tasks import (
    download_from_dropbox,
    unzip_files,
    split_blog_entries,
    convert_to_hugo,
    convert_to_jekyll,
)
from tasks.upload_to_s3 import run as upload_to_s3
from tasks.publish_to_github import run as publish_to_github
from liteflow import run as _run


from functools import partial

EASY_DIFFUSION_CONFIG = {"s3_bucket": "cmdr2.org", "s3_prefix": "easy-diffusion"}
CMDR2_BLOG_CONFIG = {
    "github_owner": "cmdr2",
    "github_repo": "cmdr2.github.io",
    "github_branch": "foo",
    "github_prefix": "content",
    "github_token": os.environ.get("CMDR2_BLOG_GITHUB_TOKEN"),
}


def filter_easy_diffusion_posts(files):
    # files is a list of tuples: (filename, (post_time, tags, post_body))
    new_files = []
    for entry in files:
        tags = entry[1][1]
        if "#easydiffusion" in tags:
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
        {
            (filter_easy_diffusion_posts, convert_to_jekyll, partial(upload_to_s3, config=EASY_DIFFUSION_CONFIG)),
            (convert_to_hugo, partial(publish_to_github, config=CMDR2_BLOG_CONFIG)),
        },
        wait_for_threads,
    ]

    _run(workflow)
