from django.template import Library
from django.template.base import Parser, Token

register = Library()


@register.tag
def url(parser: Parser, token: Token) -> str:
    from django.template.defaulttags import url as _url

    return _url(parser, token)
