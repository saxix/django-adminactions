import csv
from pathlib import Path

from demo.models import DemoModel, DemoOneToOne
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import G
from django_webtest import WebTestMixin
from utils import CheckSignalsMixin, SelectRowsMixin, user_grant_permission
from webtest import Upload

__all__ = [
    "BulkUpdateMemoryFileUploadHandlerTest",
    "BulkUpdateTemporaryFileUploadHandlerTest",
]


class BulkUpdate(SelectRowsMixin, CheckSignalsMixin, WebTestMixin):
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
        settings.FILE_UPLOAD_HANDLERS = [self.handler]
        # settings.FILE_UPLOAD_HANDLERS = []

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
                res.forms["bulk-update"]["_file"] = Upload(str(Path(__file__).parent / "bulk_update.csv"))
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

    def test_simulate(self):
        res = self._run_action(
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
                "_dry_run": True,
                "fld-id": "1",
                "fld-char": "2",
                "fld-integer": "3",
            }
        )
        # no changes saved on the DB
        assert not DemoModel.objects.filter(char="aaa", integer=111).exists()
        assert not DemoModel.objects.filter(char="bbb", integer=222).exists()
        assert res.status_code == 200

    def test_no_permission(self):
        with user_grant_permission(self.user, ["demo.change_demomodel"]):
            res = self.app.get("/", user="user")
            res = res.click("Demo models")
            form = res.forms["changelist-form"]
            form["action"] = "bulk_update"
            form.set("_selected_action", True, 0)
            res = form.submit().follow()
            assert "Sorry you do not have rights to execute this action" in str(res.body)

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
            res = self._run_action(
                **{
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
            messages = [m.message for m in list(res.context["messages"])]

            self.assertTrue(messages)
            assert "Updated" in messages[0]

            res = self._run_action(selected_rows=[1])
            messages = [m.message for m in list(res.context["messages"])]
            self.assertTrue(messages)
            assert "Updated" in messages[0]

    def test_index_required(self):
        res = self._run_action(**{"_validate": 0, "fld-index_field": []})
        assert res.status_code == 200
        assert res.context["map_form"].errors == {"index_field": ["Please select one or more index fields"]}

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
        messages = [m.message for m in list(res.context["messages"])]
        assert messages[0] == "['miss column is not present in the file']"

    def test_bulk_update_with_one_to_one_field(self):
        demo_model_instance = G(DemoModel, char='InitialValue', integer=123)
        demo_one_to_one_instance = G(DemoOneToOne, demo=demo_model_instance)
        csv_data = f"pk,one_to_one_id\n{demo_model_instance.pk},{demo_one_to_one_instance.pk}"
        res = self._run_action(
            **{
                "_file": Upload(
                    "data.csv",
                    csv_data.encode(),
                    "text/csv",
                ),
                "fld-onetoone": "one_to_one_id",
            }
        )
        self.assertTrue(DemoModel.objects.filter(pk=demo_model_instance.pk, onetoone=demo_one_to_one_instance).exists())
        self.assertEqual(res.status_code, 200)



class BulkUpdateMemoryFileUploadHandlerTest(BulkUpdate, TestCase):
    handler = "django.core.files.uploadhandler.MemoryFileUploadHandler"


class BulkUpdateTemporaryFileUploadHandlerTest(BulkUpdate, TestCase):
    handler = "django.core.files.uploadhandler.TemporaryFileUploadHandler"
