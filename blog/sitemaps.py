"""Sitemap URLs use the same public origin as canonical metadata."""
from types import SimpleNamespace
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Book, Post


class PublicSitemap(Sitemap):
    def get_urls(self, page=1, site=None, protocol=None):
        origin = urlsplit(settings.SITE_URL)
        return super().get_urls(
            page=page, site=SimpleNamespace(domain=origin.netloc), protocol=origin.scheme,
        )


class PageSitemap(PublicSitemap):
    def items(self):
        return ["blog:list", "blog:library", "blog:reading_timeline"]

    def location(self, item):
        return reverse(item)


class PostSitemap(PublicSitemap):
    def items(self):
        return Post.objects.filter(status=Post.Status.PUBLISHED).only("slug", "updated_at").order_by("pk")

    def lastmod(self, obj):
        return obj.updated_at


class BookSitemap(PublicSitemap):
    def items(self):
        return Book.objects.only("slug").order_by("pk")

    # Notes can change independently of Book.updated_at, so omit lastmod.


sitemaps = {"pages": PageSitemap, "posts": PostSitemap, "books": BookSitemap}
