# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User

from .ha_list import ha_list

class Patient(models.Model):
	first_name = models.CharField(max_length=120)
	last_name = models.CharField(max_length=120)
	date_of_birth = models.DateField(auto_now=False, auto_now_add=False, null=True, blank=True)
	locations = ["Poznań", "Rakoniewice", "Wolsztyn", "Puszczykowo", "Mosina", "Chodzież", "Trzcianka", "nie podano"]
	location = models.CharField(max_length=120, default = 'nie podano')
	phone_no = models.IntegerField(default = 0)
	create_date = models.DateTimeField(auto_now=False, auto_now_add=True)
	noachcreatedate = models.DateField(null=True, blank=True)
	noachID = models.IntegerField(null=True, blank=True)
	notes = models.TextField(null=True, blank=True)
	# person who added a patient or a new note about patient
	audiometrist = models.ForeignKey(settings.AUTH_USER_MODEL)
	# address
	street = models.CharField(max_length=120, null=True, blank=True)
	house_number = models.CharField(max_length=6, null=True, blank=True)
	apartment_number = models.CharField(max_length=6, null=True, blank=True)
	city = models.CharField(max_length=120, null=True, blank=True)
	zip_code = models.CharField(max_length=6, null=True, blank=True)

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

class Invoice(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=False)
    type = models.CharField(max_length=8, choices=(
		('transfer', 'transfer'), ('cash', 'cash')))

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
		return (self.ha_make.encode('utf-8') + ' ' + self.ha_family.encode('utf-8')
                    + ' ' + self.ha_model.encode('utf-8'))

class Hearing_Aid(Hearing_Aid_Main):
	# ear = models.CharField(max_length=5, choices=(
	# 	('left', 'left'), ('right', 'right')))
	# current = models.BooleanField(default=True)
	# 	# this hearing aid currently is being used by a patient

	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	purchase_date = models.DateField(null=True, blank=True)
	our = models.BooleanField(default=True)
	# kupiony u nas
	price_gross = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	# default 0 for adding currenly used hearing aids from other producers
	# with unknown price
	vat_rate = models.IntegerField(default=8)
	pkwiu_code = models.CharField(max_length=20, null=True, blank=True)
	invoice = models.ForeignKey(
		Invoice, on_delete=models.CASCADE, null=True, blank=True)

class NFZ(models.Model):
	date = models.DateField()
	side = models.CharField(max_length=5, choices=(('left', 'left'),('right', 'right')))
	in_progress = models.BooleanField(default=True)
	# change to False once collected by patient
	

class NFZ_Confirmed(NFZ):
	# confirmed by NFZ application for hearing aid
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

	# Additonal features:
	# nfz_scans = models.ImageField(upload_to=upload_location,
	# 	null=True,
	# 	blank=True,
	# 	height_field="height_field",
	# 	width_field="width_field")

class NFZ_New(NFZ):
    # new application form to be confirmed by NFZ
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)


class PCPR_Estimate(Hearing_Aid_Main):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	# quote for PCPR
	date = models.DateField()
	in_progress = models.BooleanField(default=True)
	# zmien na FALSE przy odbiorze aparatu

class Other_Item(models.Model):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	make = models.CharField(max_length=20)
	 # eg. Bernafon
	family = models.CharField(max_length=120)
	# eg. systemy wspomagające słyszenie, wkładka uszna
	model = models.CharField(max_length=120)
	# eg. ROGER CLIP-ON MIC + 2, twarda
	price_gross = models.DecimalField(max_digits=6, decimal_places=2)
	vat_rate = models.IntegerField()
	pkwiu_code = models.CharField(max_length=20, null=True, blank=True)
	invoice = models.ForeignKey(
		Invoice, on_delete=models.CASCADE, null=True, blank=True)
	
	def __unicode__(self):
		return ' '.join([self.make, self.family, self.model])

class HA_Invoice(Hearing_Aid_Main):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	# hearing aid invoice
    date = models.DateField()
    in_progress = models.BooleanField(default=True)
	# change to False once collected by patient


class ReminderManager(models.Manager):
    def active(self):
        return super(ReminderManager, self).filter(
			active=True,
            activation_date__lte=datetime.date.today())

class Reminder(models.Model):
	nfz_new = models.ForeignKey(NFZ_New, null=True, blank=True)
	nfz_confirmed = models.ForeignKey(NFZ_Confirmed, null=True, blank=True)
	pcpr = models.ForeignKey(PCPR_Estimate, null=True, blank=True)
	invoice = models.ForeignKey(HA_Invoice, null=True, blank=True)
	ha = models.ForeignKey(Hearing_Aid, null=True, blank=True)
	active = models.BooleanField(default=True)
	timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
	activation_date = models.DateField(
		default=datetime.date.today() + datetime.timedelta(days=60))
	objects = ReminderManager()
