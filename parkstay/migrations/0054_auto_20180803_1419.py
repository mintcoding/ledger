# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-08-03 06:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parkstay', '0053_booking_send_invoice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='send_invoice',
            field=models.BooleanField(default=True),
        ),
    ]
