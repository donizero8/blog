from django.db import migrations


OLD_HEADLINE = "Penulis di Ruang Tulis"
NEW_HEADLINE = "Penulis di Dony’s Notebook"


def update_default_headline(apps, schema_editor):
    site_profile = apps.get_model("blog", "SiteProfile")
    site_profile.objects.filter(headline=OLD_HEADLINE).update(headline=NEW_HEADLINE)


def restore_default_headline(apps, schema_editor):
    site_profile = apps.get_model("blog", "SiteProfile")
    site_profile.objects.filter(headline=NEW_HEADLINE).update(headline=OLD_HEADLINE)


class Migration(migrations.Migration):
    dependencies = [("blog", "0006_book_booknote")]

    operations = [
        migrations.RunPython(update_default_headline, restore_default_headline),
    ]
