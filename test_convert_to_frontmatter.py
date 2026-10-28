from datetime import datetime

from tasks.convert_to_frontmatter import format_content
from tasks.split_blog_entries import Post


def make_post(**overrides):
    fields = dict(
        id="1729102225",
        time=datetime(2024, 10, 16, 18, 10, 25),
        tags=["#easydiffusion", "#lab"],
        body="First paragraph.\n\nSecond paragraph.\n",
        title=None,
    )
    fields.update(overrides)
    return Post(**fields)


def test_zensical_frontmatter_uses_categories_and_full_timestamp():
    content = format_content(make_post(), "zensical")

    assert 'title: "Post from Oct 16, 2024"' in content
    assert "date: 2024-10-16T18:10:25" in content
    assert 'slug: "1729102225"' in content
    assert "categories:\n  - easydiffusion\n  - lab" in content
    assert "tags:" not in content


def test_zensical_inserts_excerpt_marker_after_first_paragraph():
    content = format_content(make_post(), "zensical")

    assert "First paragraph.\n\n<!-- more -->\n\nSecond paragraph." in content


def test_zensical_does_not_duplicate_excerpt_marker():
    content = format_content(make_post(body="Intro.\n\n<!-- more -->\n\nRest.\n"), "zensical")

    assert content.count("<!-- more -->") == 1


def test_zensical_single_paragraph_has_no_excerpt_marker():
    content = format_content(make_post(body="Only paragraph.\n"), "zensical")

    assert "<!-- more -->" not in content


def test_zensical_removes_duplicate_title_heading_and_excerpts_first_paragraph():
    content = format_content(
        make_post(title="A test post", body="# A test post\n\nFirst paragraph.\n\nSecond.\n"),
        "zensical",
    )

    assert "# A test post" not in content
    assert "First paragraph.\n\n<!-- more -->\n\nSecond." in content


def test_hugo_frontmatter_unchanged():
    content = format_content(make_post(), "hugo")

    assert "tags:\n  - easydiffusion\n  - lab" in content
    assert "categories:" not in content
    assert "date: 2024-10-16T18:10:25" in content
    assert "<!-- more -->" not in content


def test_mkdocs_frontmatter_unchanged():
    content = format_content(make_post(), "mkdocs")

    assert "categories:\n  - easydiffusion\n  - lab" in content
    assert "date: 2024-10-16" in content
    assert "<!-- more -->" not in content
