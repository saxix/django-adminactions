.. include:: globals.rst
.. module:: adminactions.export

:tocdepth: 2

.. _faq:

===
FAQ
===

.. contents::
    :local:

.. _selenium_test:

It's possible to disable selenium tests?
========================================

Simply add ``ENABLE_SELENIUM=False`` to your :file:`settings` file, or set DISABLE_SELENUIM environment variable


.. _fixture_vs_tree:

Difference between :ref:`export_delete_tree` and :ref:`export_as_fixture`
=========================================================================


Considering this:

.. graphviz::

    digraph G {
        fontname = "Bitstream Vera Sans"
        fontsize = 8

        node [
                fontname = "Bitstream Vera Sans"
                fontsize = 8
                shape = "record"
        ]

        edge [
                fontname = "Bitstream Vera Sans"
                fontsize = 8
                style = "dashed"
                arrowhead = "open"
        ]
        Country [label = "{Italia:Country|}"]
        City [label = "{Rome:City|}"]
        Continent [label = "{Europe:Continent|}"]
        User [label = "{sax:User|}"]


        City -> Country
        Country -> Continent

        edge [
                label="last modified by"
        ]
        Country -> User
        Continent -> User
        City -> User


    }

here the partial code::

    from django.contrib.auth.models import User

    class Continent(models.Model):
        label = models.CharField(...)
        last_modified_by = models.ForeignKey(User)

    class Country(models.Model):
        continent = models.ForeignKey(Continent)
        label = models.CharField(...)
        last_modified_by = models.ForeignKey(User)

    class City(models.Model):
        country = models.ForeignKey(Country)
        label = models.CharField(...)
        last_modified_by = models.ForeignKey(User)


* Selecting sax (User) as target model:

    :func:`export_delete_tree` will dump the whole tree

    :func:`export_as_fixture` will dump only ``sax``

* Selecting Rome (City) as target model:

    :func:`export_delete_tree` will dump only ``Rome``

    :func:`export_as_fixture` will dump the whole tree



