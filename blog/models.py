from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class SiteProfile(models.Model):
    hero_title = models.CharField(
        "judul beranda",
        max_length=160,
        default="Books, English, code, and things I learn.",
    )
    hero_description = models.CharField(
        "deskripsi beranda",
        max_length=240,
        default="Tempat sederhana untuk menulis hal-hal yang layak diingat.",
    )
    name = models.CharField("nama", max_length=100, default="Dony Wijaya")
    headline = models.CharField("headline", max_length=160, blank=True)
    bio = models.TextField("tentang", max_length=500, blank=True)
    location = models.CharField("lokasi", max_length=100, blank=True)
    photo = models.ImageField("foto profil", upload_to="profile/", blank=True)
    linkedin_url = models.URLField("URL LinkedIn", blank=True)
    github_url = models.URLField("URL GitHub", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "profil situs"
        verbose_name_plural = "profil situs"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        profile = cls.objects.filter(pk=1).first()
        return profile or cls(pk=1)


class Tag(models.Model):
    name = models.CharField("nama", max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "tag"
        verbose_name_plural = "tags"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:60] or "tag"
            candidate = base
            number = 2
            while Tag.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f"{base[:55]}-{number}"
                number += 1
            self.slug = candidate
        super().save(*args, **kwargs)


class Book(models.Model):
    class Status(models.TextChoices):
        WANT = "want", "Want to Read"
        READING = "reading", "Reading"
        FINISHED = "finished", "Finished"
        FAVORITE = "favorite", "Favorite"

    title = models.CharField("judul", max_length=220)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    author = models.CharField("penulis", max_length=160)
    cover = models.ImageField("sampul buku", upload_to="books/", blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.WANT)
    progress = models.PositiveSmallIntegerField(
        "progres (%)", default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    current_chapter = models.PositiveSmallIntegerField("bab saat ini", null=True, blank=True)
    total_chapters = models.PositiveSmallIntegerField("jumlah bab", null=True, blank=True)
    started_at = models.DateField("mulai membaca", null=True, blank=True)
    finished_at = models.DateField("selesai membaca", null=True, blank=True)
    rating = models.DecimalField(
        "rating", max_digits=2, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    thoughts = models.TextField("pemikiran saya", blank=True)
    lessons = models.TextField("hal yang dipelajari", blank=True, help_text="Satu pelajaran per baris.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-started_at", "title"]
        verbose_name = "buku"
        verbose_name_plural = "buku"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:220] or "book"
            candidate = base
            number = 2
            while Book.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f"{base[:214]}-{number}"
                number += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:book_detail", kwargs={"slug": self.slug})

    @property
    def lessons_list(self):
        return [line.strip(" •-\t") for line in self.lessons.splitlines() if line.strip(" •-\t")]


class BookNote(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="notes")
    heading = models.CharField("judul catatan", max_length=140)
    body = models.TextField("isi catatan")
    order = models.PositiveSmallIntegerField("urutan", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "catatan buku"
        verbose_name_plural = "catatan buku"

    def __str__(self):
        return f"{self.book}: {self.heading}"


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draf"
        PUBLISHED = "published", "Terbit"

    title = models.CharField("judul", max_length=220)
    slug = models.SlugField(max_length=240, unique=True)
    excerpt = models.TextField("ringkasan", max_length=320, blank=True)
    body = models.TextField("isi")
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="posts")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField("waktu terbit", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:detail", kwargs={"slug": self.slug})


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField("nama", max_length=80)
    email = models.EmailField("email")
    body = models.TextField("komentar", max_length=2000)
    is_approved = models.BooleanField("disetujui", default=False)
    created_at = models.DateTimeField("dikirim pada", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "komentar"
        verbose_name_plural = "komentar"

    def __str__(self):
        return f"{self.name} di {self.post}"
