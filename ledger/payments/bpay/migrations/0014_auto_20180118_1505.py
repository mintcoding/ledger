# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-01-18 07:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bpay', '0013_bpayjobrecipient'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bpaytransaction',
            name='original_crn',
            field=models.CharField(blank=True, help_text='Customer Referencer Number', max_length=20, null=True),
        ),
    ]
