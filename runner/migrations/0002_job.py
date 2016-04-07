# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-07 07:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('runner', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=200)),
                ('input', models.CharField(max_length=10000)),
                ('output', models.CharField(max_length=10000)),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='runner.Pipeline')),
            ],
        ),
    ]