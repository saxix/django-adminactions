.. _install:

.. include globals.rst

Installation
============

Installing iAdmin is as simple as checking out the source and adding it to
your project or ``PYTHONPATH``.


1. First of all follow the instruction to install `standard admin <standard_admin>`_ application,

2. Either check out iAdmin from `GitHub`_ or to pull a release off `PyPI`_. Doing ``pip install django-adminactions`` or ``easy_install django-adminactions`` is all that should be required.

3. Either symlink the ``adminactions`` directory into your project or copy the directory in. What ever works best for you.



.. _GitHub: http://github.com/saxix/django-actions
.. _PyPI: http://pypi.python.org/pypi/django-actions/

Configuration
=============

Add :mod:`adminactions` to your :setting:`INSTALLED_APPS`::

    INSTALLED_APPS = (
        'adminactions',
        'django.contrib.admin',
        'django.contrib.messages',
    )



Add the actions to your site::

    from django.contrib.admin import site
    import adminactions.actions as actions

    site.add_action(actions.mass_update)
    site.add_action(actions.graph_queryset)
    site.add_action(actions.export_to_csv)
    site.add_action(actions.export_as_json)


