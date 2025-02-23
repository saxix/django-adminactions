from datetime import datetime

import django.utils.timezone
from django.http import HttpResponse
from django.http.request import HttpRequest
from django.utils import dateformat


def format_date(request: HttpRequest) -> HttpResponse:
    d = datetime.now(tz=django.utils.timezone.get_current_timezone())
    fmt: str = request.GET.get("fmt", "")
    return HttpResponse(dateformat.format(d, fmt))
