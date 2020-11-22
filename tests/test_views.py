import datetime

import pytest
from django.urls import reverse
from django.utils import dateformat
from django.utils.encoding import smart_str


@pytest.mark.django_db()
def test_format_date(app):
    d = datetime.datetime.now()

    url = reverse('adminactions.format_date')
    fmt = 'd-m-Y'
    res = app.get("{}?fmt={}".format(url, fmt))
    assert smart_str(res.body) == dateformat.format(d, fmt)

    fmt = 'd mm Y'
    res = app.get("{}?fmt={}".format(url, fmt))
    assert smart_str(res.body) == dateformat.format(d, fmt)
