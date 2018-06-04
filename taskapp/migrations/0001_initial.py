# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-26 00:20
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import taskapp.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('abonapp', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChangeLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('act_type', models.CharField(choices=[('e', 'Change task'), ('c', 'Create task'), ('d', 'Delete task'),
                                                       ('f', 'Completing tasks'), ('b', 'The task failed')],
                                              max_length=1)),
                ('when', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ExtraComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(verbose_name='Text of comment')),
                ('date_create', models.DateTimeField(auto_now_add=True, verbose_name='Time of create')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL,
                                             verbose_name='Author')),
            ],
            options={
                'verbose_name': 'Extra comment',
                'verbose_name_plural': 'Extra comments',
                'db_table': 'extra_comments',
                'permissions': (('can_view_comments', 'Can view comments'),),
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descr', models.CharField(blank=True, max_length=128, null=True, verbose_name='Description')),
                ('priority',
                 models.CharField(choices=[('A', 'Higher'), ('C', 'Average'), ('E', 'Low')], default='E', max_length=1,
                                  verbose_name='A priority')),
                ('out_date', models.DateField(blank=True, default=taskapp.models.delta_add_days, null=True,
                                              verbose_name='Reality')),
                ('time_of_create', models.DateTimeField(auto_now_add=True, verbose_name='Date of create')),
                ('state', models.CharField(choices=[('S', 'New'), ('C', 'Confused'), ('F', 'Completed')], default='S',
                                           max_length=1, verbose_name='Condition')),
                ('attachment', models.ImageField(blank=True, null=True, upload_to='task_attachments/%Y.%m.%d',
                                                 verbose_name='Attached image')),
                ('mode', models.CharField(
                    choices=[('na', 'not chosen'), ('ic', 'ip conflict'), ('yt', 'yellow triangle'),
                             ('rc', 'red cross'), ('ls', 'weak speed'), ('cf', 'cable break'), ('cn', 'connection'),
                             ('pf', 'periodic disappearance'), ('cr', 'router setup'), ('co', 'configure onu'),
                             ('fc', 'crimp cable'), ('ni', 'Internet crash'), ('ot', 'other')], default='na',
                    max_length=2, verbose_name='The nature of the damage')),
                ('abon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                           to='abonapp.Abon', verbose_name='Subscriber')),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                             related_name='+', to=settings.AUTH_USER_MODEL,
                                             verbose_name='Task author')),
                ('recipients', models.ManyToManyField(related_name='them_task', to=settings.AUTH_USER_MODEL,
                                                      verbose_name='Recipients')),
            ],
            options={
                'db_table': 'task',
                'ordering': ('-id',),
                'permissions': (('can_viewall', 'Access to all tasks'), ('can_remind', 'Reminders of tasks')),
            },
        ),
        migrations.AddField(
            model_name='extracomment',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='taskapp.Task',
                                    verbose_name='Owner task'),
        ),
        migrations.AddField(
            model_name='changelog',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='taskapp.Task'),
        ),
        migrations.AddField(
            model_name='changelog',
            name='who',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+',
                                    to=settings.AUTH_USER_MODEL),
        ),
    ]
