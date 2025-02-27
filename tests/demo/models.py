from __future__ import annotations

import uuid

from django.contrib.auth.models import User
from django.db import models


class SubclassedImageField(models.ImageField):
    pass


class DemoModel(models.Model):
    char = models.CharField("Chäř", max_length=255)
    integer = models.IntegerField()
    logic = models.BooleanField(default=False)
    # null_logic = models.NullBooleanField(default=None)
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
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    unique = models.CharField(max_length=255, unique=True)
    nullable = models.CharField(max_length=255, null=True)
    blank = models.CharField(max_length=255, blank=True, null=True)
    not_editable = models.CharField(max_length=255, editable=False, blank=True, null=True)
    choices = models.IntegerField(choices=((1, "Choice 1"), (2, "Choice 2"), (3, "Choice 3")))
    nested_choices = models.IntegerField(choices=(('Group 1', ((1, 'Choice 1.1'), (2, 'Choice 1.2'))),
                                                  ('Group 2', ((3, 'Choice 2.1'), (4, 'Choice 3.1')))),
                                         blank=True, null=True
                                         )

    image = models.ImageField(blank=True, null=True)
    subclassed_image = SubclassedImageField(blank=True, null=True)

    m2m = models.ManyToManyField("self", blank=True)

    class Meta:
        app_label = "demo"
        ordering = ("-id",)


class UserDetail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.CharField(max_length=10, blank=True)

    class Meta:
        app_label = "demo"


class DemoOneToOne(models.Model):
    demo = models.OneToOneField(DemoModel, on_delete=models.CASCADE, related_name="onetoone")

    class Meta:
        app_label = "demo"


class DemoRelated(models.Model):
    demo = models.ForeignKey(DemoModel, on_delete=models.CASCADE, related_name="related", to_field="uuid")

    class Meta:
        app_label = "demo"
