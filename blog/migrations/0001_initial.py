import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(
        name="Post",
        fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("title", models.CharField(max_length=220, verbose_name="judul")),
            ("slug", models.SlugField(max_length=240, unique=True)),
            ("excerpt", models.TextField(blank=True, max_length=320, verbose_name="ringkasan")),
            ("body", models.TextField(verbose_name="isi")),
            ("status", models.CharField(choices=[("draft", "Draf"), ("published", "Terbit")], default="draft", max_length=12)),
            ("published_at", models.DateTimeField(blank=True, null=True, verbose_name="waktu terbit")),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("author", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="posts", to=settings.AUTH_USER_MODEL)),
        ],
        options={"ordering": ["-published_at", "-created_at"]},
    )]

