from __future__ import unicode_literals
import datetime

from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone
from .ha_list import ha_list

from django.db import models

class Patient(models.Model):
	first_name = models.CharField(max_length=120)
	last_name = models.CharField(max_length=120)
	date_of_birth = models.DateField(auto_now=False, auto_now_add=False, null=True, blank=True)
	locations = ["Poznan", "Rakoniewice", "Wolsztyn", "Puszczykowo", "Mosina", "Chodziez", "Trzcianka"]
	location = models.CharField(max_length=120)
	phone_no = models.IntegerField(null=True, blank=True)

	invoice_date = models.DateTimeField(null=True, blank=True)
	# data wystawienia faktury i wziecia wyciskow

	# collection_date = models.DateTimeField(null=True, blank=True)
	# # data odbioru
	# final_cost = models.IntegerField()
	# # kwota doplaty pacjenta
	# nfz_scans = models.ImageField(upload_to=upload_location,
	# 	null=True,
	# 	blank=True,
	# 	height_field="height_field",
	# 	width_field="width_field")

	create_date = models.DateTimeField(auto_now=False, auto_now_add=True)
	notes = models.TextField(null=True, blank=True)
	audiometrist_list = ['Barbara', 'Jakub', 'Sylwia']
	audiometrist = models.CharField(max_length=120)
	 # person who added a patient or a new note about patient

	def __str__(self):
		return self.first_name + ' ' + self.last_name

class NewInfo(models.Model):
	# provides info about recent actions with a patient eg. control
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
	note = models.TextField()
	audiometrist = models.CharField(max_length=20, null=True, blank=True)

	def __str__(self):
		return self.timestamp

class Hearing_Aid(models.Model):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	ha_make = models.CharField(max_length=20)
	 # eg. Bernafon
	ha_family = models.CharField(max_length=20)
	 # eg. WIN
	ha_model = models.CharField(max_length=20)
	 # eg. 102
	purchase_date = models.DateField(null=True, blank=True)
	ears = ['left', 'right']
	ear = models.CharField(max_length=14)
	our = models.BooleanField(default=True)
	# kupiony u nas
	ha_list = ha_list

	def __str__(self):
		return self.ha_make + ' ' + self.ha_family + ' ' + self.ha_model + ' ' + self.ear


# class Estimated_Hearing_Aid(Hearing_Aid):
# 	nfz_confirmed = models.DateTimeField(null=True, blank=True)
# 	# data przyniesienia potwierdzonych wnioskow NFZ i wystawienia kosztorysu
# 	estimated_ha = 
# 	# aparat podany kosztorysie

class NFZ_Confirmed(models.Model):
	# potwierdzone przez NFZ wnioski o aparaty
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	date = models.DateField()
	sides = ['left', 'right']
	side = models.CharField(max_length=5)
	in_progress = models.BooleanField(default=True)
	# zmien na FALSE przy odbiorze aparatu

class PCPR_Estimate(Hearing_Aid):
	# kosztorys do PCPR
	date = models.DateField()
	in_progress = models.BooleanField(default=True)
	# zmien na FALSE przy odbiorze aparatu

class HA_Invoice(Hearing_Aid):
	# faktura na aparat
	date = models.DateField()
	in_progress = models.BooleanField(default=True)
	# zmien na FALSE przy odbiorze aparatu
