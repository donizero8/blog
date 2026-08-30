import datetime
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .forms import BookAdminForm, BookNoteAdminForm, PostAdminForm, optimize_uploaded_image
from .models import Book, BookNote, Post, SiteProfile, Tag
from .widgets import MediumEditorWidget


class HomepageCopyTests(TestCase):
    def test_homepage_uses_copy_from_site_profile(self):
        profile = SiteProfile.load()
        profile.hero_title = "Judul beranda pilihan saya"
        profile.hero_description = "Deskripsi yang dapat diedit melalui CMS."
        profile.save()

        response = self.client.get(reverse("blog:list"))

        self.assertContains(response, "Judul beranda pilihan saya")
        self.assertContains(response, "Deskripsi yang dapat diedit melalui CMS.")


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


class PublicCommentCopyTests(TestCase):
    def setUp(self):
        author = get_user_model().objects.create_user(username="comment-author")
        self.post = Post.objects.create(
            title="Commentable Post",
            slug="commentable-post",
            body="<p>Post body</p>",
            author=author,
            status=Post.Status.PUBLISHED,
        )

    def test_comment_section_uses_english_copy(self):
        response = self.client.get(self.post.get_absolute_url())

        self.assertContains(response, "Comments")
        self.assertContains(response, "No comments yet. Be the first to join the conversation.")
        self.assertContains(response, "Leave a comment")
        self.assertContains(response, "Post comment")
        self.assertContains(response, 'placeholder="Your name"')
        self.assertContains(response, 'placeholder="Write a comment…"')

    def test_post_date_uses_english_month_name(self):
        self.post.published_at = datetime.datetime(
            2026, 8, 21, 10, 0, tzinfo=datetime.timezone.utc
        )
        self.post.save(update_fields=["published_at"])

        response = self.client.get(self.post.get_absolute_url())

        self.assertContains(response, "August 21, 2026")
        self.assertNotContains(response, "Agustus")

    def test_public_post_uses_english_url_and_legacy_url_redirects(self):
        self.assertEqual(self.post.get_absolute_url(), "/posts/commentable-post/")

        response = self.client.get("/tulisan/commentable-post/")

        self.assertRedirects(
            response,
            "/posts/commentable-post/",
            status_code=301,
            fetch_redirect_response=False,
        )

    def test_comment_submission_uses_english_moderation_notice(self):
        response = self.client.post(
            self.post.get_absolute_url(),
            {"name": "Reader", "email": "reader@example.com", "body": "A useful post."},
            follow=True,
        )

        self.assertContains(response, "Thank you. Your comment is awaiting approval.")
        self.assertNotContains(response, "A useful post.")
        self.assertEqual(response.redirect_chain[0][0], "/posts/commentable-post/#comments")


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


class BookJournalEditorTests(TestCase):
    def test_book_and_note_forms_use_medium_editor(self):
        self.assertIsInstance(BookAdminForm().fields["thoughts"].widget, MediumEditorWidget)
        note_widget = BookNoteAdminForm().fields["body"].widget
        self.assertIsInstance(note_widget, MediumEditorWidget)
        self.assertEqual(note_widget.variant, "compact")

    def test_book_and_note_html_is_sanitized(self):
        book_form = BookAdminForm(data={
            "title": "Safe Book",
            "slug": "safe-book",
            "author": "Writer",
            "status": "reading",
            "progress": 10,
            "current_chapter": "",
            "total_chapters": "",
            "started_at": "",
            "finished_at": "",
            "rating": "",
            "thoughts": '<h2>Insight</h2><script>alert(1)</script><p onclick="bad()">Safe</p>',
            "lessons": "One lesson",
        })
        self.assertTrue(book_form.is_valid(), book_form.errors)
        self.assertNotIn("<script", book_form.cleaned_data["thoughts"])
        self.assertNotIn("onclick", book_form.cleaned_data["thoughts"])

        book = Book.objects.create(title="Notes", slug="notes", author="Writer")
        note_form = BookNoteAdminForm(data={
            "book": book.pk,
            "heading": "Chapter 1",
            "body": '<p><strong>Useful</strong></p><img src="javascript:bad" onerror="bad()">',
            "order": 1,
        })
        self.assertTrue(note_form.is_valid(), note_form.errors)
        cleaned = note_form.cleaned_data["body"]
        self.assertIn("<strong>Useful</strong>", cleaned)
        self.assertNotIn("javascript:", cleaned)
        self.assertNotIn("onerror", cleaned)

    def test_book_detail_renders_saved_rich_text_formatting(self):
        book = Book.objects.create(
            title="Formatted Journal",
            slug="formatted-journal",
            author="Writer",
            thoughts=(
                '<p><em>A highlighted thought</em></p>'
                '<img src="/media/posts/example.webp" alt="Example" '
                'class="article-image image-small" loading="lazy">'
            ),
        )
        BookNote.objects.create(
            book=book,
            heading="Chapter 2",
            body="<blockquote>A useful note</blockquote>",
        )

        response = self.client.get(book.get_absolute_url())

        self.assertContains(response, "<em>A highlighted thought</em>", html=True)
        self.assertContains(response, 'class="article-image image-small"')
        self.assertContains(response, "<blockquote>A useful note</blockquote>", html=True)


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
