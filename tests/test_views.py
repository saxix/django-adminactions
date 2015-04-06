# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest
import datetime
from django.core.urlresolvers import reverse
from django.utils import dateformat


@pytest.mark.django_db(transaction=True)
def test_format_date(app):
    d = datetime.datetime.now()

    url = reverse('adminactions.format_date')
    fmt = 'd-m-Y'
    res = app.get("{}?fmt={}".format(url, fmt))
    assert res.body == dateformat.format(d, fmt)

    fmt = 'd mm Y'
    res = app.get("{}?fmt={}".format(url, fmt))
    assert res.body == dateformat.format(d, fmt)
