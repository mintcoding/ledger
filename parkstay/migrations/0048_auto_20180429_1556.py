# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-04-29 07:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parkstay', '0047_auto_20180322_1618'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='override_price',
            field=models.DecimalField(decimal_places=2, default='0.00', max_digits=8),
        ),
    ]
