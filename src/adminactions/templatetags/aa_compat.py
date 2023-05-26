from django.template import Library

register = Library()


@register.tag
def url(parser, token):
    from django.template.defaulttags import url as _url

    return _url(parser, token)
