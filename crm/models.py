# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime, os

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from .validators import xls_only

class SZOI_File(models.Model):
	'''File uploaded from SZOI and containing all stock approved by NFZ'''
	file = models.FileField(upload_to='documents/', validators=[xls_only])
	uploaded_at = models.DateTimeField(auto_now_add=True)

	def filename(self):
		return os.path.basename(self.file.name)

	def get_absolute_url(self):
		return reverse('crm:szoi_detail', kwargs={'pk': self.pk})

	def __unicode__(self):
		return self.filename() + ' ' + str(self.uploaded_at)


class SZOI_File_Usage(models.Model):
	'''when was the uploaded file used what was produced'''
	szoi_file = models.ForeignKey(SZOI_File, on_delete=models.CASCADE)
	used = models.DateTimeField(auto_now_add=True)

	def get_absolute_url(self):
		return reverse('crm:szoi_usage_detail', kwargs={'pk': self.pk})


class SZOI_Errors(models.Model):
	szoi_file_usage = models.ForeignKey(SZOI_File_Usage, on_delete=models.CASCADE)
	error_log = models.TextField()
	line = models.TextField()

class Patient(models.Model):
    	first_name = models.CharField(max_length=120)
	last_name = models.CharField(max_length=120)
	date_of_birth = models.DateField(
		auto_now=False, auto_now_add=False, null=True, blank=True)
	locations = ["Poznań", "Rakoniewice", "Wolsztyn", "Stęszew",
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
	NIP = models.CharField(max_length=20, null=True, blank=True)

	def get_address(self):
		number = self.house_number
		if self.apartment_number:
			number += '/'+self.apartment_number
		if not self.street:
			return '{city} {number}, {zip_code} {city}'.format(city=self.city, number=number, zip_code=self.zip_code)
		return '{street} {number}, {zip_code} {city}'.format(street=self.street, city=self.city, number=number, zip_code=self.zip_code)

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
	current = models.BooleanField(default=True, verbose_name='aktualna')
	note = models.CharField(max_length=200, null=True, blank=True, verbose_name='notatka')

	class Meta:
		abstract = True


class PCPR_Estimate(Finance):
    pass


class Invoice(Finance):
    pass
	# payed = models.BooleanField(default=False, verbose_name='zapłacona')
	# # change this to True once payment received and HA dispenced
	# type = models.CharField(max_length=8, choices=(
	# 	('transfer', 'transfer'), ('cash', 'cash')), verbose_name='rodzaj płatności')
	# date = models.DateField(default=datetime.date.today())

	# def get_number(self):
	# 	return str(self.pk) + self.timestamp.strftime("/%m/%d")
	# def get_absolute_url(self):
	# 	return reverse('crm:invoice_update', kwargs={'pk': self.pk})

# class Corrective_Invoice(Finance):
# 	invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
# 	date = models.DateField(default=datetime.date.today())
# 	def get_number(self):
# 		return str(self.pk) + self.timestamp.strftime("/%m/%d")


class Device(models.Model):
	'''Master class for all devices. Not to be used directly'''
	make = models.CharField(max_length=50, verbose_name='marka')
	family = models.CharField(max_length=50, verbose_name='rodzina')
	model = models.CharField(max_length=50, verbose_name='model')
	price_gross = models.DecimalField(
		max_digits=7, decimal_places=2, default=0, verbose_name='cena brutto')

	VAT_RATE_CHOICES = (
		('zwolniona', 'zwolniona'),
		('0', '0'),
		('5', '5'),
		('8', '8'),
		('23', '23')
		)
	vat_rate = models.CharField(max_length=9,
                              choices=VAT_RATE_CHOICES,
							  default='8',
							  verbose_name='stawka VAT')

	pkwiu_code = models.CharField(max_length=20, verbose_name='kod PKWiU')

	class Meta:
			abstract = True

	def __unicode__(self):
		return ' '.join([self.make, self.family, self.model])

class Our_Device(models.Model):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
	invoice = models.ForeignKey(
		Invoice, on_delete=models.CASCADE, null=True, blank=True)
	estimate = models.ForeignKey(
		PCPR_Estimate, on_delete=models.CASCADE, null=True, blank=True)

	class Meta:
		abstract = True


class Hearing_Aid_Stock(Device):
	'''Company hearing aids that are offered or were offered'''
	added = models.DateField(default=datetime.date.today())
	szoi_new = models.ForeignKey(
            SZOI_File_Usage, related_name="ha_szoi_new", null=True, blank=True)
	szoi_updated = models.ForeignKey(
		SZOI_File_Usage, related_name="ha_szoi_updated", null=True, blank=True)


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
	szoi_new = models.ForeignKey(
            SZOI_File_Usage, related_name="other_szoi_new", null=True, blank=True)
	szoi_updated = models.ForeignKey(
		SZOI_File_Usage, related_name="other_szoi_updated", null=True, blank=True)

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
 
		
class NFZ_Confirmed(NFZ):
	# confirmed by NFZ application for hearing aid
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE)


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


class Reminder_NFZ_Confirmed(Reminder):
	nfz_confirmed = models.ForeignKey(NFZ_Confirmed, on_delete=models.CASCADE)


class Reminder_PCPR(Reminder):
	pcpr = models.ForeignKey(PCPR_Estimate, on_delete=models.CASCADE)


class Reminder_Invoice(Reminder):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)


class Reminder_Collection(Reminder):
	''' Remind that HA collection took place in the past - ask for visit'''
	ha = models.ForeignKey(Hearing_Aid, on_delete=models.CASCADE)



