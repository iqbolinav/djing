# Generated by Django 2.1.1 on 2019-03-06 18:07

from django.db import migrations, models
import django.db.models.deletion
import traf_stat.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('abonapp', '0001_squashed_0008_auto_20181115_1206'),
    ]

    operations = [
        migrations.CreateModel(
            name='StatCache',
            fields=[
                ('last_time', traf_stat.fields.UnixDateTimeField()),
                ('abon', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='abonapp.Abon')),
                ('octets', models.PositiveIntegerField(default=0)),
                ('packets', models.PositiveIntegerField(default=0)),
            ],
            options={
                'db_table': 'flowcache',
                'ordering': ('-last_time',),
            },
        ),
        migrations.RunSQL(sql=(r'ALTER TABLE flowcache ENGINE=MEMORY;',))
    ]
