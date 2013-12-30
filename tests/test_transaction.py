from django.contrib.auth.models import Group
from django_dynamic_fixture import G
import pytest
from adminactions import compat


@pytest.mark.django_db(transaction=False)
def test_commit_atomic():  ## aka commit_on_success if django<1.6
    with compat.atomic():
        G(Group, name='name')
    assert Group.objects.filter(name='name').count() == 1

@pytest.mark.django_db(transaction=False)
def test_commit_atomic_rollback():  ## aka commit_on_success if django<1.6
    with compat.atomic():
        G(Group, name='name')
        compat.rollback()
    assert not Group.objects.filter(name='name').exists()


@pytest.mark.django_db(transaction=False)
def test_commit_commit_manually():
    with compat.commit_manually():
        G(Group, name='name')
    assert Group.objects.filter(name='name').count() == 1

@pytest.mark.django_db(transaction=False)
def test_rollback():
    with compat.commit_manually():
        G(Group, name='name')
        compat.rollback()
    assert not Group.objects.filter(name='name').exists()
