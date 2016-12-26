# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-12-25 21:54
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('abonapp', '0004_auto_20161220_0102'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='abon',
            options={'permissions': (('can_buy_tariff', '\u041f\u043e\u043a\u0443\u043f\u043a\u0430 \u0442\u0430\u0440\u0438\u0444\u0430 \u0430\u0431\u043e\u043d\u0435\u043d\u0442\u0443'),)},
        ),
        migrations.AlterModelOptions(
            name='abongroup',
            options={'permissions': (('can_add_ballance', '\u041f\u043e\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0435 \u0441\u0447\u0451\u0442\u0430'),)},
        ),
        migrations.AlterModelOptions(
            name='abontariff',
            options={'ordering': ('tariff_priority',), 'permissions': (('can_complete_service', '\u0414\u043e\u0441\u0440\u043e\u0447\u043d\u043e\u0435 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0438\u0435 \u0443\u0441\u043b\u0443\u0433\u0438 \u0430\u0431\u043e\u043d\u0435\u043d\u0442\u0430'), ('can_activate_service', '\u0410\u043a\u0442\u0438\u0432\u0430\u0446\u0438\u044f \u0443\u0441\u043b\u0443\u0433\u0438 \u0430\u0431\u043e\u043d\u0435\u043d\u0442\u0430'))},
        ),
    ]