from __future__ import annotations

from typing import NoReturn
from unittest import mock

import pytest
from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.db.transaction import atomic
from django.test import TransactionTestCase
from django.urls.base import reverse
from django_dynamic_fixture import G

from adminactions import compat
from adminactions.api import merge
from adminactions.compat import nocommit
from adminactions.exceptions import ActionInterruptedError
from adminactions.signals import adminaction_end

pytestmarker = pytest.mark.skip


@pytest.mark.django_db
def test_nocommit() -> None:
    with nocommit():
        G(Group, name="name")
    assert not Group.objects.filter(name="name").exists()


@pytest.mark.django_db
def test_transaction_merge(users) -> None:
    master, other = users
    with atomic():
        with mock.patch("django.contrib.auth.models.User.delete", side_effect=IntegrityError):
            with pytest.raises(IntegrityError):
                merge(master, other, commit=True)

        assert User.objects.filter(pk=master.pk).exists()
        assert User.objects.filter(pk=other.pk).exists()

        assert master.first_name != other.first_name


@pytest.mark.django_db
def test_transaction_mass_update(app, users, administrator) -> None:
    assert User.objects.filter(is_staff=True).count() == 1  # sanity check

    def _handler(*args, **kwargs) -> NoReturn:
        raise ActionInterruptedError

    with atomic():
        res = app.get(reverse("admin:index"), user=administrator.username)
        res = res.click("Users")
        form = res.forms["changelist-form"]
        form["action"] = "mass_update"

        form.get("_selected_action", index=0).checked = True
        form.get("_selected_action", index=1).checked = True
        form.get("_selected_action", index=2).checked = True

        res = form.submit()
        res.forms["mass-update-form"]["chk_id_is_staff"].checked = True
        res.forms["mass-update-form"]["is_staff"].checked = True

        # res.form.submit('apply').follow()
        # assert User.objects.filter(is_staff=True).count() == 1

        with pytest.raises(BaseException):
            adminaction_end.connect(_handler)
            res.forms["mass-update-form"].submit("apply").follow()
            assert res.status_code == 302
            adminaction_end.disconnect(_handler)

        assert User.objects.filter(is_staff=True).count() == 1


class TestIsLibero(TransactionTestCase):
    def test_true(self) -> None:
        assert True
