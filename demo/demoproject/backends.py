from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User, Permission


class AnyUserBackend(ModelBackend):
    supports_object_permissions = False
    supports_anonymous_user = True

    def get_all_permissions(self, user_obj, obj=None):
        perms = Permission.objects.all().values_list('content_type__app_label', 'codename').order_by()
        return perms

    get_group_permissions = get_all_permissions

    def has_perm(self, user_obj, perm, obj=None):
        return True

    def has_module_perms(self, user_obj, app_label):
        return True


