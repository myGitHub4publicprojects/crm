# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-02 06:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0005_auto_20160702_0733'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newinfo',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.Patient'),
        ),
    ]
