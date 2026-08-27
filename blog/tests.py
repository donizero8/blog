import datetime
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .forms import PostAdminForm, optimize_uploaded_image
from .models import Book, Post, Tag


class ReadingTimelineTests(TestCase):
    def test_timeline_groups_reading_history_and_excludes_want_list(self):
        Book.objects.create(
            title="Sedang Dibaca",
            author="Penulis A",
            status=Book.Status.READING,
            started_at=datetime.date(2026, 8, 16),
            progress=38,
        )
        Book.objects.create(
            title="Sudah Selesai",
            author="Penulis B",
            status=Book.Status.FINISHED,
            finished_at=datetime.date(2026, 7, 20),
            rating=4,
        )
        Book.objects.create(
            title="Daftar Nanti",
            author="Penulis C",
            status=Book.Status.WANT,
            started_at=datetime.date(2026, 6, 1),
        )

        response = self.client.get(reverse("blog:reading_timeline"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2026")
        self.assertContains(response, "August")
        self.assertContains(response, "July")
        self.assertContains(response, "Sedang Dibaca")
        self.assertContains(response, "Sudah Selesai")
        self.assertNotContains(response, "Daftar Nanti")


class SearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model

        author = get_user_model().objects.create_user(username="penulis")
        post = Post.objects.create(
            title="Belajar PostgreSQL",
            slug="belajar-postgresql",
            body="Catatan basis data",
            author=author,
            status=Post.Status.PUBLISHED,
        )
        post.tags.add(Tag.objects.create(name="Database"))
        Book.objects.create(title="Clean Code", author="Robert C. Martin", thoughts="Kode bersih")

    def test_search_finds_published_posts_and_books(self):
        post_response = self.client.get(reverse("blog:search"), {"q": "Database"})
        book_response = self.client.get(reverse("blog:search"), {"q": "Clean Code"})

        self.assertContains(post_response, "Belajar PostgreSQL")
        self.assertContains(book_response, "Clean Code")


class ImageOptimizationTests(TestCase):
    def test_uploaded_image_is_cropped_and_converted_to_webp(self):
        source = BytesIO()
        Image.new("RGB", (1200, 1200), "red").save(source, format="PNG")
        upload = SimpleUploadedFile("cover.png", source.getvalue(), content_type="image/png")

        optimized = optimize_uploaded_image(upload, (300, 424), "cover")

        with Image.open(optimized) as image:
            self.assertEqual(image.size, (300, 424))
            self.assertEqual(image.format, "WEBP")
        self.assertTrue(optimized.name.endswith("-cover.webp"))


class ArticleImageUploadTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = self.settings(MEDIA_ROOT=self.media_directory.name)
        self.settings_override.enable()
        self.user = get_user_model().objects.create_superuser(
            username="editor", email="editor@example.com", password="rahasia-kuat"
        )

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def test_staff_upload_is_compressed_and_saved_as_webp(self):
        source = BytesIO()
        Image.new("RGB", (2400, 1200), "blue").save(source, format="PNG")
        upload = SimpleUploadedFile("artikel.png", source.getvalue(), content_type="image/png")
        self.client.force_login(self.user)

        response = self.client.post(reverse("admin:blog_post_upload_image"), {"image": upload})

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["url"].endswith(".webp"))
        stored_path = Path(self.media_directory.name) / result["url"].removeprefix("/media/")
        with Image.open(stored_path) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertEqual(image.size, (1600, 800))

    def test_upload_requires_staff_login(self):
        response = self.client.post(reverse("admin:blog_post_upload_image"))
        self.assertEqual(response.status_code, 302)

    def test_post_form_keeps_safe_image_attributes_only(self):
        form = PostAdminForm(data={
            "title": "Artikel bergambar",
            "slug": "artikel-bergambar",
            "excerpt": "",
            "body": '<p>Teks</p><img src="/media/posts/example.webp" alt="Contoh" class="article-image image-medium" loading="lazy" width="800" height="600" onclick="alert(1)" style="position:fixed">',
            "tags_input": "",
            "author": self.user.pk,
            "status": "draft",
            "published_at": "",
        })

        self.assertTrue(form.is_valid(), form.errors)
        cleaned = form.cleaned_data["body"]
        self.assertIn('class="article-image image-medium"', cleaned)
        self.assertNotIn("onclick", cleaned)
        self.assertNotIn("style=", cleaned)
