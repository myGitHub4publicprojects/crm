# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-02 05:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0020_auto_20160801_1359'),
    ]

    operations = [
        migrations.AddField(
            model_name='hearing_aid',
            name='active',
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
