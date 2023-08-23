# from adminactions.signals import adminaction_requested, adminaction_start, adminaction_end
from pathlib import Path
from unittest import skipIf
from unittest.mock import patch

from demo.models import (
    DemoModel,
    DemoModelAdmin,
    DemoModelMassUpdateForm,
    TestMassUpdateForm,
)
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import fields
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django_dynamic_fixture import G
from django_webtest import WebTestMixin
from utils import CheckSignalsMixin, SelectRowsMixin, user_grant_permission
from webtest import Upload

from adminactions import config
from adminactions.compat import celery_present
from adminactions.mass_update import OPERATIONS

__all__ = [
    "MassUpdateTest",
]


def test_operationmanager_get():
    assert OPERATIONS[fields.IntegerField] == OPERATIONS[fields.BigIntegerField]
    assert OPERATIONS[fields.BooleanField] == OPERATIONS[fields.NullBooleanField]


def test_operationmanager_get_for_field():
    assert list(OPERATIONS[fields.CharField].keys()) == [
        "set",
        "set null",
        "upper",
        "lower",
        "capitalize",
        "trim",
    ]
    assert list(OPERATIONS.get_for_field(fields.CharField(null=True)).keys()) == [
        "set",
        "set null",
        "upper",
        "lower",
        "capitalize",
        "trim",
    ]


class MassUpdateTest(SelectRowsMixin, CheckSignalsMixin, WebTestMixin, TestCase):
    fixtures = ["adminactions", "demoproject"]
    urls = "demo.urls"
    csrf_checks = True

    _selected_rows = [0, 1]

    action_name = "mass_update"
    sender_model = DemoModel

    def setUp(self):
        super().setUp()
        self._url = reverse("admin:demo_demomodel_changelist")
        self.user = G(User, username="user", is_staff=True, is_active=True)

    def _run_action(self, steps=2, **kwargs):
        selected_rows = kwargs.pop("selected_rows", self._selected_rows)
        with user_grant_permission(
            self.user,
            ["demo.change_demomodel", "demo.adminactions_massupdate_demomodel"],
        ):
            res = self.app.get("/", user="user")
            res = res.click("Demo models")
            if steps >= 1:
                form = res.forms["changelist-form"]
                form["action"] = "mass_update"
                self._select_rows(form, selected_rows)
                res = form.submit()
            if steps >= 2:
                res.forms["mass-update-form"]["chk_id_char"].checked = True
                res.forms["mass-update-form"]["func_id_char"] = "upper"
                res.forms["mass-update-form"]["chk_id_choices"].checked = True
                res.forms["mass-update-form"]["func_id_choices"] = "set"
                res.forms["mass-update-form"]["choices"] = "1"
                for k, v in kwargs.items():
                    res.forms["mass-update-form"][k] = v
                res = res.forms["mass-update-form"].submit("apply")
        return res

    def test_no_permission(self):
        with user_grant_permission(self.user, ["demo.change_demomodel"]):
            res = self.app.get("/", user="user")
            res = res.click("Demo models")
            form = res.forms["changelist-form"]
            form["action"] = "mass_update"
            form.set("_selected_action", True, 0)
            res = form.submit().follow()
            assert "Sorry you do not have rights to execute this action" in str(
                res.body
            )

    def test_custom_modeladmin_form(self):
        DemoModelAdmin.mass_update_form = DemoModelMassUpdateForm
        with user_grant_permission(
            self.user,
            ["demo.change_demomodel", "demo.adminactions_massupdate_demomodel"],
        ):
            res = self.app.get("/", user="user")
            res = res.click("Demo models")
            form = res.forms["changelist-form"]
            form["action"] = "mass_update"
            self._select_rows(form, [0, 1])
            res = form.submit()

            assert isinstance(res.context["adminform"].form, DemoModelMassUpdateForm)

    def test_custom_form(self):
        with override_settings(AA_MASSUPDATE_FORM="demo.models.TestMassUpdateForm"):
            config.AA_MASSUPDATE_FORM = settings.AA_MASSUPDATE_FORM
            with user_grant_permission(
                self.user,
                ["demo.change_demomodel", "demo.adminactions_massupdate_demomodel"],
            ):
                res = self.app.get("/", user="user")
                res = res.click("Demo models")
                form = res.forms["changelist-form"]
                form["action"] = "mass_update"
                self._select_rows(form, [0, 1])
                res = form.submit()

        config.AA_MASSUPDATE_FORM = "adminactions.mass_update.MassUpdateForm"
        assert isinstance(res.context["adminform"].form, TestMassUpdateForm)

    def test_validate_on(self):
        self._run_action(**{"_validate": 1})
        assert DemoModel.objects.filter(char="CCCCC").exists()
        assert not DemoModel.objects.filter(char="ccccc").exists()

    def test_validate_off(self):
        res = self._run_action(**{"_validate": 0})
        assert res.status_code == 200
        form = res.context["adminform"].form
        assert form.errors["__all__"] == ["Cannot use operators without 'validate'"]

    def test_clean_on(self):
        self._run_action(**{"_clean": 1})

        assert DemoModel.objects.filter(char="CCCCC").exists()
        assert not DemoModel.objects.filter(char="ccccc").exists()

    def test_messages(self):
        with user_grant_permission(
            self.user,
            ["demo.change_demomodel", "demo.adminactions_massupdate_demomodel"],
        ):
            res = self._run_action(**{"_clean": 1})
            res = res.follow()
            messages = [m.message for m in list(res.context["messages"])]
            self.assertTrue(messages)
            self.assertEqual("Updated 2 records", messages[0])

            res = self._run_action(selected_rows=[1]).follow()
            messages = [m.message for m in list(res.context["messages"])]
            self.assertTrue(messages)
            self.assertEqual("Updated 1 records", messages[0])

    @skipIf(not celery_present, "Celery not installed")
    def test_async_qs(self):
        # Create handler

        res = self._run_action(**{"_async": 1, "_validate": 0, "chk_id_char": False})
        assert res.status_code == 302
        assert DemoModel.objects.filter(choices=1).exists()

    @patch("adminactions.mass_update.adminaction_end.send")
    @patch("adminactions.mass_update.adminaction_start.send")
    @patch("adminactions.mass_update.adminaction_requested.send")
    @skipIf(not celery_present, "Celery not installed")
    def test_async_single(self, req, start, end):
        res = self._run_action(**{"_async": 1, "_validate": 1})
        assert res.status_code == 302
        assert req.called
        assert start.called
        assert end.called
        assert DemoModel.objects.filter(char="CCCCC").exists()
        assert not DemoModel.objects.filter(char="ccccc").exists()

    def test_file_field(self):
        self._run_action(
            **{
                "_validate": 1,
                "select_across": 1,
                "chk_id_image": True,
                "image": Upload(str(Path(__file__).parent / "test.jpeg")),
            }
        )
        obj1 = DemoModel.objects.get(pk=1)
        obj2 = DemoModel.objects.get(pk=2)
        assert obj1.image.read() == obj2.image.read()

    def test_file_field_prevent_async(self):
        res = self._run_action(
            **{
                "_async": 1,
                "select_across": 1,
                "chk_id_image": True,
                "image": Upload(str(Path(__file__).parent / "test.jpeg")),
            }
        )
        assert res.status_code == 200
