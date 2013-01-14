# -*- coding: utf-8 -*-
from django.contrib.auth.models import User

from django.utils.translation import gettext as _
from .common import BaseTestCase


class MergeTest(BaseTestCase):
    urls = "adminactions.tests.urls"

    def test_merge(self):
        print User.objects.all()
