from __future__ import unicode_literals
import datetime

from django.utils.encoding import python_2_unicode_compatible
from django.contrib import messages
from django.shortcuts import get_object_or_404, render

from django.http import HttpResponse, HttpResponseRedirect
from .forms import PatientForm
from .models import Patient, NewInfo, Hearing_Aid
from django.core.urlresolvers import reverse


def index(request):
	patient_list = Patient.objects.all()
	# order them by last name?
	context = {'patient_list': patient_list}
	return render(request, 'crm/patient_list.html', context)

def create(request):
	# upadates database with details collected in edit view form
	return render(request, 'crm/create.html', {})


def detail(request, patient_id):
	patient = get_object_or_404(Patient, pk=patient_id)
	return render(request, 'crm/detail.html', {'patient': patient})

def edit(request, patient_id):
	# displays form for upadating patient details
	patient = get_object_or_404(Patient, pk=patient_id)
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
	return render(request, 'crm/edit.html', {'patient': patient, 'ha_list': ha_list})


def store(request):
	# for adding new patients to database
	patient = Patient(first_name=request.POST['fname'],
		last_name=request.POST['lname'],
		date_of_birth=request.POST['bday'],
		phone_no=request.POST['usrtel'])
	patient.save()
	patient_id = patient.id

	if request.POST['ha_name_left']:
		ha = Hearing_Aid(patient=patient,
			ha_name=request.POST['ha_name_left'],
			ear='left'
			)
		ha.save()
		if request.POST['purchase_date']:
			ha.purchase_date=request.POST['purchase_date']
			ha.save()

	if request.POST['ha_name_right']:
		ha = Hearing_Aid(patient=patient,
			ha_name=request.POST['ha_name_right'],
			ear='right'
			)
		ha.save()
		if request.POST['purchase_date']:
			ha.purchase_date=request.POST['purchase_date']
			ha.save()
	messages.success(request, "Successfully Created")
	return HttpResponseRedirect(reverse('crm:detail', args=(patient_id,)))

def updating(request, patient_id):
	# for updating patients already in database

	patient = Patient.objects.get(pk=patient_id)
	patient.first_name=request.POST['fname']
	patient.last_name=request.POST['lname']
	patient.phone_no=request.POST['usrtel']
	update_list = ['first_name', 'last_name', 'phone_no']
	if request.POST['bday']:
		patient.date_of_birth=request.POST['bday']
		update_list.append('date_of_birth')
	
	patient.save(update_fields=update_list)

	if request.POST['new_note']:
		new_info = NewInfo(patient=patient, note=request.POST['new_note'])
		new_info.save()

	try:
		new_info.audiometrist = request.POST['audiometrist']
		new_info.save()
	except:
		pass
	#  for some reason this does not work:
	# if request.POST['audiometrist']:
	# 	new_info.audiometrist = request.POST['audiometrist']
	# 	new_info.save()

	# print request.POST['level2']
	# print request.POST['level1']
	# print request.POST['level0']

	messages.success(request, "Successfully Updated")
	return HttpResponseRedirect(reverse('crm:detail', args=(patient_id,)))