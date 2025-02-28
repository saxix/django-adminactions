# Signals

{{app}} provides the following signals:

* [[#adminaction_requested]]
* [[#adminaction_start]]
* [[#adminaction_end]]

## adminaction_requested


Sent when the action is requested (ie click 'Go' in the admin changelist view).
The handler can raise a :ref:`actioninterrupted` to interrupt
the action's execution. The handler can rely on the following parameter:


* sender: [django.db.models.Model][]
* action: string. name of the action
* request: [django.http.HttpRequest][]
* queryset: [django.db.models.query.QuerySet][]
* modeladmin: [django.contrib.admin.ModelAdmin][]


Example::
```python

from adminactions.exceptions import ActionInterrupted
from adminactions.signals import adminaction_requested

def myhandler(sender, action, request, queryset, modeladmin, **kwargs):
    if action == 'mass_update' and queryset.filter(locked==True).exists():
        raise ActionInterrupted('Queryset cannot contains locked records')

adminaction_requested.connect(myhandler, sender=MyModel, action='mass_update`)
```

## adminaction_start

Sent after the form has been validated (ie click 'Apply' in the action Form),
**just before** the execution of the action.
The handler can raise a :ref:`actioninterrupted` to avoid the stop execution.
The handler can rely on the following parameter:

* sender: [django.db.models.Model][]
* action: string. name of the action
* request: [django.http.HttpRequest][]
* queryset: [django.db.models.query.QuerySet][]
* modeladmin: [django.contrib.admin.ModelAdmin][]
* form: :class:`django:django.forms.Form`

Example

```python
from adminactions.signals import adminaction_start

def myhandler(sender, action, request, queryset, modeladmin, form, **kwargs):
    if action == 'export' and 'money' in form.cleaned_data['columns']:
        if not request.user.is_administrator:
            raise ActionInterrupted('Only administrors can export `money` field')

adminaction_start.connect(myhandler, sender=MyModel, action='export`)

```


## adminaction_end


Sent **after** the successfully execution of the action.
The handler can rely on the following parameter:

* sender: [django.db.models.Model][]
* action: string. name of the action
* request: [django.http.HttpRequest][]
* queryset: [django.db.models.query.QuerySet][]
* modeladmin: [django.contrib.admin.ModelAdmin][]
* form: [django.forms.Form][]
* errors: dict
* updated: int




## mass_update_process


Sent **before** the record is updated:
The handler can rely on the following parameter:

* sender: [django.db.models.Model][]
* request: [django.http.HttpRequest][]
* queryset: [django.db.models.query.QuerySet][]

Es:
```python
from django.contrib.auth.models import User
from django.dispatch import receiver
from adminactions.signals import mass_update_process
from adminactions.exceptions import MassUpdateSkipRecordError


@receiver(mass_update_process, sender=User)
def my_handler(sender, record: User, **kwargs):
    if record.is_superuser:
        raise MassUpdateSkipRecordError

```
