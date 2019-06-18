# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-05-28 04:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0175_auto_20190527_1644'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityInvoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_reference', models.CharField(blank=True, default='', max_length=50, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='application',
            name='licence_fee',
        ),
        migrations.AddField(
            model_name='applicationselectedactivity',
            name='licence_fee',
            field=models.DecimalField(decimal_places=2, default='0', max_digits=8),
        ),
        migrations.AddField(
            model_name='activityinvoice',
            name='activity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='wildlifecompliance.ApplicationSelectedActivity'),
        ),
    ]
