# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-06-22 03:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0053_merge_20180621_1418'),
    ]

    operations = [
        migrations.RenameField(
            model_name='application',
            old_name='applicant',
            new_name='org_applicant',
        ),
    ]
