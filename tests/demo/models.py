# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib.admin import ModelAdmin, site
from django.contrib.auth.models import User
from django.db import models


class DemoModel(models.Model):
    char = models.CharField('Chäř', max_length=255)
    integer = models.IntegerField()
    logic = models.BooleanField(default=False)
    null_logic = models.NullBooleanField(default=None)
    date = models.DateField()
    datetime = models.DateTimeField()
    time = models.TimeField()
    decimal = models.DecimalField(max_digits=10, decimal_places=3)
    email = models.EmailField()
    #    filepath = models.FilePathField(path=__file__)
    float = models.FloatField()
    bigint = models.BigIntegerField()
    # ip = models.IPAddressField()
    generic_ip = models.GenericIPAddressField()
    url = models.URLField()
    text = models.TextField()

    unique = models.CharField(max_length=255, unique=True)
    nullable = models.CharField(max_length=255, null=True)
    blank = models.CharField(max_length=255, blank=True, null=True)
    not_editable = models.CharField(max_length=255, editable=False, blank=True, null=True)
    choices = models.IntegerField(choices=((1, 'Choice 1'), (2, 'Choice 2'), (3, 'Choice 3')))

    class Meta:
        app_label = 'demo'


class UserDetail(models.Model):
    user = models.ForeignKey(User)
    note = models.CharField(max_length=10, blank=True)

    class Meta:
        app_label = 'demo'


class UserDetailModelAdmin(ModelAdmin):
    list_display = [f.name for f in UserDetail._meta.fields]


class DemoModelAdmin(ModelAdmin):
    # list_display = ('char', 'integer', 'logic', 'null_logic',)
    list_display = [f.name for f in DemoModel._meta.fields]


site.register(DemoModel, DemoModelAdmin)
site.register(UserDetail, UserDetailModelAdmin)
