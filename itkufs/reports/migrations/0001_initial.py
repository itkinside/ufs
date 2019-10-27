# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("accounting", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="List",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="name")),
                ("slug", models.SlugField(verbose_name="slug")),
                (
                    "account_width",
                    models.PositiveSmallIntegerField(
                        help_text="Relative width of cell, 0 to hide",
                        verbose_name="account name width",
                    ),
                ),
                (
                    "short_name_width",
                    models.PositiveSmallIntegerField(
                        help_text="Relative width of cell, 0 to hide",
                        verbose_name="short name width",
                    ),
                ),
                (
                    "balance_width",
                    models.PositiveSmallIntegerField(
                        help_text="Relative width of cell, 0 to hide",
                        verbose_name="balance width",
                    ),
                ),
                (
                    "public",
                    models.BooleanField(
                        default=False,
                        help_text="Should this list be publicly available",
                        verbose_name="Public",
                    ),
                ),
                (
                    "add_active_accounts",
                    models.BooleanField(
                        default=True,
                        help_text="Should all active accounts be added by default",
                        verbose_name="Add active user accounts",
                    ),
                ),
                (
                    "orientation",
                    models.CharField(
                        max_length=1,
                        verbose_name="orientation",
                        choices=[(b"L", "Landscape"), (b"P", "Portrait")],
                    ),
                ),
                (
                    "comment",
                    models.TextField(
                        help_text="Comment shown at bottom on first page",
                        verbose_name="comment",
                        blank=True,
                    ),
                ),
                (
                    "double",
                    models.BooleanField(
                        default=False, help_text="Use two rows per account"
                    ),
                ),
                (
                    "ignore_blocked",
                    models.BooleanField(
                        default=False,
                        help_text="Don't exclude blocked accounts",
                        verbose_name="ignore blocked",
                    ),
                ),
                (
                    "extra_accounts",
                    models.ManyToManyField(
                        to="accounting.Account", blank=b"true"
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        related_name="list_set",
                        verbose_name="group",
                        to="accounting.Group",
                    ),
                ),
            ],
            options={
                "ordering": ("name",),
                "verbose_name": "list",
                "verbose_name_plural": "lists",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="ListColumn",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="name")),
                (
                    "width",
                    models.PositiveSmallIntegerField(verbose_name="width"),
                ),
                (
                    "list",
                    models.ForeignKey(
                        related_name="column_set",
                        verbose_name="list",
                        to="reports.List",
                    ),
                ),
            ],
            options={
                "ordering": ["id"],
                "verbose_name": "list item",
                "verbose_name_plural": "list items",
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name="list", unique_together=set([("slug", "group")])
        ),
    ]
