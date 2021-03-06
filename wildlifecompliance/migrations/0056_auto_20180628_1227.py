# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-06-28 04:27
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0055_auto_20180628_0945'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='defaultactivity',
            options={'verbose_name': 'Licenced activity - purpose mapping', 'verbose_name_plural': 'Licenced activity - purpose mappings'},
        ),
        migrations.AlterModelOptions(
            name='defaultactivitytype',
            options={'verbose_name': 'Licenced category - licenced activity mapping', 'verbose_name_plural': 'Licenced category - licenced activity mappings'},
        ),
        migrations.AlterModelOptions(
            name='wildlifelicenceactivity',
            options={'verbose_name': 'Licence purpose', 'verbose_name_plural': 'Licence purposes'},
        ),
        migrations.AlterModelOptions(
            name='wildlifelicenceactivitytype',
            options={'verbose_name': 'Licenced activity', 'verbose_name_plural': 'Licenced activities'},
        ),
        migrations.AlterModelOptions(
            name='wildlifelicenceclass',
            options={'verbose_name': 'Licence category', 'verbose_name_plural': 'Licence categories'},
        ),
    ]
