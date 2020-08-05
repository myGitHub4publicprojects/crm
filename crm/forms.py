# -*- coding: utf-8 -*-
from django import forms
from .models import (Patient, Hearing_Aid_Stock, Other_Item_Stock, SZOI_File_Usage)

class PatientForm(forms.ModelForm):
	class Meta:
		model = Patient
		fields = [
			"first_name",
			"last_name",
			"phone_no",
			"date_of_birth"
		]


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
	VAT_RATE_CHOICES = (
                    ('zwolniona', 'zwolniona'),
                    ('0', '0'),
                    ('5', '5'),
                    ('8', '8'),
                    ('23', '23')
        )
	vat_rate = forms.ChoiceField(choices=VAT_RATE_CHOICES)
	pkwiu_code = forms.CharField(max_length=20)
	quantity = forms.IntegerField()
	ear = forms.ChoiceField(choices=(
		('left', 'left'), ('right', 'right'), ('both', 'both')))


class Hearing_Aid_StockForm(forms.ModelForm):
	class Meta:
		model = Hearing_Aid_Stock
		fields = ['make', 'family', 'model',
                'pkwiu_code', 'vat_rate', 'price_gross']

	def clean(self):
    	# save only capitalized make, family and model names
		make = self.cleaned_data['make'] = self.cleaned_data['make'].capitalize()
		family = self.cleaned_data['family'] = self.cleaned_data['family'].capitalize()
		model = self.cleaned_data['model'] = self.cleaned_data['model'].capitalize()

		# prevent adding objects with names that already exists in a db
		existing = Hearing_Aid_Stock.objects.filter(make__iexact=make,
                                              family__iexact=family,
                                              model__iexact=model)
		existing = existing.exclude(id=self.instance.id)
		if existing.exists():
			raise forms.ValidationError("Jest już aparat o takiej nazwie")


class Other_Item_StockForm(forms.ModelForm):
	class Meta:
		model = Other_Item_Stock
		fields = ['make', 'family', 'model',
					'pkwiu_code', 'vat_rate', 'price_gross']

	def clean(self):
    	# save only capitalized make, family and model names
		make = self.cleaned_data['make'] = self.cleaned_data['make'].capitalize()
		family = self.cleaned_data['family'] = self.cleaned_data['family'].upper()
		model = self.cleaned_data['model'] = self.cleaned_data['model'].upper()

		# prevent adding objects with names that already exists in a db
		existing = Other_Item_Stock.objects.filter(make__iexact=make,
                                              family__iexact=family,
                                              model__iexact=model)
		existing = existing.exclude(id=self.instance.id)
		if existing.exists():
			raise forms.ValidationError("Jest już produkt o takiej nazwie")


class SZOI_Usage_Form(forms.ModelForm):
    class Meta:
    	model = SZOI_File_Usage
    	fields = ['szoi_file']
