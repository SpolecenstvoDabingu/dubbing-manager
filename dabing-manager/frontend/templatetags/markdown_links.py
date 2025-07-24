from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
from database.utils import MARKDOWN_LINK_RE

register = template.Library()

@register.filter
def markdown_links(text):
    if not text:
        return ''

    text = escape(text)

    def repl(match):
        label = match.group(1)
        url = match.group(2)
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{label}</a>'

    return mark_safe(MARKDOWN_LINK_RE.sub(repl, text))