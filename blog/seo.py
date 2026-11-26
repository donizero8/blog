"""Plain-text descriptions and stable public URLs for detail pages."""
from html.parser import HTMLParser

from django.conf import settings
from django.utils.text import Truncator


class DescriptionText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "iframe"}:
            self.ignored.append(tag)
        if not self.ignored and tag in {"p", "div", "br", "li", "h2", "h3", "pre", "blockquote"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if self.ignored:
            if tag == self.ignored[-1]:
                self.ignored.pop()
        elif tag in {"p", "div", "li", "h2", "h3", "pre", "blockquote"}:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


def description(*candidates):
    for candidate in candidates:
        parser = DescriptionText()
        parser.feed(candidate or "")
        text = " ".join("".join(parser.parts).split())
        if text:
            return Truncator(text).chars(160)
    return ""


def detail_metadata(obj, *candidates):
    return {
        "meta_description": description(*candidates),
        "canonical_url": settings.SITE_URL.rstrip("/") + obj.get_absolute_url(),
    }
