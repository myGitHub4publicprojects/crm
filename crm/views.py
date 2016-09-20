from __future__ import unicode_literals
import datetime

from django.utils.encoding import python_2_unicode_compatible
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect

from django.http import HttpResponse, HttpResponseRedirect
from .forms import PatientForm
from .models import Patient, NewInfo, Hearing_Aid, NFZ_Confirmed, PCPR_Estimate, HA_Invoice
from django.core.urlresolvers import reverse
from django.db.models.functions import Lower


def index(request):
	patient_list = Patient.objects.all().order_by(Lower('last_name'))
	# Lower - makes ordering case insensitive
	query = request.GET.get('q')
	if query:
		patient_list = patient_list.filter(last_name__icontains=query)
	context = {'patient_list': patient_list}
	return render(request, 'crm/patient_list.html', context)

def advancedsearch(request):
	patient_list = Patient.objects.all().order_by(Lower('last_name'))
	lname = request.GET.get('lname')
	if lname:
		patient_list = patient_list.filter(last_name__icontains=lname)
	fname = request.GET.get('fname')
	if fname:
		patient_list = patient_list.filter(first_name__icontains=fname)
	loc = request.GET.get('loc')
	if loc:
		patient_list = patient_list.filter(location=loc)

	
	hearing_aids = Hearing_Aid.objects.all()
	ha_make = request.GET.get('ha_make')
	if ha_make:
		hearing_aids = hearing_aids.filter(ha_make=ha_make)
	ha_make_family_model = request.GET.get('ha_make_family_model')
	if ha_make_family_model:
		ha_make, ha_family, ha_model = ha_make_family_model.split('_')
		hearing_aids = hearing_aids.filter(ha_make=ha_make, ha_family=ha_family, ha_model=ha_model)


	ha_purchase_start = request.GET.get('ha_purchase_start')
	ha_purchase_end = request.GET.get('ha_purchase_end')

	#the following code has to be at the end of the block of this view as it changes patient_list into a list thus filtering is not supported
	if ha_make or ha_make_family_model:
		patients_with_ha = [i.patient for i in hearing_aids]
		patient_list = list(set(patient_list).intersection(patients_with_ha))
		# patient_list = [i for i in patient_list if i in patients_with_ha]
	locations = Patient.locations
	ha_list = Hearing_Aid.ha_list
	context = {'patient_list': patient_list, 'locations': locations, 'ha_list': ha_list}
	return render(request, 'crm/advanced_search.html', context)

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
	left_hearing_aid = patient.hearing_aid_set.filter(ear="left").last()
	right_hearing_aid = patient.hearing_aid_set.filter(ear="right").last()
	left_NFZ_confirmed = patient.nfz_confirmed_set.filter(side='left').last()
	if left_NFZ_confirmed and left_NFZ_confirmed.in_progress == False:
		left_NFZ_confirmed = None 
	right_NFZ_confirmed = patient.nfz_confirmed_set.filter(side='right').last()
	if right_NFZ_confirmed and right_NFZ_confirmed.in_progress == False:
		right_NFZ_confirmed = None	
	left_PCPR_estimate = PCPR_Estimate.objects.filter(patient=patient, ear='left').last()
	if left_PCPR_estimate and left_PCPR_estimate.in_progress == False:
		left_PCPR_estimate = None		
	right_PCPR_estimate = PCPR_Estimate.objects.filter(patient=patient, ear='right').last()
	if right_PCPR_estimate and right_PCPR_estimate.in_progress == False:
		right_PCPR_estimate = None
	left_invoice = HA_Invoice.objects.filter(patient=patient, ear='left').last()
	if left_invoice and left_invoice.in_progress == False:
		left_invoice = None
	right_invoice = HA_Invoice.objects.filter(patient=patient, ear='right').last()
	if right_invoice and right_invoice.in_progress == False:
		right_invoice = None
	context = {'patient': patient,
				'left_NFZ_confirmed': left_NFZ_confirmed,
				'right_NFZ_confirmed': right_NFZ_confirmed,
				'left_hearing_aid': left_hearing_aid,
				'right_hearing_aid': right_hearing_aid,
				'left_PCPR_estimate': left_PCPR_estimate,
				'right_PCPR_estimate': right_PCPR_estimate,
				'left_invoice': left_invoice,
				'right_invoice': right_invoice}	
	
	return render(request, 'crm/detail.html', context)

def edit(request, patient_id):
	# displays form for upadating patient details
	patient = get_object_or_404(Patient, pk=patient_id)
	ha_list = Hearing_Aid.ha_list
	ears =  Hearing_Aid.ears
	patient_notes = patient.newinfo_set.order_by('-timestamp')
	right_hearing_aid = patient.hearing_aid_set.filter(ear="right").last()
	left_hearing_aid = patient.hearing_aid_set.filter(ear="left").last()
	left_NFZ_confirmed = patient.nfz_confirmed_set.filter(side='left').last()
	if left_NFZ_confirmed and left_NFZ_confirmed.in_progress == False:
		left_NFZ_confirmed = None 
	right_NFZ_confirmed = patient.nfz_confirmed_set.filter(side='right').last()
	if right_NFZ_confirmed and right_NFZ_confirmed.in_progress == False:
		right_NFZ_confirmed = None	
	left_PCPR_estimate = PCPR_Estimate.objects.filter(patient=patient, ear='left').last()
	if left_PCPR_estimate and left_PCPR_estimate.in_progress == False:
		left_PCPR_estimate = None		
	right_PCPR_estimate = PCPR_Estimate.objects.filter(patient=patient, ear='right').last()
	if right_PCPR_estimate and right_PCPR_estimate.in_progress == False:
		right_PCPR_estimate = None
	left_invoice = HA_Invoice.objects.filter(patient=patient, ear='left').last()
	if left_invoice and left_invoice.in_progress == False:
		left_invoice = None
	right_invoice = HA_Invoice.objects.filter(patient=patient, ear='right').last()
	if right_invoice and right_invoice.in_progress == False:
		right_invoice = None
	context = 	{'patient': patient,
				'ha_list': ha_list,
				'ears': ears,
				'patient_notes': patient_notes,
				'right_hearing_aid': right_hearing_aid,
				'left_hearing_aid': left_hearing_aid,
				'left_NFZ_confirmed': left_NFZ_confirmed,
				'right_NFZ_confirmed': right_NFZ_confirmed,
				'left_PCPR_estimate': left_PCPR_estimate,
				'right_PCPR_estimate': right_PCPR_estimate,
				'time_now': datetime.datetime.now(),
				'left_invoice': left_invoice,
				'right_invoice': right_invoice}

	return render(request, 'crm/edit.html', context)


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
			hearing_aid = Hearing_Aid(patient=patient, ha_make=ha_make, ha_family=ha_family, ha_model=ha_model, ear=ear)
			hearing_aid.save()
			if request.POST[ear + '_purchase_date']:
				hearing_aid.purchase_date = request.POST[ear + '_purchase_date']
				hearing_aid.save()
		except:
			pass


	for ear in Hearing_Aid.ears:
		try:
			request.POST[ear + '_NFZ_confirmed_date']
			nfz_confirmed = NFZ_Confirmed(patient=patient, date=request.POST[ear + '_NFZ_confirmed_date'], side=ear)
			nfz_confirmed.save()
		except:
			pass

	for ear in Hearing_Aid.ears:
		try:
			request.POST[ear + '_ha_estimate']
			ha = request.POST[ear + '_ha_estimate']
			ha_make, ha_family, ha_model = ha.split('_')
			pcpr_estimate = PCPR_Estimate(
				patient=patient,
				ha_make=ha_make,
				ha_family=ha_family,
				ha_model=ha_model,
				ear=ear,
				date=request.POST[ear + '_pcpr_etimate_date'])
			pcpr_estimate.save()
		except:
			pass



	if request.POST['note']:
		patient.notes = request.POST['note']
		patient.save()


	messages.success(request, "Successfully Created")
	return HttpResponseRedirect(reverse('crm:detail', args=(patient_id,)))

def updating(request, patient_id):
	# for updating egzisting patients in database

	patient = Patient.objects.get(pk=patient_id)
	patient.first_name=request.POST['fname']
	patient.last_name=request.POST['lname']
	patient.phone_no=request.POST['usrtel']
	patient.location = request.POST['location']
	update_list = ['first_name', 'last_name', 'phone_no', 'location']
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
	
	print 'data:'
	if request.POST.get('left_ha', None):
		print request.POST['left_ha']

	

	for ear in Hearing_Aid.ears:
		try:
			request.POST[ear + '_ha']
			ha = request.POST[ear + '_ha']
			ha_make, ha_family, ha_model = ha.split('_')
			hearing_aid = Hearing_Aid(patient=patient, ha_make=ha_make, ha_family=ha_family, ha_model=ha_model, ear=ear)
			hearing_aid.save()
			if request.POST.get(ear + '_purchase_date'):
				hearing_aid.purchase_date = request.POST[ear + '_purchase_date']
				hearing_aid.save()
			# notofies that patient has ha bought in other shop
			if request.POST.get(ear + '_ha_other'):
				hearing_aid.our = False
				hearing_aid.save()
		except:
			print 'cos nie poszlo'
			pass


	for ear in Hearing_Aid.ears:
		try:
			request.POST['NFZ_' + ear]
			if not NFZ_Confirmed.objects.filter(patient=patient, side=ear, in_progress=True):
				nfz_confirmed = NFZ_Confirmed(patient=patient, date=request.POST['NFZ_' + ear], side=ear)
			else:
				current = NFZ_Confirmed.objects.get(patient=patient, side=ear, in_progress=True)
				current.date = request.POST['NFZ_' + ear]
				nfz_confirmed = current
			nfz_confirmed.save()
		except:
			pass

	for ear in Hearing_Aid.ears:
			try:
				request.POST[ear + '_pcpr_ha']
				ha = request.POST[ear + '_pcpr_ha']
				ha_make, ha_family, ha_model = ha.split('_')
				pcpr_estimate = PCPR_Estimate(
					patient=patient,
					ha_make=ha_make,
					ha_family=ha_family,
					ha_model=ha_model,
					ear=ear,
					date=request.POST[ear + '_PCPR_date'])
				pcpr_estimate.save()
				print pcpr_estimate.ear
			except:
				pass

	for ear in Hearing_Aid.ears:

		# invoice procedure
		if request.POST.get(ear + '_invoice_ha'):
			ha = request.POST[ear + '_invoice_ha']
			ha_make, ha_family, ha_model = ha.split('_')
			invoice = HA_Invoice(
				patient=patient,
				ha_make=ha_make,
				ha_family=ha_family,
				ha_model=ha_model,
				ear=ear,
				date=request.POST[ear + '_invoice_date'])
			invoice.save()

		# collection procedure
		if request.POST.get(ear + '_collection_confirm'):
			print ear + '_collection_confirm'
			invoiced_ha = HA_Invoice.objects.filter(patient=patient, ear=ear).last()
			ha = Hearing_Aid(
				patient=patient,
				ha_make = invoiced_ha.ha_make,
				ha_family = invoiced_ha.ha_family,
				ha_model = invoiced_ha.ha_model,
				purchase_date = request.POST[ear + '_collection_date'],
				ear=ear)
			ha.save()

			invoice = HA_Invoice.objects.filter(patient=patient, ear=ear).last()
			invoice.in_progress = False
			invoice.save()
			pcpr_estimate = PCPR_Estimate.objects.filter(patient=patient, ear=ear).last()
			pcpr_estimate.in_progress = False
			pcpr_estimate.save()
			nfz_confirmed = NFZ_Confirmed.objects.filter(patient=patient, side=ear).last()
			nfz_confirmed.in_progress = False
			nfz_confirmed.save()

			


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