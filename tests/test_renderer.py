#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
from otterwiki.renderer import render

def test_lastword():
    lastword = render.lastword
    orig = "aaa bbb ccc"
    modified = lastword.sub(r"ddd \1", orig)
    assert modified == "aaa bbb ddd ccc"


def test_basic_markdown():
    html, toc = render.markdown("**bold** _italic_")
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html


def test_toc():
    md = """
# head 1
text
## head 1.1 **bold**
text
# head 2
# head 2
    """
    html, toc = render.markdown(md)
    # head 1
    assert "head 1" == toc[0][1]
    assert 1 == toc[0][2]
    assert "head-1" == toc[0][4]
    # head 1.1
    assert "head 1.1 <strong>bold</strong>" == toc[1][1]
    # check raw
    assert "head 1.1 bold" == toc[1][3]
    assert "head-11-bold" == toc[1][4]
    assert 2 == toc[1][2]
    # check duplicate header handling
    assert "head-2" == toc[2][4]
    assert "head-2-1" == toc[3][4]


def test_code():
    html, _ = render.markdown(
        """```
abc
```"""
    )
    assert '<pre class="code">abc</pre>' in html
    # test highlight
    html, _ = render.markdown(
        """```python
n = 0
```"""
    )
    assert '<div class="highlight">' in html
    # test missing lexer
    html, _ = render.markdown(
        """```non_existing_lexer
n = 0
```"""
    )
    assert '<pre class="code">non_existing_lexer' in html


def test_latex_block():
    text = """
```math
a^2+b^2=c^2
```
"""
    html, _ = render.markdown(text)
    assert "\\[a^2+b^2=c^2\\]" == html


def test_latex_inline():
    text = "$`a`$"
    html, _ = render.markdown(text)
    assert "$<code>a</code>$" in html


def test_img():
    text = "![](/path/to/img.png)"
    html, _ = render.markdown(text)
    assert 'src="/path/to/img.png"' in html

    text = '![](/path/to/img.png "title")'
    html, _ = render.markdown(text)
    assert 'src="/path/to/img.png"' in html
    assert 'title="title"' in html

    text = '![alt text](/path/to/img.png "title")'
    html, _ = render.markdown(text)
    assert 'src="/path/to/img.png"' in html
    assert 'title="title"' in html
    assert 'alt="alt text"' in html

def test_html_mark():
    text = "<mark>mark</mark>"
    html, _ = render.markdown(text)
    assert "<mark>mark</mark>" in html


def test_wiki_link(req_ctx):
    text = "[[Title|Link]]"
    html, _ = render.markdown(text)
    assert '<a href="/Link">Title</a>' in html
    text = "[[Link]]"
    html, _ = render.markdown(text)
    assert '<a href="/Link">Link</a>' in html

