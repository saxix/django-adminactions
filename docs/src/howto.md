# HowTo

## Register Your Own Transform Function

Transform Operation are manage by proper tranform functions, |app| come with a small set but it's possible
to add extra function.
Transform function are function that accept one or two parameter.



## Use custom Massupdate Form
<!-- sax:version 0.0.4 -->

To customize the Form used by the massupdate action simply create your own Form class and set it as value
of the ``mass_update_form`` attribute to your ``ModelAdmin``. ie::
```python
from adminactions.mass_update import MassUpdateForm


class MyMassUpdateForm(MassUpdateForm):
    class Meta:
         fields = 'field1', 'field2',


class MyModelAdmin(admin.ModelAdmin):
    mass_update_form = MyMassUpdateForm


admin.register(MyModel, MyModelAdmin)
```



## Selectively Register Actions


To register only some selected action simply use the ``site.add_action`` method::
```python

from django.contrib.admin import site
import adminactions.actions as actions


site.add_action(actions.mass_update)
site.add_action(actions.export_as_csv)
```

## Limit Massupdate to certain fields
<!-- sax:version 1.8 -->

```python

class MyModelAdmin(admin.ModelAdmin):
    mass_update_fields = ['name']
```
OR
```python

class MyModelAdmin(admin.ModelAdmin):
    mass_update_exclude = ['pk', 'date']

admin.register(MyModel, MyModelAdmin)
```



## Limit Massupdate hints to certain fields
<!-- sax:version 1.8 -->

```python

class MyModelAdmin(admin.ModelAdmin):
    mass_update_hints = ['name']

admin.register(MyModel, MyModelAdmin)
```
