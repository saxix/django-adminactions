# pylint: disable-msg= W0611
from .mass_update import mass_update
from .export import export_as_fixture, export_as_csv, export_delete_tree
from .graph import graph_queryset


def add_to_site(site):
    """
    Register all the adminactions's actions into passed site

    :param site: django.contrib.admin.AdminSite instance
    :return: None
    """
    site.add_action(mass_update)
    site.add_action(graph_queryset)
    site.add_action(export_as_csv)
    site.add_action(export_as_fixture)
    site.add_action(export_delete_tree)
