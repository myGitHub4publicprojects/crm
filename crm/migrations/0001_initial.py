# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-11-21 09:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Audiogram',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_of_test', models.DateTimeField(blank=True, null=True)),
                ('ear', models.CharField(max_length=14)),
                ('a250Hz', models.IntegerField(blank=True, null=True)),
                ('a500Hz', models.IntegerField(blank=True, null=True)),
                ('a1kHz', models.IntegerField(blank=True, null=True)),
                ('a2kHz', models.IntegerField(blank=True, null=True)),
                ('a4kHz', models.IntegerField(blank=True, null=True)),
                ('a8kHz', models.IntegerField(blank=True, null=True)),
                ('b250Hz', models.IntegerField(blank=True, null=True)),
                ('b500Hz', models.IntegerField(blank=True, null=True)),
                ('b1kHz', models.IntegerField(blank=True, null=True)),
                ('b2kHz', models.IntegerField(blank=True, null=True)),
                ('b4kHz', models.IntegerField(blank=True, null=True)),
                ('b8kHz', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Hearing_Aid_Main',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ha_make', models.CharField(max_length=20)),
                ('ha_family', models.CharField(max_length=20)),
                ('ha_model', models.CharField(max_length=20)),
                ('ear', models.CharField(max_length=14)),
            ],
        ),
        migrations.CreateModel(
            name='NewInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('note', models.TextField()),
                ('audiometrist', models.CharField(blank=True, max_length=20, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='NFZ_Confirmed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('side', models.CharField(max_length=5)),
                ('in_progress', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=120)),
                ('last_name', models.CharField(max_length=120)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('location', models.CharField(default='nie podano', max_length=120)),
                ('phone_no', models.IntegerField(default=0)),
                ('invoice_date', models.DateTimeField(blank=True, null=True)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('noachcreatedate', models.DateField(blank=True, null=True)),
                ('noachID', models.IntegerField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('audiometrist', models.CharField(default='ABC', max_length=120)),
            ],
        ),
        migrations.CreateModel(
            name='HA_Invoice',
            fields=[
                ('hearing_aid_main_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='crm.Hearing_Aid_Main')),
                ('date', models.DateField()),
                ('in_progress', models.BooleanField(default=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.Patient')),
            ],
            bases=('crm.hearing_aid_main',),
        ),
        migrations.CreateModel(
            name='Hearing_Aid',
            fields=[
                ('hearing_aid_main_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='crm.Hearing_Aid_Main')),
                ('purchase_date', models.DateField(blank=True, null=True)),
                ('our', models.BooleanField(default=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.Patient')),
            ],
            bases=('crm.hearing_aid_main',),
        ),
        migrations.CreateModel(
            name='PCPR_Estimate',
            fields=[
                ('hearing_aid_main_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='crm.Hearing_Aid_Main')),
                ('date', models.DateField()),
                ('in_progress', models.BooleanField(default=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.Patient')),
            ],
            bases=('crm.hearing_aid_main',),
        ),
        migrations.AddField(
            model_name='nfz_confirmed',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.Patient'),
        ),
        migrations.AddField(
            model_name='newinfo',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.Patient'),
        ),
        migrations.AddField(
            model_name='audiogram',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.Patient'),
        ),
    ]
