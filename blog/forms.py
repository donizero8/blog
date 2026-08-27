import bleach
from io import BytesIO
from pathlib import Path

from django import forms
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

from .models import Book, Comment, Post, SiteProfile, Tag
from .widgets import MediumEditorWidget, TagInputWidget

ALLOWED_TAGS = ["p", "br", "h2", "h3", "strong", "em", "u", "s", "a", "blockquote", "ul", "ol", "li", "pre", "code", "img"]


def optimize_uploaded_image(upload, size, suffix):
    if not upload or getattr(upload, "_committed", False):
        return upload
    upload.seek(0)
    with Image.open(upload) as source:
        image = ImageOps.exif_transpose(source)
        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, "white")
            background.paste(rgba, mask=rgba.getchannel("A"))
            image = background
        else:
            image = image.convert("RGB")
        image = ImageOps.fit(image, size, method=Image.Resampling.LANCZOS)
        output = BytesIO()
        image.save(output, format="WEBP", quality=82, method=6, optimize=True)
    filename = f"{Path(upload.name).stem}-{suffix}.webp"
    return ContentFile(output.getvalue(), name=filename)


def optimize_article_image(upload):
    upload.seek(0)
    with Image.open(upload) as source:
        image = ImageOps.exif_transpose(source)
        if image.width * image.height > 25_000_000:
            raise ValueError("Resolusi gambar terlalu besar.")
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA" if "transparency" in image.info else "RGB")
        image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        width, height = image.size
        output = BytesIO()
        image.save(output, format="WEBP", quality=82, method=6, optimize=True)
    return ContentFile(output.getvalue(), name="article-image.webp"), width, height

class PostAdminForm(forms.ModelForm):
    tags_input = forms.CharField(label="Tags", required=False)

    class Meta:
        model = Post
        exclude = ("tags",)
        widgets = {"body": MediumEditorWidget()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        suggestions = list(Tag.objects.values_list("name", flat=True))
        self.fields["tags_input"].widget = TagInputWidget(suggestions=suggestions)
        if self.instance.pk:
            self.initial["tags_input"] = ", ".join(self.instance.tags.values_list("name", flat=True))

    def clean_body(self):
        return bleach.clean(
            self.cleaned_data["body"],
            tags=ALLOWED_TAGS,
            attributes={
                "a": ["href", "title", "target", "rel"],
                "img": ["src", "alt", "class", "loading", "width", "height"],
            },
            protocols=["http", "https", "mailto"],
            strip=True,
        )

    def clean_tags_input(self):
        raw_names = self.cleaned_data.get("tags_input", "").split(",")
        names = []
        seen = set()
        for raw_name in raw_names:
            name = " ".join(raw_name.strip().split())[:60]
            key = name.casefold()
            if name and key not in seen:
                names.append(name)
                seen.add(key)
        if len(names) > 12:
            raise forms.ValidationError("Maksimal 12 tag untuk satu tulisan.")
        return ", ".join(names)

    def _save_m2m(self):
        super()._save_m2m()
        tags = []
        for name in self.cleaned_data.get("tags_input", "").split(", "):
            if not name:
                continue
            tag = Tag.objects.filter(name__iexact=name).first()
            if not tag:
                tag = Tag.objects.create(name=name)
            tags.append(tag)
        self.instance.tags.set(tags)


class CommentForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput, label="")

    class Meta:
        model = Comment
        fields = ("name", "email", "body")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Nama Anda", "autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"placeholder": "nama@email.com", "autocomplete": "email"}),
            "body": forms.Textarea(attrs={"placeholder": "Tulis komentar…", "rows": 5}),
        }

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Komentar tidak dapat diproses.")
        return ""


class SiteProfileAdminForm(forms.ModelForm):
    class Meta:
        model = SiteProfile
        fields = "__all__"

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo and getattr(photo, "size", 0) > 3 * 1024 * 1024:
            raise forms.ValidationError("Ukuran foto maksimal 3 MB.")
        return optimize_uploaded_image(photo, (416, 416), "profile")


class BookAdminForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = "__all__"

    def clean_cover(self):
        cover = self.cleaned_data.get("cover")
        if cover and getattr(cover, "size", 0) > 5 * 1024 * 1024:
            raise forms.ValidationError("Ukuran sampul maksimal 5 MB.")
        return optimize_uploaded_image(cover, (300, 424), "cover")
