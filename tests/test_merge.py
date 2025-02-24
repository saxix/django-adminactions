from __future__ import annotations

import os

from demo.models import DemoModel, DemoOneToOne, UserDetail
from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import G
from django_webtest import WebTestMixin
from utils import BaseTestCaseMixin, SelectRowsMixin, user_grant_permission

from adminactions.api import ALL_FIELDS, merge

PROFILE_MODULE = getattr(settings, "AUTH_PROFILE_MODULE", "tests.UserProfile")


def get_profile(user):
    return UserDetail.objects.get_or_create(user=user, note="")[0]


class MergeTestApi(BaseTestCaseMixin, TestCase):
    fixtures = ["adminactions.json", "demoproject.json"]

    def setUp(self) -> None:
        super().setUp()
        self.master_pk = 2
        self.other_pk = 3

    def tearDown(self) -> None:
        super().tearDown()

    def test_merge_success_no_commit(self) -> None:
        master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        result = merge(master, other)

        assert User.objects.filter(pk=master.pk).exists()
        assert User.objects.filter(pk=other.pk).exists()

        assert result.pk == master.pk
        assert result.first_name == master.first_name
        assert result.last_name == master.last_name
        assert result.password == master.password

    def test_merge_success_fields_no_commit(self) -> None:
        master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        result = merge(master, other, ["password", "last_login"])

        master = User.objects.get(pk=master.pk)

        assert User.objects.filter(pk=master.pk).exists()
        assert User.objects.filter(pk=other.pk).exists()

        assert result.last_login != master.last_login
        assert result.last_login == other.last_login
        assert result.password == other.password

        assert result.last_name != other.last_name

    def test_merge_success_commit(self) -> None:
        old_master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        result = merge(old_master, other, commit=True)

        master = User.objects.get(pk=result.pk)  # reload
        assert User.objects.filter(pk=master.pk).exists()
        assert not User.objects.filter(pk=other.pk).exists()

        assert result.pk == master.pk
        assert master.first_name == old_master.first_name
        assert master.last_name == old_master.last_name
        assert master.password == old_master.password

    def test_merge_success_m2m(self) -> None:
        master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        group = Group.objects.get_or_create(name="G1")[0]
        other.groups.add(group)
        other.save()

        result = merge(master, other, commit=True, m2m=["groups"])
        master = User.objects.get(pk=result.pk)  # reload
        self.assertSequenceEqual(master.groups.all(), [group])

    def test_merge_success_m2m_all(self) -> None:
        master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        group = Group.objects.get_or_create(name="G1")[0]
        perm = Permission.objects.all()[0]
        other.groups.add(group)
        other.user_permissions.add(perm)
        other.save()

        merge(master, other, commit=True, m2m=ALL_FIELDS)

        self.assertSequenceEqual(master.groups.all(), [group])
        self.assertSequenceEqual(master.user_permissions.all(), [perm])

    def test_merge_success_related_all(self) -> None:
        master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        entry = other.logentry_set.get_or_create(object_repr="test", action_flag=1)[0]

        result = merge(master, other, commit=True, related=ALL_FIELDS)

        master = User.objects.get(pk=result.pk)  # reload
        self.assertSequenceEqual(master.logentry_set.all(), [entry])
        assert LogEntry.objects.filter(pk=entry.pk).exists()

    def test_merge_one_to_one_move_single(self) -> None:
        master = DemoModel.objects.get(pk=1)
        other = DemoModel.objects.get(pk=2)
        related_one = DemoOneToOne(demo=other)
        related_one.save()

        result = merge(master, other, commit=True, related=ALL_FIELDS)

        master = DemoModel.objects.get(pk=result.pk)  # reload
        assert master.onetoone == related_one
        assert DemoOneToOne.objects.filter(pk=related_one.pk).exists()
        assert os.path.basename(master.image.file.name) == "second.png"

    # @skipIf(not hasattr(settings, 'AUTH_PROFILE_MODULE'), "")
    def test_merge_one_to_one_field(self) -> None:
        master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        profile = get_profile(other)
        if profile:
            entry = other.logentry_set.get_or_create(object_repr="test", action_flag=1)[0]

            result = merge(master, other, commit=True, related=ALL_FIELDS)

            master = User.objects.get(pk=result.pk)  # reload
            self.assertSequenceEqual(master.logentry_set.all(), [entry])
            assert LogEntry.objects.filter(pk=entry.pk).exists()
            assert get_profile(result) == profile
            # self.assertEqual(master.get_profile(), profile)

    def test_merge_ignore_related(self) -> None:
        master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        entry = other.logentry_set.get_or_create(object_repr="test", action_flag=1)[0]
        result = merge(master, other, commit=True, related=None)

        master = User.objects.get(pk=result.pk)  # reload
        self.assertSequenceEqual(master.logentry_set.all(), [])
        assert not User.objects.filter(pk=other.pk).exists()
        assert not LogEntry.objects.filter(pk=entry.pk).exists()

    def test_merge_image(self) -> None:
        master = DemoModel.objects.get(pk=3)
        other = DemoModel.objects.get(pk=1)
        img1 = other.image
        img2 = other.subclassed_image

        assert master.image != other.image
        assert master.subclassed_image != other.subclassed_image

        result = merge(
            master,
            other,
            fields=["image", "subclassed_image"],
            commit=True,
            related=None,
        )

        master = DemoModel.objects.get(pk=result.pk)  # reload
        assert not DemoModel.objects.filter(pk=other.pk).exists()
        assert master.image == img1
        assert master.subclassed_image == img2


class TestMergeAction(SelectRowsMixin, WebTestMixin, TestCase):
    csrf_checks = True
    fixtures = ["adminactions.json", "demoproject.json"]
    urls = "demo.urls"
    sender_model = User
    action_name = "merge"
    _selected_rows = [1, 2]

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("admin:auth_user_changelist")
        self.user = G(User, username="user", is_staff=True, is_active=True)

    def _run_action(self, steps=3, page_start=None):
        with user_grant_permission(self.user, ["auth.change_user", "auth.adminactions_merge_user"]):
            if isinstance(steps, int):
                steps = list(range(1, steps + 1))
                res = self.app.get("/", user="user")
                res = res.click("Users")
            else:
                res = page_start
            if 1 in steps:
                form = res.forms["changelist-form"]
                form["action"] = "merge"
                self._select_rows(form)
                res = form.submit()
                assert not hasattr(res.forms["merge-form"], "errors")

            if 2 in steps:
                res.forms["merge-form"]["username"] = res.forms["merge-form"]["form-1-username"].value
                res.forms["merge-form"]["email"] = res.forms["merge-form"]["form-1-email"].value
                res.forms["merge-form"]["last_login"] = res.forms["merge-form"]["form-1-last_login"].value
                res.forms["merge-form"]["date_joined"] = res.forms["merge-form"]["form-1-date_joined"].value
                res = res.forms["merge-form"].submit("preview")
                assert not hasattr(res.forms["merge-form"], "errors")

            if 3 in steps:
                res = res.forms["merge-form"].submit("apply")
            return res

    def test_no_permission(self) -> None:
        with user_grant_permission(self.user, ["auth.change_user"]):
            res = self.app.get("/", user="user")
            res = res.click("Users")
            form = res.forms["changelist-form"]
            form["action"] = "merge"
            self._select_rows(form)
            res = form.submit().follow()
            assert "Sorry you do not have rights to execute this action" in str(res.body)

    # noinspection PyTypeChecker
    def test_success(self) -> None:
        res = self._run_action(1)
        preserved = User.objects.get(pk=self._selected_values[0])
        removed = User.objects.get(pk=self._selected_values[1])

        assert preserved.email != removed.email  # sanity check

        self._run_action([2, 3], res)

        assert not User.objects.filter(pk=removed.pk).exists()
        assert User.objects.filter(pk=preserved.pk).exists()

        preserved_after = User.objects.get(pk=self._selected_values[0])
        assert preserved_after.email == removed.email
        assert not LogEntry.objects.filter(pk=removed.pk).exists()

    def test_error_if_too_many_records(self) -> None:
        with user_grant_permission(self.user, ["auth.change_user", "auth.adminactions_merge_user"]):
            res = self.app.get("/", user="user")
            res = res.click("Users")
            form = res.forms["changelist-form"]
            form["action"] = "merge"
            self._select_rows(form, [1, 2, 3])
            res = form.submit().follow()
            self.assertContains(res, "Please select exactly 2 records")

    def test_swap(self) -> None:
        with user_grant_permission(self.user, ["auth.change_user", "auth.adminactions_merge_user"]):
            # removed = User.objects.get(pk=self._selected_rows[0])
            # preserved = User.objects.get(pk=self._selected_rows[1])

            res = self.app.get("/", user="user")
            res = res.click("Users")
            form = res.forms["changelist-form"]
            form["action"] = "merge"
            self._select_rows(form, [1, 2])
            res = form.submit()
            removed = User.objects.get(pk=self._selected_values[0])
            preserved = User.objects.get(pk=self._selected_values[1])

            # steps = 2 (swap):
            res.forms["merge-form"]["master_pk"] = self._selected_values[1]
            res.forms["merge-form"]["other_pk"] = self._selected_values[0]

            res.forms["merge-form"]["username"] = res.forms["merge-form"]["form-0-username"].value
            res.forms["merge-form"]["email"] = res.forms["merge-form"]["form-0-email"].value
            res.forms["merge-form"]["last_login"] = res.forms["merge-form"]["form-1-last_login"].value
            res.forms["merge-form"]["date_joined"] = res.forms["merge-form"]["form-1-date_joined"].value

            # res.form['field_names'] = 'username,email'

            res = res.forms["merge-form"].submit("preview")
            # steps = 3:
            res = res.forms["merge-form"].submit("apply")

            preserved_after = User.objects.get(pk=self._selected_values[1])
            assert not User.objects.filter(pk=removed.pk).exists()
            assert User.objects.filter(pk=preserved.pk).exists()

            assert preserved_after.email == removed.email
            assert not LogEntry.objects.filter(pk=removed.pk).exists()

    def test_merge_move_detail(self) -> None:
        from adminactions.merge import MergeForm

        with user_grant_permission(self.user, ["auth.change_user", "auth.adminactions_merge_user"]):
            # removed = User.objects.get(pk=self._selected_rows[0])
            # preserved = User.objects.get(pk=self._selected_rows[1])

            res = self.app.get("/", user="user")
            res = res.click("Users")
            form = res.forms["changelist-form"]
            form["action"] = "merge"
            self._select_rows(form, [1, 2])
            res = form.submit()
            removed = User.objects.get(pk=self._selected_values[0])
            preserved = User.objects.get(pk=self._selected_values[1])

            removed.userdetail_set.create(note="1")
            preserved.userdetail_set.create(note="2")

            # steps = 2:
            res.forms["merge-form"]["master_pk"] = self._selected_values[1]
            res.forms["merge-form"]["other_pk"] = self._selected_values[0]

            res.forms["merge-form"]["username"] = res.forms["merge-form"]["form-0-username"].value
            res.forms["merge-form"]["email"] = res.forms["merge-form"]["form-0-email"].value
            res.forms["merge-form"]["last_login"] = res.forms["merge-form"]["form-1-last_login"].value
            res.forms["merge-form"]["date_joined"] = res.forms["merge-form"]["form-1-date_joined"].value
            res.forms["merge-form"]["dependencies"] = MergeForm.DEP_MOVE
            res = res.forms["merge-form"].submit("preview")
            # steps = 3:
            res = res.forms["merge-form"].submit("apply")

            preserved_after = User.objects.get(pk=self._selected_values[1])
            assert preserved_after.userdetail_set.count() == 2
            assert not User.objects.filter(pk=removed.pk).exists()

    def test_merge_delete_detail(self) -> None:
        from adminactions.merge import MergeForm

        with user_grant_permission(self.user, ["auth.change_user", "auth.adminactions_merge_user"]):
            # removed = User.objects.get(pk=self._selected_rows[0])
            # preserved = User.objects.get(pk=self._selected_rows[1])

            res = self.app.get("/", user="user")
            res = res.click("Users")
            form = res.forms["changelist-form"]
            form["action"] = "merge"
            self._select_rows(form, [1, 2])
            res = form.submit()
            removed = User.objects.get(pk=self._selected_values[0])
            preserved = User.objects.get(pk=self._selected_values[1])

            removed.userdetail_set.create(note="1")
            preserved.userdetail_set.create(note="2")

            # steps = 2:
            res.forms["merge-form"]["master_pk"] = self._selected_values[1]
            res.forms["merge-form"]["other_pk"] = self._selected_values[0]

            res.forms["merge-form"]["username"] = res.forms["merge-form"]["form-0-username"].value
            res.forms["merge-form"]["email"] = res.forms["merge-form"]["form-0-email"].value
            res.forms["merge-form"]["last_login"] = res.forms["merge-form"]["form-1-last_login"].value
            res.forms["merge-form"]["date_joined"] = res.forms["merge-form"]["form-1-date_joined"].value
            res.forms["merge-form"]["dependencies"] = MergeForm.DEP_DELETE
            res = res.forms["merge-form"].submit("preview")
            # steps = 3:
            res = res.forms["merge-form"].submit("apply")

            preserved_after = User.objects.get(pk=self._selected_values[1])
            assert preserved_after.userdetail_set.count() == 1
            assert not User.objects.filter(pk=removed.pk).exists()


class TestMergeImageAction(SelectRowsMixin, WebTestMixin, TestCase):
    csrf_checks = True
    fixtures = ["adminactions.json", "demoproject.json"]
    urls = "demo.urls"
    sender_model = User
    action_name = "merge"
    _selected_rows = [0, 2]

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("admin:demo_demomodel_changelist")
        self.user = G(User, username="user", is_staff=True, is_active=True)

    def _run_action(self, steps=3, page_start=None):
        with user_grant_permission(self.user, ["demo.change_demomodel", "demo.adminactions_merge_demomodel"]):
            if isinstance(steps, int):
                steps = list(range(1, steps + 1))
                res = self.app.get("/", user="user")
                res = res.click("Demo models")
            else:
                res = page_start

            if 1 in steps:
                form = res.forms["changelist-form"]
                form["action"] = "merge"
                self._select_rows(form)
                res = form.submit()
                assert not hasattr(res.forms["merge-form"], "errors")

            if 2 in steps:
                res.forms["merge-form"]["image"] = res.forms["merge-form"]["form-1-image"].value
                res.forms["merge-form"]["field_names"] = "image,subclassed_image"
                res = res.forms["merge-form"].submit("preview")
                assert not hasattr(res.forms["merge-form"], "errors")

            if 3 in steps:
                res = res.forms["merge-form"].submit("apply")
            return res

    # noinspection PyTypeChecker
    def test_success(self) -> None:
        res = self._run_action(1)
        preserved = DemoModel.objects.get(pk=self._selected_values[0])
        removed = DemoModel.objects.get(pk=self._selected_values[1])

        img1 = removed.image
        img2 = removed.subclassed_image

        assert preserved.image != removed.image  # sanity check
        assert preserved.subclassed_image != removed.subclassed_image  # sanity check
        assert preserved.pk == 3  # sanity check
        assert removed.pk == 1  # sanity check

        self._run_action([2, 3], res)

        assert not DemoModel.objects.filter(pk=removed.pk).exists()
        assert DemoModel.objects.filter(pk=preserved.pk).exists()

        preserved_after = DemoModel.objects.get(pk=preserved.pk)

        assert preserved_after.image == img1
        assert preserved_after.subclassed_image == img2
