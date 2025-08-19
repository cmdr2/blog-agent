from tasks import (
    download_from_dropbox,
    unzip_files,
    split_blog_entries,
    convert_to_hugo,
    convert_to_jekyll,
    upload_to_s3 as publish_to_github,
)
from liteflow import run as _run


from functools import partial

EASY_DIFFUSION_CONFIG = {"s3_bucket": "cmdr2.org", "s3_prefix": "easy-diffusion"}
CMDR2_BLOG_CONFIG = {"s3_bucket": "cmdr2.org", "s3_prefix": "cmdr2"}


def filter_easy_diffusion_posts(files):
    # files is a list of tuples: (filename, (post_time, tags, post_body))
    new_files = []
    for entry in files:
        tags = entry[1][1]
        if "easydiffusion" in tags:
            new_files.append(entry)
    return new_files


def wait_for_threads(thread_groups):
    for thread_group in thread_groups:
        for thread in thread_group:
            thread.join()


workflow = [
    download_from_dropbox,
    unzip_files,
    split_blog_entries,
    {
        [filter_easy_diffusion_posts, convert_to_jekyll, partial(publish_to_github, config=EASY_DIFFUSION_CONFIG)],
        [convert_to_hugo, partial(publish_to_github, config=CMDR2_BLOG_CONFIG)],
    },
    wait_for_threads,
]


def run():
    _run(workflow)
