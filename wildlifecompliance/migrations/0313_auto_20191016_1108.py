# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-10-16 03:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0312_auto_20191015_1713'),
    ]

    operations = [
        migrations.RenameField(
            model_name='legalcase',
            old_name='created_date',
            new_name='case_created_date',
        ),
        migrations.RenameField(
            model_name='legalcase',
            old_name='created_time',
            new_name='case_created_time',
        ),
    ]