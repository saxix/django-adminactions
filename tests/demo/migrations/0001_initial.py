# Generated by Django 2.0.1 on 2018-01-29 00:00

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import demo.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DemoModel",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("char", models.CharField(max_length=255, verbose_name="Chäř")),
                ("integer", models.IntegerField()),
                ("logic", models.BooleanField(default=False)),
                ("date", models.DateField()),
                ("datetime", models.DateTimeField()),
                ("time", models.TimeField()),
                ("decimal", models.DecimalField(decimal_places=3, max_digits=10)),
                ("email", models.EmailField(max_length=254)),
                ("float", models.FloatField()),
                ("bigint", models.BigIntegerField()),
                ("generic_ip", models.GenericIPAddressField()),
                ("url", models.URLField()),
                ("text", models.TextField()),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("unique", models.CharField(max_length=255, unique=True)),
                ("nullable", models.CharField(max_length=255, null=True)),
                ("blank", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "not_editable",
                    models.CharField(blank=True, editable=False, max_length=255, null=True),
                ),
                (
                    "choices",
                    models.IntegerField(choices=[(1, "Choice 1"), (2, "Choice 2"), (3, "Choice 3")]),
                ),
                ("image", models.ImageField(blank=True, null=True, upload_to="")),
                (
                    "subclassed_image",
                    demo.models.SubclassedImageField(blank=True, null=True, upload_to=""),
                ),
            ],
            options={
                "ordering": ("-id",),
            },
        ),
        migrations.CreateModel(
            name="DemoOneToOne",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "demo",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="onetoone",
                        to="demo.DemoModel",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DemoRelated",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "demo",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        to="demo.DemoModel",
                        related_name="related",
                        to_field="uuid",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserDetail",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("note", models.CharField(blank=True, max_length=10)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
