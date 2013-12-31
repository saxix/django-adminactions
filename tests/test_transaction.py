import pytest
from django.contrib.auth.models import Group
from django_dynamic_fixture import G
from adminactions import compat


@pytest.mark.django_db(transaction=True)
def test_nocommit():
    with compat.nocommit():
        G(Group, name='name')
    assert not Group.objects.filter(name='name').exists()
