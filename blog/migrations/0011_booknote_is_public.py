from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("blog", "0010_comment_is_read")]

    operations = [
        migrations.AddField(
            model_name="booknote",
            name="is_public",
            field=models.BooleanField(default=False, verbose_name="tampilkan di situs", help_text="Centang agar isi catatan dapat dilihat pengunjung."),
        ),
    ]
