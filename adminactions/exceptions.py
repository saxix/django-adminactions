# -*- coding: utf-8 -*-

from django.utils.translation import gettext as _


class ActionInterrupted(Exception):
    """
    This exception can be raised by a :ref:`adminaction_requested` or :ref:`adminaction_start`
     to prevent action to be executed
    """
