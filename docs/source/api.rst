.. include:: globals.rst
.. module:: adminactions

:tocdepth: 2

.. _api:

===
API
===

.. currentmodule:: adminactions

---------
Functions
---------

.. _api_export_as_csv:


export_as_csv
-------------

.. seealso:: Are you looking for the :ref:`export_as_csv` action? .

.. function:: adminactions.api.export_as_csv

Exports a queryset as csv from a queryset with the given fields.


.. _csv_defaults:

**Defaults**

.. warning:: Due a mistake the default configuration of `export_as_csv` is not `csv` but `semicolon-csv`

::

    csv_options_default = {'date_format': 'd/m/Y',
                           'datetime_format': 'N j, Y, P',
                           'time_format': 'P',
                           'header': False,
                           'quotechar': '"',
                           'quoting': csv.QUOTE_ALL,
                           'delimiter': ';',
                           'escapechar': '\\', }



Usage examples

Returns  :class:`~django:django.http.HttpResponse`::

    response = export_as_csv(User.objects.all())

Write to file

.. code-block:: python

    >>> users = export_as_csv(User.objects.all(), out=open('users.csv', 'w'))
    >>> users.close()

Write to buffer

.. code-block:: python

    >>> users = export_as_csv(User.objects.all(), out=StringIO())
    >>> with open('users.csv', 'w') as f:
            f.write(users.getvalue())


.. _export_with_callable:

Export with callable

.. code-block:: python

    >>> fields = ['username', 'get_full_name']
    >>> export_as_csv(User.objects.all(), fields=fields, out=sys.stdout)
    "sax";"FirstName 9 LastName 9"
    "user_0";"FirstName 0 LastName 0"
    "user_1";"FirstName 1 LastName 1"


.. _export_with_dictionaries:

Export with dictionaries

.. code-block:: python

    >>> fields = ['codename', 'content_type__app_label']
    >>> qs = Permission.objects.filter(codename='add_user').values('codename', 'content_type__app_label')
    >>> __ = export_as_csv(qs, fields=fields, out=sys.stdout)
    "add_user";"auth"


.. _api_export_as_xls:


export_as_xls
-------------
.. versionadded:: 0.3

Exports a queryset as csv from a queryset with the given fields.



.. _api_merge:

merge
-----

.. seealso:: See :ref:`merge` action for additional notes.


Merge 'other' into master.

        ``fields`` is a list of fieldnames that must be read from ``other`` to put into master.
        If ``fields`` is None ``master`` will get all the ``other`` values except primary_key.
        Finally ``other`` will be deleted and master will be preserved




Custom validation
~~~~~~~~~~~~~~~~~

If you need to disable validation for some fields, it is possible to set parameter ``merge_form``
to a subclass of `:class:adminactions.merge.MergeForm` and change the validation there.

.. code-block:: python

    class CompanyMergeForm(merge.MergeForm):
        class Meta:
            model = models.Company
            fields = "__all__"

        def full_clean(self):
            super().full_clean()
            if 'address_psc' in self._errors:
                del self._errors['address_psc']

    class CompanyAdmin(city_admin_mixin_generator(admin.ModelAdmin):
        form = CompanyForm
        merge_form = CompanyMergeForm



.. _get_export_as_csv_filename:
.. _get_export_as_fixture_filename:
.. _get_export_delete_tree_filename:
.. _filename_callbacks:


------------------
Filename callbacks
------------------
To use custom names for yours exports simply implements ``get_export_<TYPE>_filename``
in your ``Modeladmin`` class, these must return a string that will be used as filename
in the SaveAs dialog box of the browser

example:

.. code-block:: python


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
