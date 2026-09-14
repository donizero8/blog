import datetime
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .forms import (
    BookAdminForm,
    BookNoteAdminForm,
    PostAdminForm,
    SiteProfileAdminForm,
    optimize_uploaded_image,
    sanitize_editor_html,
)
from .admin import clean_google_maps_url
from .cover_url import download_cover_url, validate_cover_url
from .models import Book, BookNote, Comment, Post, SiteProfile, Tag
from .widgets import MediumEditorWidget, ProfileImageWidget


class HomepageCopyTests(TestCase):
    def test_homepage_uses_copy_from_site_profile(self):
        profile = SiteProfile.load()
        profile.hero_title = "Judul beranda pilihan saya"
        profile.hero_description = "Deskripsi yang dapat diedit melalui CMS."
        profile.save()

        response = self.client.get(reverse("blog:list"))

        self.assertContains(response, "Judul beranda pilihan saya")
        self.assertContains(response, "Deskripsi yang dapat diedit melalui CMS.")

    def test_site_profile_uses_adjustable_image_widget(self):
        self.assertIsInstance(SiteProfileAdminForm().fields["photo"].widget, ProfileImageWidget)


class BookCoverUrlTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="cover-admin", email="cover@example.com", password="strong-password"
        )

    @patch("blog.cover_url.socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.215.14", 443))])
    def test_validates_public_https_only(self, _resolve):
        parsed, address = validate_cover_url("https://example.com/cover.jpg")
        self.assertEqual(parsed.hostname, "example.com")
        self.assertEqual(address, "93.184.215.14")
        with self.assertRaises(ValueError):
            validate_cover_url("http://example.com/cover.jpg")
        with self.assertRaises(ValueError):
            validate_cover_url("https://user:pass@example.com/cover.jpg")

    @patch("blog.cover_url.socket.getaddrinfo", return_value=[(None, None, None, None, ("127.0.0.1", 443))])
    def test_rejects_private_addresses(self, _resolve):
        with self.assertRaises(ValueError):
            validate_cover_url("https://localhost/cover.jpg")

    def test_book_form_contains_url_field(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin:blog_book_add"))
        self.assertContains(response, "URL gambar sampul")
        self.assertContains(response, "id_cover_url")
        self.assertNotContains(response, "Cari sampul di Google Books")

    @patch("blog.cover_url.download_cover_url")
    def test_cover_url_is_saved(self, download):
        source = BytesIO()
        Image.new("RGB", (100, 140), "red").save(source, format="PNG")
        download.return_value = SimpleUploadedFile("url-cover.webp", source.getvalue(), content_type="image/png")
        form = BookAdminForm(data={"title": "A book", "slug": "a-book", "author": "Author", "status": "want", "progress": 0, "cover_url": "https://example.com/cover.jpg"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["cover"].name, "url-cover.webp")
        download.assert_called_once_with("https://example.com/cover.jpg")

    @patch("blog.cover_url.PinnedHTTPSConnection")
    @patch("blog.cover_url.validate_cover_url")
    def test_download_rejects_redirects(self, validate, connection):
        from urllib.parse import urlsplit
        validate.return_value = (urlsplit("https://example.com/cover.jpg"), "93.184.215.14")
        connection.return_value.getresponse.return_value.status = 302
        with self.assertRaises(ValueError):
            download_cover_url("https://example.com/cover.jpg")
        connection.return_value.close.assert_called_once()

    @patch("blog.cover_url.PinnedHTTPSConnection")
    @patch("blog.cover_url.validate_cover_url")
    def test_download_converts_image_to_local_webp(self, validate, connection):
        from urllib.parse import urlsplit
        validate.return_value = (urlsplit("https://example.com/cover.jpg"), "93.184.215.14")
        source = BytesIO()
        Image.new("RGB", (100, 140), "red").save(source, format="PNG")
        response = connection.return_value.getresponse.return_value
        response.status = 200
        response.getheader.side_effect = lambda name, default=None: {
            "Content-Type": "image/png", "Content-Length": str(len(source.getvalue()))
        }.get(name, default)
        response.read.return_value = source.getvalue()
        cover = download_cover_url("https://example.com/cover.jpg")
        with Image.open(cover) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertEqual(image.size, (300, 424))


class AdminDashboardStatsTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="dashboard-admin", email="dashboard@example.com", password="strong-password"
        )
        self.post = Post.objects.create(
            title="Draft post", slug="draft-post", author=self.admin, status=Post.Status.DRAFT
        )
        Post.objects.create(
            title="Published post", slug="published-post", author=self.admin, status=Post.Status.PUBLISHED
        )
        Book.objects.create(title="Reading book", slug="reading-book", author="Writer", status=Book.Status.READING)
        self.comment = Comment.objects.create(
            post=self.post, name="Reader", email="reader@example.com", body="Needs attention"
        )
        self.client.force_login(self.admin)

    def test_admin_index_shows_content_statistics(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Statistik konten")
        self.assertContains(response, "Masih draft")
        self.assertContains(response, "Belum dibaca")
        self.assertContains(response, "Menunggu moderasi")
        self.assertEqual(response.context["post_stats"]["drafts"], Post.objects.filter(status=Post.Status.DRAFT).count())
        self.assertEqual(response.context["book_stats"]["reading"], Book.objects.filter(status=Book.Status.READING).count())
        self.assertEqual(response.context["comment_stats"]["unread"], Comment.objects.filter(is_read=False).count())

    def test_opening_comment_marks_it_as_read(self):
        response = self.client.get(reverse("admin:blog_comment_change", args=[self.comment.pk]))

        self.assertEqual(response.status_code, 200)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_read)


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


class YouTubeSanitizationTests(TestCase):
    def test_referrer_policy_added_to_old_embeds_and_preserved(self):
        from django.template import Context, Template

        old = '<iframe class="youtube-embed" src="https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"></iframe>'
        updated = sanitize_editor_html(old)
        self.assertIn('referrerpolicy="strict-origin-when-cross-origin"', updated)
        self.assertEqual(sanitize_editor_html(updated), updated)
        self.assertEqual(Template('{% load editor_content %}{{ body|editor_content }}').render(Context({'body': old})), updated)
        self.assertNotIn('referrerpolicy="no-referrer"', sanitize_editor_html(old.replace('<iframe ', '<iframe referrerpolicy="no-referrer" ')))


class LocationCardTests(TestCase):
    def test_long_google_maps_url_is_cleaned(self):
        cleaned = clean_google_maps_url(
            "https://www.google.com/maps/place/Monas/@-6.1754,106.8272,17z"
            "?api=1&query=Monas&utm_source=share#details"
        )

        self.assertEqual(
            cleaned,
            "https://www.google.com/maps/place/Monas/@-6.1754,106.8272,17z?api=1&query=Monas",
        )

    def test_non_maps_and_non_google_urls_are_rejected(self):
        with self.assertRaises(ValueError):
            clean_google_maps_url("https://example.com/maps/place/Monas")
        with self.assertRaises(ValueError):
            clean_google_maps_url("https://www.google.com/search?q=Monas")

    def test_location_card_markup_is_sanitized_and_preserved(self):
        html = (
            '<a class="place-card extra" href="https://www.google.com/maps/place/Monas" '
            'target="_blank" rel="noopener noreferrer" onclick="bad()">'
            '<span class="place-card-icon">📍</span><span class="place-card-copy">'
            '<strong>Monas</strong><small>Buka lokasi di Google Maps ↗</small></span></a>'
        )
        cleaned = sanitize_editor_html(html)

        self.assertNotIn("onclick", cleaned)
        self.assertNotIn('class="place-card extra"', cleaned)
        self.assertIn('class="place-card-icon"', cleaned)
        self.assertNotIn("Buka lokasi di Google Maps", cleaned)
        self.assertIn("Open location in Google Maps", cleaned)

    @patch("blog.admin.clean_google_maps_url", return_value="https://www.google.com/maps/place/Monas")
    def test_admin_resolver_returns_cleaned_url(self, resolver):
        admin = get_user_model().objects.create_superuser(
            username="maps-admin", email="maps@example.com", password="strong-password"
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse("admin:blog_post_resolve_maps_url"),
            {"url": "https://maps.app.goo.gl/example"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["url"], "https://www.google.com/maps/place/Monas")
        resolver.assert_called_once_with("https://maps.app.goo.gl/example")

    def test_only_canonical_youtube_embed_is_allowed(self):
        src = "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
        html = sanitize_editor_html(f'<iframe src="{src}" class="youtube-embed" allowfullscreen></iframe>')
        self.assertIn(src, html)
        self.assertIn('class="youtube-embed"', html)
        for unsafe in ["https://evil.example/embed/dQw4w9WgXcQ", src + "?autoplay=1", "javascript:alert(1)", "https://www.youtube-nocookie.com.evil.test/embed/dQw4w9WgXcQ"]:
            cleaned = sanitize_editor_html(f'<iframe src="{unsafe}" srcdoc="bad" onload="bad" style="position:fixed"></iframe>')
            self.assertNotIn("src=", cleaned)
            self.assertNotIn("srcdoc", cleaned)
            self.assertNotIn("onload", cleaned)
            self.assertNotIn("style=", cleaned)


class LibraryDisplayLimitTests(TestCase):
    def test_library_renders_all_books_with_initial_section_limits(self):
        initial_reading = Book.objects.filter(status=Book.Status.READING).count()
        initial_finished = Book.objects.filter(status=Book.Status.FINISHED).count()
        initial_want = Book.objects.filter(status=Book.Status.WANT).count()

        for number in range(6):
            Book.objects.create(
                title=f"Reading Book {number}",
                author="Reader",
                status=Book.Status.READING,
                started_at=datetime.date(2026, 8, number + 1),
            )
        for number in range(5):
            Book.objects.create(
                title=f"Finished Book {number}",
                author="Reader",
                status=Book.Status.FINISHED,
                started_at=datetime.date(2026, 7, number + 1),
                finished_at=datetime.date(2026, 7, number + 10),
            )
            Book.objects.create(
                title=f"Wanted Book {number}",
                author="Reader",
                status=Book.Status.WANT,
            )

        response = self.client.get(reverse("blog:library"))

        self.assertEqual(len(response.context["reading_books"]), initial_reading + 6)
        self.assertEqual(len(response.context["finished_books"]), initial_finished + 5)
        self.assertEqual(len(response.context["want_books"]), initial_want + 5)
        self.assertEqual(
            response.context["stats"],
            {
                "read": initial_finished + 5,
                "reading": initial_reading + 6,
                "want": initial_want + 5,
            },
        )
        self.assertContains(response, 'data-page-size="2"')
        self.assertContains(response, 'data-page-size="4"', count=2)
        self.assertContains(response, "Show more", count=3)


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

    def test_post_edit_shortcut_is_visible_only_with_change_permission(self):
        public_response = self.client.get(self.post.get_absolute_url())
        self.assertNotContains(public_response, "Edit post")

        admin = get_user_model().objects.create_superuser(
            username="post-admin", email="post-admin@example.com", password="strong-password"
        )
        self.client.force_login(admin)
        admin_response = self.client.get(self.post.get_absolute_url())

        self.assertContains(admin_response, "Edit post")
        self.assertContains(admin_response, reverse("admin:blog_post_change", args=[self.post.pk]))

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
    def test_external_image_url_is_allowed_but_unsafe_protocol_is_removed(self):
        safe = sanitize_editor_html(
            '<img src="https://images.example.com/cover.jpg" alt="Cover" '
            'class="article-image image-medium" loading="lazy" referrerpolicy="no-referrer">'
        )
        unsafe = sanitize_editor_html('<img src="javascript:alert(1)" alt="Unsafe">')

        self.assertIn('src="https://images.example.com/cover.jpg"', safe)
        self.assertIn('referrerpolicy="no-referrer"', safe)
        self.assertNotIn("javascript:", unsafe)

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
        staff = get_user_model().objects.create_user(username="book-editor", is_staff=True)
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
        self.client.force_login(staff)

        response = self.client.get(book.get_absolute_url())

        self.assertContains(response, "<em>A highlighted thought</em>", html=True)
        self.assertContains(response, 'class="article-image image-small"')
        self.assertContains(response, "<blockquote>A useful note</blockquote>", html=True)

    def test_public_book_detail_hides_complete_notes(self):
        book = Book.objects.create(title="Private Journal", slug="private-journal", author="Writer")
        BookNote.objects.create(
            book=book,
            heading="A private chapter",
            body="<p>This complete note must not be sent to public visitors.</p>",
        )

        response = self.client.get(book.get_absolute_url())

        self.assertContains(response, "Only the admin can view the full notes.")
        self.assertNotContains(response, "A private chapter")
        self.assertNotContains(response, "This complete note must not be sent")

    def test_staff_can_view_complete_book_notes(self):
        staff = get_user_model().objects.create_user(username="staff-reader", is_staff=True)
        book = Book.objects.create(title="Staff Journal", slug="staff-journal", author="Writer")
        BookNote.objects.create(book=book, heading="Visible to staff", body="<p>Complete staff note.</p>")
        self.client.force_login(staff)

        response = self.client.get(book.get_absolute_url())

        self.assertContains(response, "Visible to staff")
        self.assertContains(response, "Complete staff note.")
        self.assertNotContains(response, "Only the admin can view the full notes.")

    def test_book_edit_shortcut_is_visible_only_with_change_permission(self):
        book = Book.objects.create(title="Editable Book", slug="editable-book", author="Writer")
        public_response = self.client.get(book.get_absolute_url())
        self.assertNotContains(public_response, "Edit book")

        admin = get_user_model().objects.create_superuser(
            username="book-admin", email="book-admin@example.com", password="strong-password"
        )
        self.client.force_login(admin)
        admin_response = self.client.get(book.get_absolute_url())

        self.assertContains(admin_response, "Edit book")
        self.assertContains(admin_response, reverse("admin:blog_book_change", args=[book.pk]))


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
            "body": '<p><b>Tebal</b> dan <i>miring</i></p><img src="/media/posts/example.webp" alt="Contoh" class="article-image image-medium" loading="lazy" width="800" height="600" onclick="alert(1)" style="position:fixed">',
            "tags_input": "",
            "author": self.user.pk,
            "status": "draft",
            "published_at": "",
        })

        self.assertTrue(form.is_valid(), form.errors)
        cleaned = form.cleaned_data["body"]
        self.assertIn("<b>Tebal</b>", cleaned)
        self.assertIn("<i>miring</i>", cleaned)
        self.assertIn('class="article-image image-medium"', cleaned)
        self.assertNotIn("onclick", cleaned)
        self.assertNotIn("style=", cleaned)
