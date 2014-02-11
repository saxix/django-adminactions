from django.contrib.admin import ModelAdmin, site
from .models import DemoModel, UserDetail


class UserDetailModelAdmin(ModelAdmin):
    list_display = [f.name for f in UserDetail._meta.fields]

class DemoModelAdmin(ModelAdmin):
#    list_display = ('char', 'integer', 'logic', 'null_logic',)
    list_display = [f.name for f in DemoModel._meta.fields]



site.register(DemoModel, DemoModelAdmin)
site.register(UserDetail, UserDetailModelAdmin)
