from django.contrib.auth.models import Group
from django_dynamic_fixture import G
import pytest
from adminactions import compat


@pytest.mark.django_db
def test_commit():
    with compat.atomic():
        G(Group, name='name')
    assert Group.objects.filter(name='name').count() == 1


@pytest.mark.django_db(transaction=False)
def test_rollback():
    with compat.commit_manually():
        G(Group, name='name')
        compat.rollback()
    assert not Group.objects.filter(name='name').exists()


@pytest.mark.django_db(transaction=False)
def test_nocommit():
    with compat.nocommit():
        G(Group, name='name')
    assert not Group.objects.filter(name='name').exists()

