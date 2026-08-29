import bleach

from django.db import migrations
from django.utils.html import linebreaks


ALLOWED_TAGS = [
    "p", "br", "h2", "h3", "strong", "em", "u", "s", "a",
    "blockquote", "ul", "ol", "li", "pre", "code", "img",
]


def convert_book_journal(apps, schema_editor):
    Book = apps.get_model("blog", "Book")
    BookNote = apps.get_model("blog", "BookNote")
    sanitizer = bleach.sanitizer.Cleaner(
        tags=ALLOWED_TAGS,
        attributes={
            "a": ["href", "title", "target", "rel"],
            "img": ["src", "alt", "class", "loading", "width", "height"],
        },
        protocols=["http", "https", "mailto"],
        strip=True,
    )

    for book in Book.objects.exclude(thoughts="").iterator():
        book.thoughts = sanitizer.clean(linebreaks(book.thoughts))
        book.save(update_fields=["thoughts"])

    for note in BookNote.objects.exclude(body="").iterator():
        note.body = sanitizer.clean(linebreaks(note.body))
        note.save(update_fields=["body"])


class Migration(migrations.Migration):
    dependencies = [("blog", "0008_siteprofile_homepage_copy")]
    operations = [migrations.RunPython(convert_book_journal, migrations.RunPython.noop)]
