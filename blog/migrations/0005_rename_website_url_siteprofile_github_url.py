from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("blog", "0004_siteprofile")]
    operations = [
        migrations.RenameField(
            model_name="siteprofile",
            old_name="website_url",
            new_name="github_url",
        ),
        migrations.AlterField(
            model_name="siteprofile",
            name="github_url",
            field=models.URLField(blank=True, verbose_name="URL GitHub"),
        ),
    ]
