.. include:: globals.rst
.. module:: adminactions

:tocdepth: 2

.. _api:

===
API
===

.. currentmodule:: adminactions


.. autosummary::
    actions.add_to_site
    api.export_as_csv
    api.merge
    utils.clone_instance
    utils.get_field_by_path
    utils.get_field_value
    utils.get_verbose_name
    templatetags.actions.verbose_name
    templatetags.actions.field_display
    templatetags.actions.raw_value


.. autofunction:: adminactions.actions.add_to_site


.. _api_export_as_csv:

.. autofunction:: adminactions.api.export_as_csv


.. _api_merge:

.. autofunction:: adminactions.api.merge


.. _get_export_as_csv_filename:
.. _get_export_as_fixture_filename:
.. _get_export_delete_tree_filename:
.. _filename_callbacks:

Filename callbacks
-------------------
To use custom names for yours exports simply implements ``get_export_<TYPE>_filename``
in your ``Modeladmin`` class, these must return a string that will be used as filename
in the SaveAs dialog box of the browser

example::
    class UserAdmin(ModelAdmin):
        def get_export_as_csv_filename(request, queryset):
            if 'isadmin' in request.GET
                return 'administrators.csv'
            else:
                return 'all_users.csv'

Available callbacks:

* ``get_export_as_csv_filename``
* ``get_export_as_fixture_filename``
* ``get_export_delete_tree_filename``



Utils
-----

.. autofunction:: adminactions.utils.clone_instance
.. autofunction:: adminactions.utils.get_field_by_path
.. autofunction:: adminactions.utils.get_field_value
.. autofunction:: adminactions.utils.get_verbose_name


Templatetags
------------
.. autofunction:: adminactions.templatetags.actions.verbose_name
.. autofunction:: adminactions.templatetags.actions.field_display
.. autofunction:: adminactions.templatetags.actions.raw_value
