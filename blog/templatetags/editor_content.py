from django import template
from django.utils.safestring import mark_safe

from blog.forms import sanitize_editor_html

register = template.Library()


@register.filter
def editor_content(value):
    return mark_safe(sanitize_editor_html(value or ""))
