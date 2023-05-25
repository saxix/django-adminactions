import csv
from pathlib import Path

from webtest import Upload

from demo.models import DemoModel
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import G
from django_webtest import WebTestMixin
from unittest.mock import patch
from utils import CheckSignalsMixin, SelectRowsMixin, user_grant_permission

__all__ = [
    "BulkUpdateTest",
]


class BulkUpdateTest(SelectRowsMixin, CheckSignalsMixin, WebTestMixin, TestCase):
    fixtures = ["adminactions", "demoproject"]
    urls = "demo.urls"
    csrf_checks = True

    _selected_rows = [0, 1]

    action_name = "bulk_update"
    sender_model = DemoModel

    def setUp(self):
        super().setUp()
        self._url = reverse("admin:demo_demomodel_changelist")
        self.user = G(User, username="user", is_staff=True, is_active=True)

    def _run_action(self, steps=2, **kwargs):
        selected_rows = kwargs.pop("selected_rows", self._selected_rows)
        select_across = kwargs.pop("select_across", False)
        with user_grant_permission(
            self.user,
            ["demo.change_demomodel", "demo.adminactions_bulkupdate_demomodel"],
        ):
            res = self.app.get("/", user="user", auto_follow=False)
            res = res.click("Demo models")
            if steps >= 1:
                form = res.forms["changelist-form"]
                form["action"] = "bulk_update"
                form["select_across"] = select_across
                self._select_rows(form, selected_rows)
                res = form.submit()
            if steps >= 2:
                res.forms["bulk-update"]["_file"] = Upload(
                    str(Path(__file__).parent / "bulk_update.csv")
                )
                res.forms["bulk-update"]["fld-integer"] = "number"
                res.forms["bulk-update"]["fld-char"] = "name"
                res.forms["bulk-update"]["fld-id"] = "pk"
                res.forms["bulk-update"]["fld-index_field"] = ["id"]
                res.forms["bulk-update"]["fld-id"] = "pk"
                res.forms["bulk-update"]["csv-delimiter"] = ","
                res.forms["bulk-update"]["csv-quoting"] = csv.QUOTE_NONE

                for k, v in kwargs.items():
                    res.forms["bulk-update"][k] = v
                res = res.forms["bulk-update"].submit("apply")
        return res

    def test_no_permission(self):
        with user_grant_permission(self.user, ["demo.change_demomodel"]):
            res = self.app.get("/", user="user")
            res = res.click("Demo models")
            form = res.forms["changelist-form"]
            form["action"] = "bulk_update"
            form.set("_selected_action", True, 0)
            res = form.submit().follow()
            assert "Sorry you do not have rights to execute this action" in str(
                res.body
            )

    def test_no_header(self):
        self._run_action(
            **{
                "_clean": 1,
                "_validate": 1,
                "select_across": 1,
                "csv-header": False,
                "_file": Upload(
                    "data.csv",
                    b"1,aaa,111\n2,bbb,222\n3,ccc,333",
                    "text/csv",
                ),
                "fld-id": "1",
                "fld-char": "2",
                "fld-integer": "3",
            }
        )
        assert DemoModel.objects.filter(char="aaa", integer=111).exists()
        assert DemoModel.objects.filter(char="bbb", integer=222).exists()

    def test_clean_on(self):
        self._run_action(
            **{
                "_clean": 1,
                "_validate": 1,
                "select_across": 1,
                "_file": Upload(
                    "data.csv",
                    b"pk,name,number\n1,aaa,111\n2,bbb,222\n3,ccc,333",
                    "text/csv",
                ),
                "fld-char": "name",
                "fld-integer": "number",
            }
        )

        assert DemoModel.objects.filter(char="aaa").exists()
        assert DemoModel.objects.filter(char="bbb").exists()

    def test_messages(self):
        with user_grant_permission(
            self.user,
            ["demo.change_demomodel", "demo.adminactions_bulkupdate_demomodel"],
        ):
            res = self._run_action(            **{
                "select_across": 1,
                "_file": Upload(
                    "data.csv",
                    b"pk,name,number\n1,aaa,111\n2,bbb,222\n3,ccc,333",
                    "text/csv",
                ),
                "fld-char": "name",
                "fld-integer": "number",
            })
            res = res.follow()
            messages = [m.message for m in list(res.context["messages"])]

            self.assertTrue(messages)
            assert "Updated" in messages[0]

            res = self._run_action(selected_rows=[1]).follow()
            messages = [m.message for m in list(res.context["messages"])]
            self.assertTrue(messages)
            assert "Updated" in messages[0]

    def test_index_required(self):
        res = self._run_action(**{"_async": 0, "_validate": 0, "fld-index_field": []})
        assert res.status_code == 200
        assert res.context["map_form"].errors == {
            "index_field": ["Please select one or more index fields"]
        }

    def test_wrong_mapping(self):

        res = self._run_action(
            **{
                "_file": Upload(
                    "data.csv",
                    b"pk,name,number\n1,aaa,111\n2,bbb,222\n3,ccc,333",
                    "text/csv",
                ),
                "fld-index_field": ["id"],
                "fld-id": "miss",
            }
        )
        assert res.status_code == 200
        messages = [m.message for m in list(res.context['messages'])]
        assert messages[0] == "['miss column is not present in the file']"

    def test_async_qs(self):
        # Create handler
        G(DemoModel, id=1, char="char1", integer=100)
        G(DemoModel, id=2, char="char2", integer=101)
        G(DemoModel, id=3, char="char3", integer=102)

        res = self._run_action(
            **{
                "_async": 1,
                "_validate": 0,
                "_file": Upload(
                    "data.csv",
                    b"pk,name,number\n1,aaa,111\n2,bbb,222\n3,ccc,333",
                    "text/csv",
                ),
                "fld-index_field": ["id"],
                "fld-id": "pk",
                "fld-char": "name",
                "fld-integer": "number",
            }
        )
        assert res.status_code == 302, res.showbrowser()
        assert DemoModel.objects.filter(id=1, char="char1").exists()

    @patch("adminactions.bulk_update.adminaction_end.send")
    @patch("adminactions.bulk_update.adminaction_start.send")
    @patch("adminactions.bulk_update.adminaction_requested.send")
    def test_async_single(self, req, start, end):
        G(DemoModel, id=1, char="char1", integer=100)
        G(DemoModel, id=2, char="char2", integer=101)
        G(DemoModel, id=3, char="char3", integer=102)
        res = self._run_action(
            **{
                "_async": 1,
                "_validate": 1,
                "select_across": 1,
                "_file": Upload(
                    "data.csv",
                    b"pk,name,number\n1,aaa,111\n2,bbb,222\n3,ccc,333",
                    "text/csv",
                ),
                "fld-char": "name",
                "fld-integer": "number",
            }
        )
        assert res.status_code == 302
        assert req.called
        assert start.called
        assert end.called
        assert DemoModel.objects.filter(char="aaa").exists()
        assert DemoModel.objects.filter(char="bbb").exists()
