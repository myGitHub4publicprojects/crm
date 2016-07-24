# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-24 07:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0012_auto_20160724_0940'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hearing_aid',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.Patient'),
        ),
        migrations.AlterField(
            model_name='newinfo',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.Patient'),
        ),
    ]
