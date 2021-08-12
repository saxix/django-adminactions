.. include:: globals.rst

.. _install:

============
Installation
============

Installing django-adminactions is as simple as checking out the source and adding it to
your project or ``PYTHONPATH``.


1. First of all follow the instruction to install `django_admin`_ application,

2. Either check out django-adminactions from `GitHub`_ or to pull a release off `PyPI`_. Doing ``pip install django-adminactions`` or ``easy_install django-adminactions`` is all that should be required.

3. Either symlink the ``adminactions`` directory into your project or copy the directory in. What ever works best for you.


Install test dependencies
=========================

If you want to run :mod:`adminactions` tests you need extra requirements


.. code-block:: python

    pip install -U django-adminactions[tests]


Configuration
=============

Add :mod:`adminactions` to your `INSTALLED_APPS`::

    INSTALLED_APPS = (
        'adminactions',
        'django.contrib.admin',
        'django.contrib.messages',
    )


Add the actions to your site::

    from django.contrib.admin import site
    import adminactions.actions as actions

    # register all adminactions
    actions.add_to_site(site)


Add service url to your urls.py ::

    urlpatterns = patterns('',
        ...
        url(r'^adminactions/', include('adminactions.urls')),
    )


Bonus:
    add `AdminActionPermMixin` to your `ModelAdmin`::

    class MyModelAdmin(AdminActionPermMixin, admin.ModelAdmin):
        pass


Add defaults for the Export to CSV to the Django Config.
See all available settings at :ref:`_export_as_csv`.::

    import csv
    
    ADMINACTIONS_CSV_OPTIONS_DEFAULT = {
        'date_format': 'Y-m-d',
        'datetime_format': 'Y-m-d G:i:s O',
        'time_format': 'G:i:s',
        'header': True,
        'quotechar': '"',
        'quoting': csv.QUOTE_ALL,
        'delimiter': ',',
        'escapechar': '\\',
    }
