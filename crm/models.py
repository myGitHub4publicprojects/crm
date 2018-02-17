# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone
from django.conf import settings

from django.contrib.auth.models import User
jakub = User.objects.all().first()

from .ha_list import ha_list

class Patient(models.Model):
	first_name = models.CharField(max_length=120)
	last_name = models.CharField(max_length=120)
	date_of_birth = models.DateField(auto_now=False, auto_now_add=False, null=True, blank=True)
	locations = ["Poznań", "Rakoniewice", "Wolsztyn", "Puszczykowo", "Mosina", "Chodzież", "Trzcianka", "nie podano"]
	location = models.CharField(max_length=120, default = 'nie podano')
	phone_no = models.IntegerField(default = 0)
	invoice_date = models.DateTimeField(null=True, blank=True)
	create_date = models.DateTimeField(auto_now=False, auto_now_add=True)
	noachcreatedate = models.DateField(null=True, blank=True)
	noachID = models.IntegerField(null=True, blank=True)
	notes = models.TextField(null=True, blank=True)
	audiometrist = models.ForeignKey(settings.AUTH_USER_MODEL)
	 # person who added a patient or a new note about patient

	def __unicode__(self):
		return self.first_name + ' ' + self.last_name

class NewInfo(models.Model):
	# provides info about recent actions with a patient eg. control
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
	note = models.TextField()
	audiometrist = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)

	def __str__(self):
		return self.timestamp

class Audiogram(models.Model):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	time_of_test = models.DateTimeField(null=True, blank=True)
	ear = models.CharField(max_length=5, choices=(('left', 'left'),('right', 'right')))
	a250Hz = models.IntegerField(null=True, blank=True)
	a500Hz = models.IntegerField(null=True, blank=True)
	a1kHz = models.IntegerField(null=True, blank=True)
	a2kHz = models.IntegerField(null=True, blank=True)
	a4kHz = models.IntegerField(null=True, blank=True)
	a8kHz = models.IntegerField(null=True, blank=True)
	b250Hz = models.IntegerField(null=True, blank=True)
	b500Hz = models.IntegerField(null=True, blank=True)
	b1kHz = models.IntegerField(null=True, blank=True)
	b2kHz = models.IntegerField(null=True, blank=True)
	b4kHz = models.IntegerField(null=True, blank=True)
	b8kHz = models.IntegerField(null=True, blank=True)

class Hearing_Aid_Main(models.Model):
	ha_make = models.CharField(max_length=20)
	 # eg. Bernafon
	ha_family = models.CharField(max_length=20)
	 # eg. WIN
	ha_model = models.CharField(max_length=20)
	 # eg. 102
	ear = models.CharField(max_length=5, choices=(('left', 'left'),('right', 'right')))
	ha_list = ha_list
	current = models.BooleanField(default=True)
		# this hearing aid currently is being used by a patient
	def __str__(self):
		return self.ha_make + ' ' + self.ha_family + ' ' + self.ha_model + ' ' + self.ear

class Hearing_Aid(Hearing_Aid_Main):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	purchase_date = models.DateField(null=True, blank=True)
	our = models.BooleanField(default=True)
	# kupiony u nas


# class Estimated_Hearing_Aid(Hearing_Aid):
# 	nfz_confirmed = models.DateTimeField(null=True, blank=True)
# 	# data przyniesienia potwierdzonych wnioskow NFZ i wystawienia kosztorysu
# 	estimated_ha = 
# 	# aparat podany kosztorysie

class NFZ_Confirmed(models.Model):
	# confirmed by NFZ application for hearing aid
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	date = models.DateField()
	side = models.CharField(max_length=5, choices=(('left', 'left'),('right', 'right')))
	in_progress = models.BooleanField(default=True)
	# change to False once collected by patient

	# Additonal features:
	# nfz_scans = models.ImageField(upload_to=upload_location,
	# 	null=True,
	# 	blank=True,
	# 	height_field="height_field",
	# 	width_field="width_field")

class PCPR_Estimate(Hearing_Aid_Main):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	# quote for PCPR
	date = models.DateField()
	in_progress = models.BooleanField(default=True)
	# zmien na FALSE przy odbiorze aparatu

class HA_Invoice(Hearing_Aid_Main):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	# hearing aid invoice
	date = models.DateField()
	in_progress = models.BooleanField(default=True)
	# change to False once collected by patient
