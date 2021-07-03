from datetime import datetime
from django.http import HttpResponse
from django.utils import dateformat


def format_date(request):
    d = datetime.now()
    return HttpResponse(dateformat.format(d, request.GET.get('fmt', '')))

