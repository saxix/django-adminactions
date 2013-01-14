.. include:: globals.rst
.. module:: adminactions.export

:tocdepth: 2

.. _howto:

======
HowTo
======

.. contents::
    :local:


.. _register_transform_function:

Register Your Own Transform Function
====================================

Transform Operation are manage by proper tranform functions, |app| come with a small set but it's possible
to add extra function.
Transform function are function that accept one or two parameter.



.. _customize_mass_update_form:


Customize Massupdate Form
=========================

.. versionadded:: 0.0.4

To customize the Form used by the massupdate action simply create your own Form class and set it as value
of the ``mass_updated_form`` attribute to your ``ModelAdmin``. ie::

    class MyMassUpdateForm(ModelForm):
        class Meta:
            model = MyModel


    class MyModelAdmin(admin.ModelAdmin):
        mass_updated_form = MyMassUpdateForm


    admin.register(MyModel, MyModelAdmin)


Selectively Register Actions
============================

To register only some selected action simply use the ``site.add_action`` method::

        from django.contrib.admin import site
        import adminactions.actions as actions


        site.add_action(actions.mass_update)
        site.add_action(actions.export_as_csv)
