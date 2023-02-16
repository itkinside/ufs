# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-03-16 06:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="list",
            name="extra_accounts",
            field=models.ManyToManyField(blank="true", to="accounting.Account"),
        ),
        migrations.AlterField(
            model_name="list",
            name="orientation",
            field=models.CharField(
                choices=[("L", "Landscape"), ("P", "Portrait")],
                max_length=1,
                verbose_name="orientation",
            ),
        ),
    ]
