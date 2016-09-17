# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-01 11:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0018_auto_20160801_1316'),
    ]

    operations = [
        migrations.AddField(
            model_name='pcpr_estimate',
            name='in_progress',
            field=models.BooleanField(default=True),
        ),
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
        migrations.AlterField(
            model_name='nfz_confirmed',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.Patient'),
        ),
    ]
