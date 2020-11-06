import mock
import pytest
from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.db.transaction import atomic
from django.test import TransactionTestCase
from django_dynamic_fixture import G

from adminactions import compat
from adminactions.api import merge
from adminactions.exceptions import ActionInterrupted
from adminactions.signals import adminaction_end

pytestmarker = pytest.mark.skip


@pytest.mark.django_db()
def test_nocommit():
    with compat.nocommit():
        G(Group, name='name')
    assert not Group.objects.filter(name='name').exists()


@pytest.mark.django_db()
def test_transaction_merge(users):
    master, other = users
    with atomic():

        with mock.patch('django.contrib.auth.models.User.delete', side_effect=IntegrityError):
            with pytest.raises(IntegrityError):
                merge(master, other, commit=True)

        assert User.objects.filter(pk=master.pk).exists()
        assert User.objects.filter(pk=other.pk).exists()

        assert master.first_name != other.first_name


@pytest.mark.django_db()
def test_transaction_mass_update(app, users, administrator):
    assert User.objects.filter(is_staff=True).count() == 1  # sanity check

    def _handler(*args, **kwargs):
        raise ActionInterrupted()

    with atomic():
        res = app.get('/admin/', user=administrator.username)
        res = res.click('Users')
        form = res.forms['changelist-form']
        form['action'] = 'mass_update'

        form.get('_selected_action', index=0).checked = True
        form.get('_selected_action', index=1).checked = True
        form.get('_selected_action', index=2).checked = True

        res = form.submit()
        res.form['chk_id_is_staff'].checked = True
        res.form['is_staff'].checked = True

        # res.form.submit('apply').follow()
        # assert User.objects.filter(is_staff=True).count() == 1

        with pytest.raises(BaseException):
            adminaction_end.connect(_handler)
            res.form.submit('apply').follow()
            adminaction_end.disconnect(_handler)

        assert User.objects.filter(is_staff=True).count() == 1


class TestIsLibero(TransactionTestCase):
    def test_true(self):
        self.assertTrue(True)
