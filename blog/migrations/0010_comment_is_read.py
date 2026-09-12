from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("blog", "0009_convert_book_journal_to_rich_text")]

    operations = [
        migrations.AddField(
            model_name="comment",
            name="is_read",
            field=models.BooleanField(default=False, verbose_name="sudah dibaca"),
        ),
    ]
