import pytest
from adminactions.utils import get_verbose_name


def test_get_verbose_name():
    from django.contrib.auth.models import User, Permission
    user = User()
    p = Permission()
    assert unicode(get_verbose_name(user, 'username')) == 'username'

    assert unicode(get_verbose_name(User, 'username'))        == 'username'

    assert unicode(get_verbose_name(User.objects.all(), 'username')) == 'username'

    assert unicode(get_verbose_name(User.objects, 'username')) == 'username'

    assert unicode(get_verbose_name(User.objects, user._meta.get_field_by_name('username')[0])) == 'username'

    assert unicode(get_verbose_name(p, 'content_type.model')) == 'python model class name'

    with pytest.raises(ValueError):
        get_verbose_name(object, 'aaa')
