from __future__ import unicode_literals
import datetime

from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone

from django.db import models

class Patient(models.Model):
	first_name = models.CharField(max_length=120)
	last_name = models.CharField(max_length=120)
	date_of_birth = models.DateField(auto_now=False, auto_now_add=False, null=True, blank=True)
	locations = ["Poznan", "Rakoniewice", "Wolsztyn", "Puszczykowo", "Mosina", "Chodziez", "Trzcianka"]
	location = models.CharField(max_length=120)
	phone_no = models.IntegerField(null=True, blank=True)
	# nfz_confirmed = models.DateTimeField(null=True, blank=True)
	# # data przyniesienia potwierdzonych wnioskow NFZ i wystawienia kosztorysu
	invoice_date = models.DateTimeField(null=True, blank=True)
	# # data wystawienia faktury i wziecia wyciskow
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
	ha_list = {
		'Bernafon':{
			'WIN':['102', '105', '322'],
			'NEO':['105', '106'],
			'Nevara':['ITCD', 'ITCP']
					},
		'Audioservice':{
			'IDA':['4', '6']
						},
		'Phonak':{
			'Rodzina1':['model1', 'model2']
				},
		'Interton':{
			'Rodzina1':['model1', 'model2']
					}}

	def __str__(self):
		return self.ha_make + ' ' + self.ha_family + ' ' + self.ha_model + ' ' + self.ear
