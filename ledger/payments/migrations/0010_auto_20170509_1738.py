# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-05-09 09:38
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0009_merge_20170509_1157'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bpayfile',
            name='created',
            field=models.DateTimeField(help_text='File Creation Date Time.'),
        ),
        migrations.AlterField(
            model_name='bpayfile',
            name='file_id',
            field=models.BigIntegerField(help_text='File Identification Number.'),
        ),
        migrations.AlterField(
            model_name='bpaygrouprecord',
            name='modifier',
            field=models.IntegerField(choices=[(1, 'interim/previous day'), (2, 'final/previous day'), (3, 'interim/same day'), (4, 'final/same day')], help_text='As of Date modifier'),
        ),
        migrations.AlterField(
            model_name='bpaygrouprecord',
            name='settled',
            field=models.DateTimeField(help_text='File Settlement Date Time'),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='car',
            field=models.CharField(blank=True, help_text='Customer Additional Reference.', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='cheque_num',
            field=models.IntegerField(default=0, help_text='Number of cheques in deposit'),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='country',
            field=models.CharField(blank=True, help_text='Country of payment.', max_length=3, null=True),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='crn',
            field=models.CharField(help_text='Customer Referencer Number', max_length=20),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='discount_method',
            field=models.CharField(blank=True, help_text='Discount Method Code.', max_length=3, null=True),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='discount_ref',
            field=models.CharField(blank=True, help_text='Discount Reference Code.', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='discretionary_data',
            field=models.CharField(blank=True, help_text='Reason for refund or reversal.', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='entry_method',
            field=models.CharField(blank=True, choices=[('000', 'undefined'), ('001', 'key entry by operator'), ('002', 'touch tone entry by payer'), ('003', 'speech recognition'), ('004', 'internet/on-line banking'), ('005', 'electtronic bill presentment'), ('006', 'batch data entry'), ('007', 'mobile entry')], help_text='Manner in which the payment details are captured.', max_length=3, null=True),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='orig_ref_num',
            field=models.CharField(blank=True, help_text='Contains the original/previous CRN in the case of a refund or reversal.', max_length=21, null=True),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='p_date',
            field=models.DateTimeField(help_text='Date of payment.'),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='p_instruction_code',
            field=models.CharField(choices=[('05', 'payment'), ('15', 'error correction'), ('25', 'reversal')], help_text='Payment instruction method.', max_length=2, validators=[django.core.validators.MinLengthValidator(2)]),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='p_method_code',
            field=models.CharField(choices=[('001', 'Debit Account'), ('101', 'Visa'), ('201', 'Mastercard'), ('301', 'Bankcard')], help_text='Method of payment.', max_length=3, validators=[django.core.validators.MinLengthValidator(3)]),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='payer_name',
            field=models.CharField(blank=True, help_text="Name of payer extracted from payer's account details.", max_length=40, null=True),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='ref_rev_code',
            field=models.CharField(blank=True, choices=[('001', 'payer paid twice'), ('002', 'payer paid wrong account'), ('003', 'payer paid wrong biller'), ('004', 'payer paid wrong amount'), ('005', 'payer did not authorise'), ('400', 'Visa chargeback'), ('500', 'MasterCard chargeback'), ('600', 'Bankcard chargeback')], help_text='Reason code for reversal or refund.', max_length=3, null=True),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='service_code',
            field=models.CharField(help_text='Unique identification for a service provider realting to a bill.', max_length=7, validators=[django.core.validators.MinLengthValidator(1)]),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='state',
            field=models.CharField(blank=True, help_text='State code of payer institution.', max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='txn_ref',
            field=models.CharField(help_text='Transaction Reference Number', max_length=21, validators=[django.core.validators.MinLengthValidator(12)]),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='type',
            field=models.CharField(choices=[('399', 'credit'), ('699', 'debit')], help_text='Indicates whether it is a credit or debit item', max_length=3, validators=[django.core.validators.MinLengthValidator(3)]),
        ),
    ]
