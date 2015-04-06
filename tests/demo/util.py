# -*- coding: utf-8 -*-
from __future__ import absolute_import
from random import randrange, shuffle
from django_dynamic_fixture.fixture_algorithms.random_fixture import RandomDataFixture
from six.moves import range


def ipaddress(not_valid=None):
    """
        returns a string representing a random ip address

    :param not_valid: if passed must be a list of integers representing valid class A netoworks that must be ignored
    """
    not_valid_class_A = not_valid or []

    class_a = [r for r in range(1, 256) if r not in not_valid_class_A]
    shuffle(class_a)
    first = class_a.pop()

    return ".".join([str(first), str(randrange(1, 256)),
                     str(randrange(1, 256)), str(randrange(1, 256))])


class DataFixtureClass(RandomDataFixture):  # it can inherit of SequentialDataFixture, RandomDataFixture etc.
    def genericipaddressfield_config(self, field, key):  # method name must have the format: FIELDNAME_config
        return ipaddress()
