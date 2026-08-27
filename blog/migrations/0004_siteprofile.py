from django.db import migrations, models


def create_default_profile(apps, schema_editor):
    SiteProfile = apps.get_model("blog", "SiteProfile")
    SiteProfile.objects.get_or_create(
        pk=1,
        defaults={
            "name": "Dony Wijaya",
            "headline": "Penulis di Ruang Tulis",
            "bio": "Berbagi ide, catatan, dan pengalaman melalui tulisan.",
        },
    )


class Migration(migrations.Migration):
    dependencies = [("blog", "0003_comment")]
    operations = [
        migrations.CreateModel(
            name="SiteProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="Dony Wijaya", max_length=100, verbose_name="nama")),
                ("headline", models.CharField(blank=True, max_length=160, verbose_name="headline")),
                ("bio", models.TextField(blank=True, max_length=500, verbose_name="tentang")),
                ("location", models.CharField(blank=True, max_length=100, verbose_name="lokasi")),
                ("photo", models.ImageField(blank=True, upload_to="profile/", verbose_name="foto profil")),
                ("linkedin_url", models.URLField(blank=True, verbose_name="URL LinkedIn")),
                ("website_url", models.URLField(blank=True, verbose_name="URL situs pribadi")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "profil situs", "verbose_name_plural": "profil situs"},
        ),
        migrations.RunPython(create_default_profile, migrations.RunPython.noop),
    ]
