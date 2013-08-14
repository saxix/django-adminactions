.. include:: globals.rst
.. module:: adminactions

:tocdepth: 2

.. _api:

===
API
===

.. currentmodule:: adminactions

-------------------
Functions
-------------------

.. _api_export_as_csv:


export_as_csv
-------------

.. function:: adminactions.api.export_as_csv

Exports a queryset as csv from a queryset with the given fields.

Usage examples

Returns  :class:`django:django.http.HttpResponse`::

    response = export_as_csv(User.objects.all())

Write to file

.. code-block:: python

    users = export_as_csv(User.objects.all(), out=open('users.csv', 'w'))
    users.close()

Write to buffer

.. code-block:: python

    users = export_as_csv(User.objects.all(), out=StringIO())

    with open('users.csv', 'w') as f:
        f.write(users.getvalue())




.. _api_export_as_xls:


export_as_xls
-------------
.. versionadded:: 0.3

.. autofunction:: adminactions.api.export_as_xls



.. _api_merge:

merge
-----

.. autofunction:: adminactions.api.merge



.. _get_export_as_csv_filename:
.. _get_export_as_fixture_filename:
.. _get_export_delete_tree_filename:
.. _filename_callbacks:


-------------------
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


-----
Utils
-----

.. autofunction:: adminactions.utils.clone_instance
.. autofunction:: adminactions.utils.get_field_by_path
.. autofunction:: adminactions.utils.get_field_value
.. autofunction:: adminactions.utils.get_verbose_name
.. autofunction:: adminactions.actions.add_to_site

------------
Templatetags
------------
.. autofunction:: adminactions.templatetags.actions.verbose_name
.. autofunction:: adminactions.templatetags.actions.field_display
.. autofunction:: adminactions.templatetags.actions.raw_value
