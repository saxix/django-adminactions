.. include:: globals.rst
.. module:: adminactions.export

:tocdepth: 2

.. _howto:

=====
HowTo
=====

.. contents::
    :local:


.. _register_transform_function:

Register Your Own Transform Function
====================================

Transform Operation are manage by proper tranform functions, |app| come with a small set but it's possible
to add extra function.
Transform function are function that accept one or two parameter.



.. _use_custom_mass_update_form:

Use custom Massupdate Form
==========================

.. versionadded:: 0.0.4

To customize the Form used by the massupdate action simply create your own Form class and set it as value
of the ``mass_update_form`` attribute to your ``ModelAdmin``. ie::

    from adminactions.mass_update import MassUpdateForm


    class MyMassUpdateForm(MassUpdateForm):
        class Meta:
             fields = 'field1', 'field2',


    class MyModelAdmin(admin.ModelAdmin):
        mass_update_form = MyMassUpdateForm


    admin.register(MyModel, MyModelAdmin)


.. _selectively_register_actions:

Selectively Register Actions
============================

To register only some selected action simply use the ``site.add_action`` method::

        from django.contrib.admin import site
        import adminactions.actions as actions


        site.add_action(actions.mass_update)
        site.add_action(actions.export_as_csv)

.. _limit_massupdate_to_certain_fields:

Limit Massupdate to certain fields
==================================

.. versionadded:: 1.8

    class MyModelAdmin(admin.ModelAdmin):
        mass_update_fields = ['name']

    OR

    class MyModelAdmin(admin.ModelAdmin):
        mass_update_exclude = ['pk', 'date']

    admin.register(MyModel, MyModelAdmin)


.. _limit_massupdate_hints_to_certain_fields:

Limit Massupdate hints to certain fields
========================================

.. versionadded:: 1.8

    class MyModelAdmin(admin.ModelAdmin):
        mass_update_hints = ['name']

    admin.register(MyModel, MyModelAdmin)

