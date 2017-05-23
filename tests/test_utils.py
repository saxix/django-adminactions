from __future__ import absolute_import

import six

import pytest

from adminactions.compat import get_field_by_name
from adminactions.utils import get_verbose_name


def test_get_verbose_name():
    from django.contrib.auth.models import User, Permission

    user = User()
    p = Permission()
    assert six.text_type(get_verbose_name(user, 'username')) == 'username'

    assert six.text_type(get_verbose_name(User, 'username')) == 'username'

    assert six.text_type(get_verbose_name(User.objects.all(), 'username')) == 'username'

    assert six.text_type(get_verbose_name(User.objects, 'username')) == 'username'

    assert six.text_type(get_verbose_name(User.objects, get_field_by_name(user, 'username')[0])) == 'username'

    assert six.text_type(get_verbose_name(p, 'content_type.model')) == 'python model class name'

    with pytest.raises(ValueError):
        get_verbose_name(object, 'aaa')

    with pytest.raises(ValueError):
        get_verbose_name(p, None)


def test_flatten():
    from adminactions.utils import flatten

    assert flatten([[[1, 2, 3], (42, None)], [4, 5], [6], 7, (8, 9, 10)]) == [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]
