from __future__ import unicode_literals
import datetime

from django.utils.encoding import python_2_unicode_compatible
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect

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
	ha_list = Hearing_Aid.ha_list
	ears =  Hearing_Aid.ears
	locations = Patient.locations
	audiometrist_list = Patient.audiometrist_list
	context = {'ha_list': ha_list, 'ears': ears, 'locations': locations, 'audiometrist_list': audiometrist_list}
	return render(request, 'crm/create.html', context)


def detail(request, patient_id):
	patient = get_object_or_404(Patient, pk=patient_id)
	context = {'patient': patient}
	if patient.hearing_aid_set.filter(ear="left"):
		left_hearing_aid = patient.hearing_aid_set.filter(ear="left")[0]
		context['left_hearing_aid'] = left_hearing_aid
	if patient.hearing_aid_set.filter(ear="right"):
		right_hearing_aid = patient.hearing_aid_set.filter(ear="right")[0]
		context['right_hearing_aid'] = right_hearing_aid
	return render(request, 'crm/detail.html', context)

def edit(request, patient_id):
	# displays form for upadating patient details
	patient = get_object_or_404(Patient, pk=patient_id)
	ha_list = Hearing_Aid.ha_list
	ears =  Hearing_Aid.ears
	return render(request, 'crm/edit.html', {'patient': patient, 'ha_list': ha_list, 'ears': ears})


def store(request):
	# for adding new patients to database
	patient = Patient(first_name=request.POST['fname'],
		last_name=request.POST['lname'],
		date_of_birth=request.POST['bday'],
		phone_no=request.POST['usrtel'],
		audiometrist = request.POST['audiometrist'],
		location = request.POST['location']
		)
	patient.save()
	patient_id = patient.id

	for ear in Hearing_Aid.ears:
		try:
			request.POST[ear + '_ha']
			print request.POST[ear + '_ha']
			ha = request.POST[ear + '_ha']
			ha_make, ha_family, ha_model = ha.split('_')
			hearing_aid = Hearing_Aid(patient=patient, ha_make=ha_make, ha_family=ha_family, ha_model=ha_model, ear=request.POST['ear'])
			hearing_aid.save()
			if request.POST[ear + '_purchase_date']:
				hearing_aid.purchase_date = request.POST[ear + '_purchase_date']
				hearing_aid.save()
		except:
			pass

	if request.POST['note']:
		patient.notes = request.POST['note']
		patient.save()

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

	for ear in Hearing_Aid.ears:
		try:
			request.POST[ear + '_ha']
			print request.POST[ear + '_ha']
			ha = request.POST[ear + '_ha']
			ha_make, ha_family, ha_model = ha.split('_')
			hearing_aid = Hearing_Aid(patient=patient, ha_make=ha_make, ha_family=ha_family, ha_model=ha_model, ear=request.POST['ear'])
			hearing_aid.save()
			if request.POST[ear + '_purchase_date']:
				hearing_aid.purchase_date = request.POST[ear + '_purchase_date']
				hearing_aid.save()
		except:
			pass

	messages.success(request, "Successfully Updated")

	return HttpResponseRedirect(reverse('crm:detail', args=(patient_id,)))

def deleteconfirm(request, patient_id):
	patient = get_object_or_404(Patient, pk=patient_id)
	return render(request, 'crm/delete-confirm.html', {'patient': patient})

def delete_patient(request, patient_id):
	patient = get_object_or_404(Patient, pk = patient_id)
	patient.delete()
	messages.success(request, "Patient %s deleted" % patient.last_name)
	return redirect('crm:index')