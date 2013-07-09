.. include:: globals.rst
.. _signals:

=======
Signals
=======

|app| provides the following signals:

    * :ref:`adminaction_requested`
    * :ref:`adminaction_start`
    * :ref:`adminaction_end`

.. _adminaction_requested:

``adminaction_requested``
=========================

Sent when the action is requested (ie click 'Go' in the admin changelist view).
The handler can raise a :ref:`actioninterrupted` to interrupt
the action's execution. The handler can rely on the following parameter:

    * sender: :class:`django:django.db.models.Model`
    * action: string. name of the action
    * request: :class:`django:django.core.httpd.HttpRequest`
    * queryset: :class:`django:django.db.models.query.Queryset`
    * modeladmin: :class:`django:django.contrib.admin.ModelAdmin`

Example::

    from adminactions.signals import adminaction_requested

    def myhandler(sender, action, request, queryset, modeladmin, **kwargs):
        if action == 'mass_update' and queryset.filter(locked==True).exists():
            raise ActionInterrupted('Queryset cannot contains locked records')

    adminaction_requested.connect(myhandler, sender=MyModel, action='mass_update`)


.. _adminaction_start:

``adminaction_start``
=====================

Sent after the form has been validated (ie click 'Apply' in the action Form),
**just before** the execution of the action.
The handler can raise a :ref:`actioninterrupted` to avoid the stop execution.
The handler can rely on the following parameter:

    * sender: :class:`django:django.db.models.Model`
    * action: string. name of the action
    * request: :class:`django:django.core.httpd.HttpRequest`
    * queryset: :class:`django:django.db.models.query.Queryset`
    * modeladmin: :class:`django:django.contrib.admin.ModelAdmin`
    * form: :class:`django:django.forms.Form`

Example::

    from adminactions.signals import adminaction_start

    def myhandler(sender, action, request, queryset, modeladmin, form, **kwargs):
        if action == 'export' and 'money' in form.cleaned_data['columns']:
            if not request.user.is_administrator:
                raise ActionInterrupted('Only administrors can export `money` field')

    adminaction_start.connect(myhandler, sender=MyModel, action='export`)


.. _adminaction_end:

``adminaction_end``
===================

Sent **after** the successfully execution of the action.
The handler can rely on the following parameter:

    * sender: :class:`django:django.db.models.Model`
    * action: string. name of the action
    * request: :class:`django:django.core.httpd.HttpRequest`
    * queryset: :class:`django:django.db.models.query.Queryset`
    * modeladmin: :class:`django:django.contrib.admin.ModelAdmin`
    * form: :class:`django:django.forms.Form`
    * errors: dict
    * updated: int
