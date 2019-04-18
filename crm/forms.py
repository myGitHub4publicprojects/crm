# -*- coding: utf-8 -*-
from django import forms
from .models import Patient, Invoice

class PatientForm(forms.ModelForm):
	class Meta:
		model = Patient
		fields = [
			"first_name",
			"last_name",
			"phone_no",
			"date_of_birth"
		]

class InvoiceForm(forms.ModelForm):
    class Meta:
    	model = Invoice
    	fields = ['type','note']

class DeviceForm(forms.Form):
	device_type = forms.ChoiceField(
		choices=(('ha', 'Aparat'), ('other', 'Inne')))
	make = forms.CharField(max_length=20)
	# eg. Bernafon
	family = forms.CharField(max_length=120)
	# eg. systemy wspomagające słyszenie, wkładka uszna, WIN
	model = forms.CharField(max_length=120)
 	# eg. ROGER CLIP-ON MIC + 2, twarda, 102
	price_gross = forms.DecimalField(max_digits=8, decimal_places=2)
	vat_rate = forms.IntegerField()
	pkwiu_code = forms.CharField(max_length=20)
	quantity = forms.IntegerField()
	ear = forms.ChoiceField(choices=(
		('left', 'left'), ('right', 'right'), ('both', 'both')))
