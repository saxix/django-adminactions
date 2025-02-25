from __future__ import annotations

from typing import TYPE_CHECKING

from .bulk_update import bulk_update
from .byrows_update import byrows_update
from .duplicates import find_duplicates_action
from .export import export_as_csv, export_as_fixture, export_as_xls, export_delete_tree
from .graph import graph_queryset
from .mass_update import mass_update
from .merge import merge

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from django.contrib.admin import AdminSite
    from django.contrib.admin.options import ModelAdmin
    from django.db.models import QuerySet
    from django.db.models.base import Model
    from django.http.request import HttpRequest
    from django.http.response import HttpResponse

    TActionFunction = Callable[[ModelAdmin[Any], HttpRequest, QuerySet[Model]], HttpResponse]

actions = [
    export_as_fixture,
    export_as_csv,
    export_as_xls,
    export_delete_tree,
    find_duplicates_action,
    merge,
    mass_update,
    graph_queryset,
    bulk_update,
    byrows_update,
]


def add_to_site(
    site: AdminSite, exclude: list[str] | None = None, include: list[TActionFunction] | None = None
) -> None:
    """
    Register all the adminactions into passed site

    Examples:

    >>> from django.contrib.admin import site
    >>> add_to_site(site)

    >>> from django.contrib.admin import site
    >>> add_to_site(site, exclude=[merge])

    """
    exclude = exclude or []
    selection = include or actions
    for action in selection:
        if action.__name__ not in exclude:
            site.add_action(action)  # type: ignore[arg-type]
