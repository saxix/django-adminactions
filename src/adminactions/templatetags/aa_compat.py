from django.template import Library

register = Library()


@register.tag
def url(parser, token):
    # try:
    #     from django.templatetags.future import url as _url
    # except:
    from django.template.defaulttags import url as _url
    return _url(parser, token)
