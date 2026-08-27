import datetime
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


def create_sample_book(apps, schema_editor):
    Book = apps.get_model("blog", "Book")
    BookNote = apps.get_model("blog", "BookNote")
    book, _ = Book.objects.get_or_create(
        slug="code-complete",
        defaults={
            "title": "Code Complete",
            "author": "Steve McConnell",
            "status": "reading",
            "progress": 38,
            "current_chapter": 12,
            "total_chapters": 35,
            "started_at": datetime.date(2026, 8, 16),
            "thoughts": "A practical reading journal about building software carefully and improving the way code is constructed.",
            "lessons": "Defensive programming\nCode construction\nSoftware quality",
        },
    )
    BookNote.objects.get_or_create(book=book, heading="Chapter 5", defaults={"body": "Notes about designing routines that are easy to understand and maintain.", "order": 1})
    BookNote.objects.get_or_create(book=book, heading="Chapter 8", defaults={"body": "A useful reminder to make complexity visible before trying to manage it.", "order": 2})


class Migration(migrations.Migration):
    dependencies = [("blog", "0005_rename_website_url_siteprofile_github_url")]
    operations = [
        migrations.CreateModel(
            name="Book",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=220, verbose_name="judul")),
                ("slug", models.SlugField(blank=True, max_length=240, unique=True)),
                ("author", models.CharField(max_length=160, verbose_name="penulis")),
                ("cover", models.ImageField(blank=True, upload_to="books/", verbose_name="sampul buku")),
                ("status", models.CharField(choices=[("want", "Want to Read"), ("reading", "Reading"), ("finished", "Finished"), ("favorite", "Favorite")], default="want", max_length=12)),
                ("progress", models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name="progres (%)")),
                ("current_chapter", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="bab saat ini")),
                ("total_chapters", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="jumlah bab")),
                ("started_at", models.DateField(blank=True, null=True, verbose_name="mulai membaca")),
                ("finished_at", models.DateField(blank=True, null=True, verbose_name="selesai membaca")),
                ("rating", models.DecimalField(blank=True, decimal_places=1, max_digits=2, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)], verbose_name="rating")),
                ("thoughts", models.TextField(blank=True, verbose_name="pemikiran saya")),
                ("lessons", models.TextField(blank=True, help_text="Satu pelajaran per baris.", verbose_name="hal yang dipelajari")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "buku", "verbose_name_plural": "buku", "ordering": ["-started_at", "title"]},
        ),
        migrations.CreateModel(
            name="BookNote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("heading", models.CharField(max_length=140, verbose_name="judul catatan")),
                ("body", models.TextField(verbose_name="isi catatan")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="urutan")),
                ("book", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notes", to="blog.book")),
            ],
            options={"verbose_name": "catatan buku", "verbose_name_plural": "catatan buku", "ordering": ["order", "id"]},
        ),
        migrations.RunPython(create_sample_book, migrations.RunPython.noop),
    ]
