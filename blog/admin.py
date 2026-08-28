import uuid
from datetime import date

from django.contrib import admin
from django.core.files.storage import default_storage
from django.http import HttpResponseNotAllowed, JsonResponse
from django.urls import path
from PIL import Image, UnidentifiedImageError

from .forms import BookAdminForm, PostAdminForm, SiteProfileAdminForm, optimize_article_image
from .models import Book, BookNote, Comment, Post, SiteProfile, Tag

admin.site.site_header = "Dony’s Notebook"
admin.site.site_title = "Admin Dony’s Notebook"
admin.site.index_title = "Kelola tulisan"


class BookNoteInline(admin.StackedInline):
    model = BookNote
    extra = 1


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
        ("Buku", {"fields": ("cover", "title", "slug", "author", "status")}),
        ("Progres", {"fields": ("progress", ("current_chapter", "total_chapters"), ("started_at", "finished_at"), "rating")}),
        ("Jurnal", {"fields": ("thoughts", "lessons")}),
        ("Informasi", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

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
        ]
        return custom_urls + super().get_urls()

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
    list_display = ("name", "post", "short_body", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("name", "email", "body", "post__title")
    list_editable = ("is_approved",)
    actions = ("approve_comments", "unapprove_comments")
    readonly_fields = ("created_at",)

    @admin.display(description="Isi")
    def short_body(self, obj):
        return obj.body[:70]

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
