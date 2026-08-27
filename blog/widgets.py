from django import forms

class MediumEditorWidget(forms.Textarea):
    template_name = "blog/admin/widgets/medium_editor.html"

    class Media:
        css = {"all": ("blog/admin/editor.css",)}
        js = ("blog/admin/editor.js",)


class TagInputWidget(forms.TextInput):
    template_name = "blog/admin/widgets/tag_input.html"

    def __init__(self, suggestions=None, attrs=None):
        super().__init__(attrs)
        self.suggestions = suggestions or []

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["suggestions"] = self.suggestions
        return context

    class Media:
        css = {"all": ("blog/admin/tags.css",)}
        js = ("blog/admin/tags.js",)
