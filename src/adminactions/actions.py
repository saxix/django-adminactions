# pylint: disable-msg= W0611
from __future__ import absolute_import, unicode_literals

from .byrows_update import byrows_update
from .export import (export_as_csv, export_as_fixture, export_as_xls,
                     export_delete_tree,)
from .graph import graph_queryset
from .mass_update import mass_update
from .merge import merge

actions = [export_as_fixture,
           export_as_csv,
           export_as_xls,
           export_delete_tree,
           merge, mass_update,
           graph_queryset,
           byrows_update]


def add_to_site(site, exclude=None):
    """
    Register all the adminactions into passed site

    :param site: AdminSite instance
    :type site: django.contrib.admin.AdminSite

    :param exclude: name of the actions to exclude
    :type exclude: List
    :return: None

    Examples:

    >>> from django.contrib.admin import site
    >>> add_to_site(site)

    >>> from django.contrib.admin import site
    >>> add_to_site(site, exclude=['merge'])

    """
    exclude = exclude or []
    for action in actions:
        if action.__name__ not in exclude:
            site.add_action(action)
