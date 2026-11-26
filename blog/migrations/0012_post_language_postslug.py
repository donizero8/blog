from django.db import migrations, models
import django.db.models.deletion


def reserve_existing_slugs(apps, schema_editor):
    Post = apps.get_model('blog', 'Post')
    PostSlug = apps.get_model('blog', 'PostSlug')
    alias = schema_editor.connection.alias
    for post in Post.objects.using(alias).all().iterator():
        PostSlug.objects.using(alias).create(post_id=post.pk, slug=post.slug)


class Migration(migrations.Migration):
    dependencies = [('blog', '0011_booknote_is_public')]
    operations = [
        migrations.AddField(model_name='post', name='language', field=models.CharField(choices=[('id', 'Indonesia'), ('en', 'Inggris')], default='en', max_length=2, verbose_name='bahasa')),
        migrations.AlterField(model_name='post', name='language', field=models.CharField(choices=[('id', 'Indonesia'), ('en', 'Inggris')], default='id', max_length=2, verbose_name='bahasa')),
        migrations.CreateModel(name='PostSlug', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('slug', models.SlugField(max_length=240, unique=True)),
            ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slug_history', to='blog.post')),
        ]),
        migrations.RunPython(reserve_existing_slugs, migrations.RunPython.noop),
    ]
