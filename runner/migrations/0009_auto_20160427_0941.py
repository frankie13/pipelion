# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-27 09:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('runner', '0008_job_can_submit'),
    ]

    operations = [
        migrations.CreateModel(
            name='InputKey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='command',
            name='input_keys',
            field=models.ManyToManyField(to='runner.InputKey'),
        ),
    ]