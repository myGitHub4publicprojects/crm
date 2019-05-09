# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse


class Patient(models.Model):
	first_name = models.CharField(max_length=120)
	last_name = models.CharField(max_length=120)
	date_of_birth = models.DateField(
		auto_now=False, auto_now_add=False, null=True, blank=True)
	locations = ["Poznań", "Rakoniewice", "Wolsztyn",
              "Puszczykowo", "Mosina", "Chodzież", "Trzcianka", "nie podano"]
	location = models.CharField(max_length=120, default='nie podano')
	phone_no = models.IntegerField(default=0)
	create_date = models.DateTimeField(auto_now=False, auto_now_add=True)
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
	audiometrist = models.ForeignKey(
		settings.AUTH_USER_MODEL, null=True, blank=True)

	def __unicode__(self):
		return self.timestamp


class Finance(models.Model):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
	updated = models.DateTimeField(auto_now=True, auto_now_add=False)
	current = models.BooleanField(default=True)
	note = models.CharField(max_length=200, null=True, blank=True)

	class Meta:
		abstract = True


class PCPR_Estimate(Finance):
    pass


class Pro_Forma_Invoice(Finance):
    pass


class Invoice(Finance):
	payed = models.BooleanField(default=False)
	# change this to True once payment received and HA dispenced
	type = models.CharField(max_length=8, choices=(
		('transfer', 'transfer'), ('cash', 'cash')))


class Corrective_Invoice(Finance):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)


class Device(models.Model):
    '''Master class for all devices. Not to be used directly'''
    make = models.CharField(max_length=50, verbose_name='marka')
    family = models.CharField(max_length=50, verbose_name='rodzina')
    model = models.CharField(max_length=50, verbose_name='model')
    price_gross = models.DecimalField(
    	max_digits=7, decimal_places=2, default=0, verbose_name='cena brutto')
    vat_rate = models.IntegerField(default=8, verbose_name='stawka VAT')
    pkwiu_code = models.CharField(max_length=20, verbose_name='kod PKWiU')

    class Meta:
    		abstract = True

    def __unicode__(self):
    	return ' '.join([self.make, self.family, self.model])

class Our_Device(models.Model):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	invoice = models.ForeignKey(
		Invoice, on_delete=models.CASCADE, null=True, blank=True)
	corrective_invoice = models.ForeignKey(
            Corrective_Invoice, on_delete=models.CASCADE, null=True, blank=True)
	pro_forma = models.ForeignKey(
		Pro_Forma_Invoice, on_delete=models.CASCADE, null=True, blank=True)
	estimate = models.ForeignKey(
		PCPR_Estimate, on_delete=models.CASCADE, null=True, blank=True)

	class Meta:
		abstract = True

class Hearing_Aid_Stock(Device):
	'''Company hearing aids that are offered or were offered'''
	added = models.DateField(default=datetime.date.today())

	def get_absolute_url(self):
		return reverse('crm:edit_ha', kwargs={'pk': self.pk})

class Hearing_Aid(Device, Our_Device):
	ear = models.CharField(max_length=5, choices=(
		('left', 'left'), ('right', 'right')))
	current = models.BooleanField(default=True)
		# this hearing aid currently is being used by a patient
	purchase_date = models.DateField(null=True, blank=True)
	our = models.BooleanField(default=True)
	# purchased from our company


class Other_Item_Stock(Device):
	'''Company devices that are offered or were offered'''
	added = models.DateField(default=datetime.date.today())

	def get_absolute_url(self):
		return reverse('crm:edit_other', kwargs={'pk': self.pk})


class Other_Item(Device, Our_Device):
    pass


class NFZ(models.Model):
    date = models.DateField()
    side = models.CharField(max_length=5, choices=(
        ('left', 'left'), ('right', 'right')))
    in_progress = models.BooleanField(default=True)
    # change to False once collected by patient

    class Meta:
        abstract = True


class NFZ_New(NFZ):
    # new application form to be confirmed by NFZ
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
        
		
class NFZ_Confirmed(NFZ):
	# confirmed by NFZ application for hearing aid
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

	# Additonal features:
	# nfz_scans = models.ImageField(upload_to=upload_location,
	# 	null=True,
	# 	blank=True,
	# 	height_field="height_field",
	# 	width_field="width_field")


class ReminderManager(models.Manager):
    def active(self):
        return super(ReminderManager, self).filter(
            active=True,
            activation_date__lte=datetime.date.today())


class Reminder(models.Model):
	active = models.BooleanField(default=True)
	timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
	activation_date = models.DateField(
		default=datetime.date.today() + datetime.timedelta(days=60))
	objects = ReminderManager()

	class Meta:
		abstract = True


class Reminder_NFZ_New(Reminder):
	nfz_new = models.ForeignKey(NFZ_New, on_delete=models.CASCADE)


class Reminder_NFZ_Confirmed(Reminder):
	nfz_confirmed = models.ForeignKey(NFZ_Confirmed, on_delete=models.CASCADE)


class Reminder_PCPR(Reminder):
	pcpr = models.ForeignKey(PCPR_Estimate, on_delete=models.CASCADE)


class Reminder_Proforma(Reminder):
	proforma = models.ForeignKey(Pro_Forma_Invoice, on_delete=models.CASCADE)


class Reminder_Invoice(Reminder):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)


class Reminder_Collection(Reminder):
	''' Remind that HA collection took place in the past - ask for visit'''
	ha = models.ForeignKey(Hearing_Aid, on_delete=models.CASCADE)
