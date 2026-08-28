from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("blog", "0007_update_default_branding")]

    operations = [
        migrations.AddField(
            model_name="siteprofile",
            name="hero_title",
            field=models.CharField(
                default="Books, English, code, and things I learn.",
                max_length=160,
                verbose_name="judul beranda",
            ),
        ),
        migrations.AddField(
            model_name="siteprofile",
            name="hero_description",
            field=models.CharField(
                default="Tempat sederhana untuk menulis hal-hal yang layak diingat.",
                max_length=240,
                verbose_name="deskripsi beranda",
            ),
        ),
    ]
