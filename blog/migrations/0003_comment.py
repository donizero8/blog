import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("blog", "0002_tag_post_tags")]
    operations = [
        migrations.CreateModel(
            name="Comment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, verbose_name="nama")),
                ("email", models.EmailField(max_length=254, verbose_name="email")),
                ("body", models.TextField(max_length=2000, verbose_name="komentar")),
                ("is_approved", models.BooleanField(default=False, verbose_name="disetujui")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="dikirim pada")),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="comments", to="blog.post")),
            ],
            options={"verbose_name": "komentar", "verbose_name_plural": "komentar", "ordering": ["created_at"]},
        )
    ]
