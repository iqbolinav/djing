# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-05-17 13:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abonapp', '0019_abon_ip_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='extrafieldsmodel',
            name='title',
            field=models.CharField(default='no title', max_length=16),
        ),
        migrations.AlterField(
            model_name='extrafieldsmodel',
            name='field_type',
            field=models.CharField(choices=[('int', 'Цифровое поле'), ('str', 'Текстовое поле'), ('dbl', 'Дробное с плавающей точкой'), ('ipa', 'IP Адрес')], default='str', max_length=3),
        ),
    ]
