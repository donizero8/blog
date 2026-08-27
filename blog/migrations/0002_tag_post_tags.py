from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("blog", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=60, unique=True, verbose_name="nama")),
                ("slug", models.SlugField(blank=True, max_length=70, unique=True)),
            ],
            options={"verbose_name": "tag", "verbose_name_plural": "tags", "ordering": ["name"]},
        ),
        migrations.AddField(
            model_name="post",
            name="tags",
            field=models.ManyToManyField(blank=True, related_name="posts", to="blog.tag"),
        ),
    ]
