from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.urls.base import reverse
from django_webtest import DjangoTestApp
from webtest import Upload


def test_import_fixture_by_content(app: DjangoTestApp, admin_user: User) -> None:
    fixtures = Path(__file__).parent / "demo" / "fixtures" / "demoproject.json"
    url = reverse("admin:demo_demomodel_changelist")
    res = app.get(url, user=admin_user)
    res = res.click("Import Fixture")
    res.forms["import-form"]["fixture_content"] = fixtures.read_text()
    res = res.forms["import-form"].submit()
    assert "3 objects imported" in res.text


@pytest.mark.xfail(raises=AssertionError)
def test_import_fixture_by_file(app: DjangoTestApp, admin_user: User) -> None:
    fixtures = Path(__file__).parent / "demo" / "fixtures" / "demoproject.json"
    url = reverse("admin:demo_demomodel_changelist")
    res = app.get(url, user=admin_user)
    res = res.click("Import Fixture")
    res.forms["import-form"]["fixture_file"] = Upload(str(fixtures))
    res = res.forms["import-form"].submit().follow()
    assert "3 objects imported" in res.text
