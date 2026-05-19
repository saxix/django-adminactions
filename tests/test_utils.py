from __future__ import annotations

import pytest
from django.db import models

from adminactions.utils import clone_instance, get_field_by_name, get_verbose_name


class CloneParent(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = "tests"


class CloneChild(CloneParent):
    value = models.CharField(max_length=10)

    class Meta:
        app_label = "tests"


def test_get_verbose_name() -> None:
    from django.contrib.auth.models import Permission, User

    user = User()
    p = Permission()
    assert get_verbose_name(user, "username") == "username"

    assert get_verbose_name(User, "username") == "username"

    assert get_verbose_name(User.objects.all(), "username") == "username"

    assert get_verbose_name(User.objects, "username") == "username"

    assert get_verbose_name(User.objects, get_field_by_name(user, "username")[0]) == "username"

    assert get_verbose_name(p, "content_type.model") == "python model class name"

    with pytest.raises(TypeError):
        get_verbose_name(object, "aaa")

    with pytest.raises(TypeError):
        get_verbose_name(p, None)


def test_clone_instance_uses_field_attnames() -> None:
    instance = CloneChild(id=1, name="parent", value="child")

    clone = clone_instance(instance)

    assert clone.pk == instance.pk
    assert clone.cloneparent_ptr_id == instance.cloneparent_ptr_id
    assert clone.name == instance.name
    assert clone.value == instance.value


def test_clone_instance_accepts_attname_fieldnames() -> None:
    instance = CloneChild(id=1, name="parent", value="child")

    clone = clone_instance(instance, ["cloneparent_ptr_id", "value"])

    assert clone.pk == instance.pk
    assert clone.cloneparent_ptr_id == instance.cloneparent_ptr_id
    assert clone.value == instance.value


def test_flatten() -> None:
    from adminactions.utils import flatten

    assert flatten([[[1, 2, 3], (42, None)], [4, 5], [6], 7, (8, 9, 10)]) == [
        1,
        2,
        3,
        42,
        None,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
    ]
