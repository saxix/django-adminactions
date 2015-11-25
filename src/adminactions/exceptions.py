# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals


class ActionInterrupted(Exception):
    """
    This exception can be raised by a :ref:`adminaction_requested` or :ref:`adminaction_start`
     to prevent action to be executed
    """


class FakeTransaction(Exception):
    pass
