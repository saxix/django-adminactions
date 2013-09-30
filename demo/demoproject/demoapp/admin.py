from django.contrib.admin import ModelAdmin
from .models import DemoModel



class DemoModelAdmin(ModelAdmin):
#    list_display = ('char', 'integer', 'logic', 'null_logic',)
    list_display = [f.name for f in DemoModel._meta.fields]
