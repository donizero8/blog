import uuid
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.contrib import admin
from django.core.files.storage import default_storage
from django.db.models import Count, Q
from django.http import HttpResponseNotAllowed, JsonResponse
from django.urls import path
from PIL import Image, UnidentifiedImageError

from .forms import (
    BookAdminForm,
    BookNoteAdminForm,
    PostAdminForm,
    SiteProfileAdminForm,
    optimize_article_image,
)
from .models import Book, BookNote, Comment, Post, SiteProfile, Tag

admin.site.site_header = "Dony’s Notebook"
admin.site.site_title = "Admin Dony’s Notebook"
admin.site.index_title = "Kelola tulisan"

GOOGLE_MAPS_SHORT_HOSTS = {"maps.app.goo.gl"}
GOOGLE_MAPS_HOSTS = {"google.com", "www.google.com", "maps.google.com"}
GOOGLE_MAPS_ALLOWED_QUERY = {
    "api", "q", "query", "query_place_id", "origin", "destination", "travelmode", "waypoints",
}


def _valid_maps_url(value, allowed_hosts):
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and parsed.hostname in allowed_hosts
            and not parsed.username
            and not parsed.password
            and parsed.port is None
        )
    except ValueError:
        return False


class GoogleMapsRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _valid_maps_url(newurl, GOOGLE_MAPS_SHORT_HOSTS | GOOGLE_MAPS_HOSTS):
            raise HTTPError(newurl, code, "Tujuan redirect bukan Google Maps.", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def clean_google_maps_url(value):
    value = value.strip()
    if _valid_maps_url(value, GOOGLE_MAPS_SHORT_HOSTS):
        request = Request(value, headers={"User-Agent": "DonyNotebook/1.0"})
        with build_opener(GoogleMapsRedirectHandler()).open(request, timeout=5) as response:
            value = response.geturl()
    if not _valid_maps_url(value, GOOGLE_MAPS_HOSTS):
        raise ValueError("URL harus berasal dari Google Maps.")
    parsed = urlsplit(value)
    if not (parsed.path == "/maps" or parsed.path.startswith("/maps/")):
        raise ValueError("URL Google tidak mengarah ke Maps.")
    clean_query = urlencode(
        [(key, item) for key, item in parse_qsl(parsed.query, keep_blank_values=False) if key in GOOGLE_MAPS_ALLOWED_QUERY],
        doseq=True,
    )
    return urlunsplit(("https", "www.google.com", parsed.path, clean_query, ""))


class BookNoteInline(admin.StackedInline):
    model = BookNote
    form = BookNoteAdminForm
    # Keep the journal area empty until the editor explicitly adds a note.
    # Existing notes are still rendered normally on the change page.
    extra = 0


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    form = BookAdminForm
    inlines = (BookNoteInline,)
    list_display = ("title", "author", "status", "progress", "rating", "updated_at")
    list_filter = ("status", "rating")
    search_fields = ("title", "author", "thoughts", "lessons")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Buku", {"fields": ("cover_url", "cover", "title", "slug", "author", "status")}),
        ("Progres", {
            "fields": ("progress", ("current_chapter", "total_chapters"), ("started_at", "finished_at")),
            "classes": ("book-progress-section",),
        }),
        ("Jurnal", {"fields": ("thoughts", "lessons")}),
        ("Informasi", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    class Media:
        css = {"all": ("blog/admin/book.css",)}
        js = ("blog/admin/book.js",)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ("title", "author", "status", "published_at", "updated_at")
    list_filter = ("status", "author")
    search_fields = ("title", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("title", "slug", "excerpt", "tags_input", "body")}),
        ("Publikasi", {"fields": ("author", "status", "published_at")}),
        ("Informasi", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_changeform_initial_data(self, request):
        return {"author": request.user.pk}

    def get_urls(self):
        custom_urls = [
            path(
                "upload-image/",
                self.admin_site.admin_view(self.upload_image),
                name="blog_post_upload_image",
            ),
            path(
                "resolve-maps-url/",
                self.admin_site.admin_view(self.resolve_maps_url),
                name="blog_post_resolve_maps_url",
            ),
        ]
        return custom_urls + super().get_urls()

    def resolve_maps_url(self, request):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        try:
            url = clean_google_maps_url(request.POST.get("url", ""))
        except (ValueError, HTTPError, URLError, TimeoutError):
            return JsonResponse({"error": "URL Google Maps tidak valid atau tidak dapat dibuka."}, status=400)
        return JsonResponse({"url": url})

    def upload_image(self, request):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        upload = request.FILES.get("image")
        if not upload:
            return JsonResponse({"error": "Pilih gambar untuk diunggah."}, status=400)
        if upload.size > 8 * 1024 * 1024:
            return JsonResponse({"error": "Ukuran gambar maksimal 8 MB."}, status=400)
        try:
            optimized, width, height = optimize_article_image(upload)
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError, ValueError):
            return JsonResponse({"error": "File bukan gambar yang valid atau resolusinya terlalu besar."}, status=400)
        today = date.today()
        filename = f"posts/{today:%Y/%m}/{uuid.uuid4().hex}.webp"
        saved_name = default_storage.save(filename, optimized)
        return JsonResponse({"url": default_storage.url(saved_name), "width": width, "height": height})


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "post_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Jumlah tulisan")
    def post_count(self, obj):
        return obj.posts.count()


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("name", "post", "short_body", "is_read", "is_approved", "created_at")
    list_filter = ("is_read", "is_approved", "created_at")
    search_fields = ("name", "email", "body", "post__title")
    list_editable = ("is_approved",)
    actions = ("mark_as_read", "mark_as_unread", "approve_comments", "unapprove_comments")
    readonly_fields = ("created_at",)

    @admin.display(description="Isi")
    def short_body(self, obj):
        return obj.body[:70]

    def change_view(self, request, object_id, form_url="", extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and self.has_view_or_change_permission(request, obj):
            Comment.objects.filter(pk=obj.pk, is_read=False).update(is_read=True)
            obj.is_read = True
        return super().change_view(request, object_id, form_url, extra_context)

    @admin.action(description="Tandai komentar terpilih sudah dibaca")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="Tandai komentar terpilih belum dibaca")
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)

    @admin.action(description="Setujui komentar terpilih")
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Batalkan persetujuan komentar terpilih")
    def unapprove_comments(self, request, queryset):
        queryset.update(is_approved=False)


@admin.register(SiteProfile)
class SiteProfileAdmin(admin.ModelAdmin):
    form = SiteProfileAdminForm
    fieldsets = (
        ("Beranda", {"fields": ("hero_title", "hero_description")}),
        ("Identitas", {"fields": ("photo", "name", "headline", "bio", "location")}),
        ("Tautan", {"fields": ("linkedin_url", "github_url")}),
        ("Informasi", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not SiteProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.index_template = "admin/index.html"
_default_admin_index = admin.site.index


def dashboard_index(request, extra_context=None):
    context = dict(extra_context or {})
    if request.user.has_perm("blog.view_post"):
        context["post_stats"] = Post.objects.aggregate(
            total=Count("id"),
            drafts=Count("id", filter=Q(status=Post.Status.DRAFT)),
            published=Count("id", filter=Q(status=Post.Status.PUBLISHED)),
        )
    if request.user.has_perm("blog.view_book"):
        context["book_stats"] = Book.objects.aggregate(
            total=Count("id"),
            want=Count("id", filter=Q(status=Book.Status.WANT)),
            reading=Count("id", filter=Q(status=Book.Status.READING)),
            finished=Count("id", filter=Q(status=Book.Status.FINISHED)),
            favorite=Count("id", filter=Q(status=Book.Status.FAVORITE)),
        )
    if request.user.has_perm("blog.view_comment"):
        context["comment_stats"] = Comment.objects.aggregate(
            total=Count("id"),
            unread=Count("id", filter=Q(is_read=False)),
            pending=Count("id", filter=Q(is_approved=False)),
            approved=Count("id", filter=Q(is_approved=True)),
        )
    return _default_admin_index(request, extra_context=context)


admin.site.index = dashboard_index
