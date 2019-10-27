# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("accounting", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Bill",
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
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="created"
                    ),
                ),
                ("description", models.TextField(verbose_name="description")),
                (
                    "group",
                    models.ForeignKey(
                        to="accounting.Group", on_delete=models.CASCADE
                    ),
                ),
                (
                    "transaction",
                    models.ForeignKey(
                        blank=True,
                        to="accounting.Transaction",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="BillingLine",
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
                (
                    "description",
                    models.CharField(
                        max_length=100, verbose_name="description"
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        default=0,
                        verbose_name="amount",
                        max_digits=10,
                        decimal_places=2,
                    ),
                ),
                (
                    "bill",
                    models.ForeignKey(
                        to="billing.Bill", on_delete=models.CASCADE
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
