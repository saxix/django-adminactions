# Mass Update


Update one or more fields of the selected queryset to a common value and/or apply a
`transform_operations`_ to selected field.

|| |
|----------------------|------------------------------------------------------------------------------------------|
|**validate**          |  use obj.save() instead of obj._default_manager.update. Slower but required in some cases (To run some business logic in save() and clean(). Manadatory if use :ref:`transform_operations` |
|**unique_transaction**|  .. versionadded:: 0.0.4 |

**validate**
    use obj.save() instead of obj._default_manager.update. Slower but required in some cases (To run some business logic in save() and clean(). Manadatory if use :ref:`transform_operations`


**Screenshot**

![Mass Update](_static/mass_update.png){ align=left }


## Ignore Fields
<!-- sax:version 1.9 -->

It is possible to prevent some fields to be displayed to avoid changes.
To filter out some fields you need to set `UPDATE_ACTION_IGNORED_FIELDS` settings parameter as follow::

    UPDATE_ACTION_IGNORED_FIELDS = {
        'app_name': {
                'user': ['is_staff', 'is_superuser'],
        },
    }

## Prevent Record to be updated

To prevent record to be updated based on custom logic, it is possible to connect to `mass_update_process` and raise `MassUpdateSkipRecordError`

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




## Transform Operation

<!-- sax:version 0.0.4 -->


Is possible to update fields applying function. |app| comes with a predefined set of functions.
You can anyway `register your own functions <register_transform_function>`


**common to all models**

|<!-- --> | <!-- -->                                                         |
|------------|------------------------------------------------------------------|
|set         | set the value                                                    |
|set null    | set the value to null (only available if the field has null=True


### CharField

    ---------=  ------------------------------------==
    upper       convert to uppercase
    lower       convert to lowercase
    capitalize  capitalize first character
    capwords    capitalize each word
    swapcase    swap the case
    trim        remove leading and trailing whitespace
    ---------=  ------------------------------------==


### IntegerField


    ---------==  ------------------------------------------------------------------=
    add          add the value passed as arg to the current value of the field
    sub          subtract the value passed as arg to the current value of the field
    add_percent  add the `X` percent to the current value
    sub_percent  subtract the `X` percent from the current value
    ---------==  ------------------------------------------------------------------=

### BooleanField


    ---------=  ---------------------------------
    swap        invert (negate) the current value
    ---------=  ---------------------------------

### NullBooleanField


    ---------=  ---------------------------------
    swap        invert (negate) the current value
    ---------=  ---------------------------------

### EmailField`


    ------------=  ------------------------------------==
    change domain  set the domain (@?????) to common value
    ------------=  ------------------------------------==

### URLField`

    ------------=  ------------------------------------------
    change domain  set the protocol (????://) to common value
    ------------=  ------------------------------------------
