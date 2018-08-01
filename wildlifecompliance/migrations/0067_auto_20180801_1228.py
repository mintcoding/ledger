# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-08-01 04:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0066_merge_20180730_1535'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessment',
            name='status',
            field=models.CharField(choices=[('awaiting_assessment', 'Awaiting Assessment'), ('assessed', 'Assessed'), ('completed', 'Completed'), ('recalled', 'Recalled')], default='awaiting_assessment', max_length=20, verbose_name='Status'),
        ),
    ]
