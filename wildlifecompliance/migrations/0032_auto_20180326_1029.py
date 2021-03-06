# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-03-26 02:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0031_wildlifelicenceactivity'),
    ]

    operations = [
        migrations.CreateModel(
            name='DefaultActivity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wildlifecompliance.WildlifeLicenceActivity')),
                ('activity_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wildlifecompliance.WildlifeLicenceActivityType')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='defaultactivity',
            unique_together=set([('activity_type', 'activity')]),
        ),
    ]
