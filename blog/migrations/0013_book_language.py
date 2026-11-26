from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('blog', '0012_post_language_postslug')]
    operations = [
        migrations.AddField(model_name='book', name='language', field=models.CharField(choices=[('id', 'Indonesia'), ('en', 'Inggris')], default='en', max_length=2, verbose_name='bahasa')),
        migrations.AlterField(model_name='book', name='language', field=models.CharField(choices=[('id', 'Indonesia'), ('en', 'Inggris')], default='id', max_length=2, verbose_name='bahasa')),
    ]
