# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.encoding import python_2_unicode_compatible
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect

from django.http import HttpResponse, HttpResponseRedirect
from .forms import PatientForm
from .models import (Patient, Audiogram, NewInfo, Hearing_Aid, NFZ_Confirmed,
					PCPR_Estimate, HA_Invoice, Audiogram)
from .noach_file_handler import noach_file_handler
from django.core.urlresolvers import reverse
from django.db.models.functions import Lower
from django.db.models import Q

ears = ['left', 'right']

def index(request):
	#x = Lower('last_name')
	order_by = request.GET.get('order_by','last_name')
	if order_by == 'last_name' or order_by == 'first_name':
		patient_list = Patient.objects.all().order_by(Lower(order_by))
	else:
		patient_list = Patient.objects.all().order_by(order_by)
	# Lower - makes ordering case insensitive
	query = request.GET.get('q')
	if query:
		patient_list = patient_list.filter(last_name__icontains=query)

	paginator = Paginator(patient_list, 50) # Show X patients per page

	page = request.GET.get('page')
	try:
		patients = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page.
		patients = paginator.page(1)
	except EmptyPage:
		# If page is out of range (e.g. 9999), deliver last page of results.
		patients = paginator.page(paginator.num_pages)

	context = {'patients': patients}
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

	def patients_from_ha(HA_queryset):
		patients_id = [i.patient.id for i in HA_queryset]
		return Patient.objects.filter(id__in=patients_id)

    # search by ha make
	ha_make = request.GET.get('ha_make')
	if ha_make:
		all_ha_make = Hearing_Aid.objects.filter(ha_make=ha_make)
		patient_list = patient_list & patients_from_ha(all_ha_make)

	# search by ha make family and model
	ha_make_family_model = request.GET.get('ha_make_family_model')
	if ha_make_family_model:
		ha_make, ha_family, ha_model = ha_make_family_model.split('_')
		all_such_has = Hearing_Aid.objects.filter(ha_make=ha_make, ha_model=ha_model, ha_family=ha_family)
		patient_list = patient_list & patients_from_ha(all_such_has)

	# search by dates of purchase
	if request.GET.get('s_purch_date') or request.GET.get('e_purch_date'):
		ha_purchase_start = request.GET.get('s_purch_date') or '1990-01-01'
		ha_purchase_end = request.GET.get('e_purch_date') or str(datetime.datetime.today().date())
		all_such_has = Hearing_Aid.objects.filter(
			purchase_date__range=[ha_purchase_start,ha_purchase_end])
		patient_list = patient_list & patients_from_ha(all_such_has)

	locations = Patient.locations
	ha_list = Hearing_Aid.ha_list
	context = {'patient_list': patient_list, 'locations': locations, 'ha_list': ha_list}
	return render(request, 'crm/advanced_search.html', context)

def create(request):
	ha_list = Hearing_Aid.ha_list
	locations = Patient.locations
	audiometrist_list = Patient.audiometrist_list
	context = {'ha_list': ha_list, 'ears': ears, 'locations': locations, 'audiometrist_list': audiometrist_list}
	return render(request, 'crm/create.html', context)

def edit(request, patient_id):
	# displays form for upadating patient details
	patient = get_object_or_404(Patient, pk=patient_id)
	right_hearing_aid = patient.hearing_aid_set.filter(ear="right").last()
	left_hearing_aid = patient.hearing_aid_set.filter(ear="left").last()
	nfz_left_qs = patient.nfz_confirmed_set.filter(side='left')
	nfz_right_qs = patient.nfz_confirmed_set.filter(side='right')
	left_PCPR_qs = PCPR_Estimate.objects.filter(patient=patient, ear='left')
	right_PCPR_qs = PCPR_Estimate.objects.filter(patient=patient, ear='right')
	left_invoice_qs = HA_Invoice.objects.filter(patient=patient, ear='left')
	right_invoice_qs = HA_Invoice.objects.filter(patient=patient, ear='right')

	def last_and_previous(queryset):
		'''returns last obj or None of a qs as "last" and
		all but last items of such qs'''
		result = {'last': queryset.last(), 'previous': queryset}
		if queryset:
			if queryset.last().in_progress == False:
				result['last'] = None
		if len(queryset) > 1:
			result['previous'] = queryset.order_by('-id')[1:]
		return result

	context = {'patient': patient,
			'ha_list': Hearing_Aid.ha_list,
			'ears': ears,
			'patient_notes': patient.newinfo_set.order_by('-timestamp'),
			'right_hearing_aid': right_hearing_aid,
			'left_hearing_aid': left_hearing_aid,
			'left_NFZ_confirmed_all': last_and_previous(nfz_left_qs)['previous'],
			'left_NFZ_confirmed': last_and_previous(nfz_left_qs)['last'],
			'right_NFZ_confirmed_all': last_and_previous(nfz_right_qs)['previous'],
			'right_NFZ_confirmed': last_and_previous(nfz_right_qs)['last'],
			'left_PCPR_estimate_all': last_and_previous(left_PCPR_qs)['previous'],
			'left_PCPR_estimate': last_and_previous(left_PCPR_qs)['last'],
			'right_PCPR_estimate_all': last_and_previous(right_PCPR_qs)['previous'],
			'right_PCPR_estimate': last_and_previous(right_PCPR_qs)['last'],
			'left_invoice_all': last_and_previous(left_invoice_qs)['previous'],
			'left_invoice': last_and_previous(left_invoice_qs)['last'],
			'right_invoice_all': last_and_previous(right_invoice_qs)['previous'],
			'right_invoice': last_and_previous(right_invoice_qs)['last']
			}

	if patient.audiogram_set.filter(ear="left"):
		left_audiogram = patient.audiogram_set.filter(ear="left").order_by('time_of_test').last()
		context['left_audiogram'] = left_audiogram
	if patient.audiogram_set.filter(ear="right"): 
		right_audiogram = patient.audiogram_set.filter(ear="right").order_by('time_of_test').last()
		context['right_audiogram'] = right_audiogram

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


	messages.success(request, "Pomyślnie utworzono")
	return HttpResponseRedirect(reverse('crm:edit', args=(patient_id,)))

def updating(request, patient_id):
	# for updating egzisting patients in database

	print request.POST

	patient = Patient.objects.get(pk=patient_id)


	print 'prawe: ', patient.hearing_aid_set.filter(ear="right")
	print 'lewe: ', patient.hearing_aid_set.filter(ear="right")

	print 'pcpr left: ', PCPR_Estimate.objects.filter(patient=patient, ear='left')
	print 'pcpr right: ', PCPR_Estimate.objects.filter(patient=patient, ear='right')



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
	
	print 'data:'
	if request.POST.get('left_ha', None):
		print request.POST['left_ha']

	

	for ear in ears:
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
			pass


	for ear in ears:
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

	for ear in ears:
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
			print 'pcrpr est', pcpr_estimate.ha_model, pcpr_estimate.ear
		except:
			pass

	for ear in ears:

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

			
	if request.POST.get('remove_audiogram') == 'remove':
		current_left_audiogram = patient.audiogram_set.filter(ear = 'left').order_by('-time_of_test').last()
		current_right_audiogram = patient.audiogram_set.filter(ear = 'right').order_by('-time_of_test').last()
		if current_left_audiogram: current_left_audiogram.delete()
		if current_right_audiogram: current_right_audiogram.delete()

	messages.success(request, "Zaktualizowano dane")

	return HttpResponseRedirect(reverse('crm:edit', args=(patient_id,)))

def deleteconfirm(request, patient_id):
	patient = get_object_or_404(Patient, pk=patient_id)
	return render(request, 'crm/delete-confirm.html', {'patient': patient})

def delete_patient(request, patient_id):
	patient = get_object_or_404(Patient, pk = patient_id)
	patient.delete()
	messages.success(request, "Pacjent %s usunięty" % patient.last_name)
	return redirect('crm:index')

def select_noach_file(request):
	''' enables selecting a noach file from user computer'''
	return render(request, 'crm/select_noach_file.html')

def import_from_noach(request):
	'''use a xml file with patients exported from Noach to create new patients, audiograms and ha.
	If patient already in database, update audiograms and ha '''

	# read xml file
	# noach_patients =		#dict

	patients = Patient.objects.all()
	noach_file = request.FILES.get('noach_file')
	# a dict where NoachPatientID is a key and dict with patient data is a value
	noach_patients = noach_file_handler(noach_file)
	# a list of patients from noach_file that are not present in crm
	to_be_created = []
	remove_list = []  # items to be removed from to_be_created


	for patient in patients:
		if patient.noachID and patient.noachID in noach_patients and \
		patient.noachcreatedate ==  datetime.datetime.strptime(noach_patients[patient.noachID]["noachcreatedate"], '%Y-%m-%d').date():



			# print 'jest w crm: ', patient.noachID
			# print noach_patients


			# 		update audiograms if older than in noach file
			if noach_patients[patient.noachID].get('last_audiogram'):
				current_left_audiogram = patient.audiogram_set.filter(ear = 'left').order_by('-time_of_test').last()
				current_right_audiogram = patient.audiogram_set.filter(ear = 'right').order_by('-time_of_test').last()
				noach_audiograms_time = datetime.datetime.strptime(noach_patients[patient.noachID]['last_audiogram']['time_of_test'], '%Y-%m-%dT%H:%M:%S')

				if current_left_audiogram:
					print 'current left stary:', current_left_audiogram.time_of_test > noach_audiograms_time
					if current_left_audiogram.time_of_test > noach_audiograms_time and noach_patients[patient.noachID]['last_audiogram']['results'].get('AirConductorLeft'):
						
						current_left_audiogram.time_of_test = noach_audiograms_time
						update_list = ['time_of_test']

						a250Hz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(250)
						if a250Hz:
							current_left_audiogram.a250Hz = a250Hz
							update_list.append('a250Hz')
						a500Hz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(500)
						if a500Hz:
							current_left_audiogram.a500Hz = a500Hz
							update_list.append('a500Hz')
						a1kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(1000)
						if a1kHz:
							current_left_audiogram.a1kHz = a1kHz
							update_list.append('a1kHz')
						a2kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(2000)
						if a2kHz:
							current_left_audiogram.a2kHz = a2kHz
							update_list.append('a2kHz')
						a4kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(4000)
						if a4kHz:
							current_left_audiogram.a4kHz = a4kHz
							update_list.append('a4kHz')
						a8kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(8000)
						if a8kHz:
							current_left_audiogram.a8kHz = a8kHz
							update_list.append('a8kHz')

						if noach_patients[patient.noachID]['last_audiogram']['results'].get('BoneConductorRight'):
							b250Hz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(250)
							if b250Hz:
								current_left_audiogram.b250Hz = b250Hz
								update_list.append('b250Hz')
							b500Hz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(500)
							if b500Hz:
								current_left_audiogram.b500Hz = b500Hz
								update_list.append('b500Hz')
							b1kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(1000)
							if b1kHz:
								current_left_audiogram.b1kHz = b1kHz
								update_list.append('b1kHz')
							b2kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(2000)
							if b2kHz:
								current_left_audiogram.b2kHz = b2kHz
								update_list.append('b2kHz')
							b4kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(4000)
							if b4kHz:
								current_left_audiogram.b4kHz = b4kHz
								update_list.append('b4kHz')
							b8kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(8000)
							if b8kHz:
								current_left_audiogram.b8kHz = b8kHz
								update_list.append('b8kHz')



						current_left_audiogram.save(update_fields=update_list)

				else:
					print 'else left'


					new_left_audiogram = Audiogram(patient = patient, time_of_test = noach_audiograms_time, ear = 'left')
					new_left_audiogram.save()
					update_list = []
					if noach_patients[patient.noachID]['last_audiogram']['results'].get('AirConductorLeft'):
						a250Hz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorLeft'].get(250)
						if a250Hz:
							new_left_audiogram.a250Hz = a250Hz
							update_list.append('a250Hz')
						a500Hz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorLeft'].get(500)
						if a500Hz:
							new_left_audiogram.a500Hz = a500Hz
							update_list.append('a500Hz')
						a1kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorLeft'].get(1000)
						if a1kHz:
							new_left_audiogram.a1kHz = a1kHz
							update_list.append('a1kHz')
						a2kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorLeft'].get(2000)
						if a2kHz:
							new_left_audiogram.a2kHz = a2kHz
							update_list.append('a2kHz')
						a4kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorLeft'].get(4000)
						if a4kHz:
							new_left_audiogram.a4kHz = a4kHz
							update_list.append('a4kHz')
						a8kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorLeft'].get(8000)
						if a8kHz:
							new_left_audiogram.a8kHz = a8kHz
							update_list.append('a8kHz')

						if noach_patients[patient.noachID]['last_audiogram']['results'].get('BoneConductorLeft'):
							b250Hz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorLeft'].get(250)
							if b250Hz:
								new_left_audiogram.b250Hz = b250Hz
								update_list.append('b250Hz')
							b500Hz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorLeft'].get(500)
							if b500Hz:
								new_left_audiogram.b500Hz = b500Hz
								update_list.append('b500Hz')
							b1kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorLeft'].get(1000)
							if b1kHz:
								new_left_audiogram.b1kHz = b1kHz
								update_list.append('b1kHz')
							b2kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorLeft'].get(2000)
							if b2kHz:
								new_left_audiogram.b2kHz = b2kHz
								update_list.append('b2kHz')
							b4kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorLeft'].get(4000)
							if b4kHz:
								new_left_audiogram.b4kHz = b4kHz
								update_list.append('b4kHz')
							b8kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorLeft'].get(8000)
							if b8kHz:
								new_left_audiogram.b8kHz = b8kHz
								update_list.append('b8kHz')



						new_left_audiogram.save(update_fields=update_list)

						print 'dodalem lewy'

				if current_right_audiogram:
					print 'current right stary:', current_right_audiogram.time_of_test > noach_audiograms_time
					if current_right_audiogram.time_of_test > noach_audiograms_time and noach_patients[patient.noachID]['last_audiogram']['results'].get('AirConductorRight'):
						
						current_right_audiogram.time_of_test = noach_audiograms_time
						update_list = ['time_of_test']


						a250Hz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(250)
						if a250Hz:
							current_right_audiogram.a250Hz = a250Hz
							update_list.append('a250Hz')
						a500Hz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(500)
						if a500Hz:
							current_right_audiogram.a500Hz = a500Hz
							update_list.append('a500Hz')
						a1kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(1000)
						if a1kHz:
							current_right_audiogram.a1kHz = a1kHz
							update_list.append('a1kHz')
						a2kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(2000)
						if a2kHz:
							current_right_audiogram.a2kHz = a2kHz
							update_list.append('a2kHz')
						a4kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(4000)
						if a4kHz:
							current_right_audiogram.a4kHz = a4kHz
							update_list.append('a4kHz')
						a8kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(8000)
						if a8kHz:
							current_right_audiogram.a8kHz = a8kHz
							update_list.append('a8kHz')

						if noach_patients[patient.noachID]['last_audiogram']['results'].get('BoneConductorRight'):
							b250Hz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(250)
							if b250Hz:
								current_right_audiogram.b250Hz = b250Hz
								update_list.append('b250Hz')
							b500Hz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(500)
							if b500Hz:
								current_right_audiogram.b500Hz = b500Hz
								update_list.append('b500Hz')
							b1kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(1000)
							if b1kHz:
								current_right_audiogram.b1kHz = b1kHz
								update_list.append('b1kHz')
							b2kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(2000)
							if b2kHz:
								current_right_audiogram.b2kHz = b2kHz
								update_list.append('b2kHz')
							b4kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(4000)
							if b4kHz:
								current_right_audiogram.b4kHz = b4kHz
								update_list.append('b4kHz')
							b8kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(8000)
							if b8kHz:
								current_right_audiogram.b8kHz = b8kHz
								update_list.append('b8kHz')



						current_right_audiogram.save(update_fields=update_list)

				else:
					# print 'else right'
					# print 'a1kHz: ', noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(1000)


					new_right_audiogram = Audiogram(patient = patient, time_of_test = noach_audiograms_time, ear = 'right')
					new_right_audiogram.save()
					update_list = []

					a250Hz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(250)
					if a250Hz:
						new_right_audiogram.a250Hz = a250Hz
						update_list.append('a250Hz')
					a500Hz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(500)
					if a500Hz:
						new_right_audiogram.a500Hz = a500Hz
						update_list.append('a500Hz')
					a1kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(1000)
					if a1kHz:
						new_right_audiogram.a1kHz = a1kHz
						update_list.append('a1kHz')
					a2kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(2000)
					if a2kHz:
						new_right_audiogram.a2kHz = a2kHz
						update_list.append('a2kHz')
					a4kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(4000)
					if a4kHz:
						new_right_audiogram.a4kHz = a4kHz
						update_list.append('a4kHz')
					a8kHz = noach_patients[patient.noachID]['last_audiogram']['results']['AirConductorRight'].get(8000)
					if a8kHz:
						new_right_audiogram.a8kHz = a8kHz
						update_list.append('a8kHz')

					if noach_patients[patient.noachID]['last_audiogram']['results'].get('BoneConductorRight'):
						b250Hz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(250)
						if b250Hz:
							new_right_audiogram.b250Hz = b250Hz
							update_list.append('b250Hz')
						b500Hz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(500)
						if b500Hz:
							new_right_audiogram.b500Hz = b500Hz
							update_list.append('b500Hz')
						b1kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(1000)
						if b1kHz:
							new_right_audiogram.b1kHz = b1kHz
							update_list.append('b1kHz')
						b2kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(2000)
						if b2kHz:
							new_right_audiogram.b2kHz = b2kHz
							update_list.append('b2kHz')
						b4kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(4000)
						if b4kHz:
							new_right_audiogram.b4kHz = b4kHz
							update_list.append('b4kHz')
						b8kHz = noach_patients[patient.noachID]['last_audiogram']['results']['BoneConductorRight'].get(8000)
						if b8kHz:
							new_right_audiogram.b8kHz = b8kHz
							update_list.append('b8kHz')



					new_right_audiogram.save(update_fields=update_list)
					# print 'new_right_audiogram.a1kHz: ', new_right_audiogram.a1kHz
			remove_list.append(patient.noachID)
			continue

		for noach_patient in noach_patients.values():
		
			if patient.first_name == noach_patient['first_name']\
			and patient.last_name == noach_patient['last_name']\
			and str(patient.date_of_birth) == str(noach_patient.get('dateofbirth')):
				# this means that patient was added to crm and now the same patient is imported from noach,

				# add noach create date and noach id
				patient.noachcreatedate = noach_patient['noachcreatedate']
				patient.noachID = noach_patient['noahpatientid']
				update_list = ['noachID', 'noachcreatedate']
				phone_from_noach = noach_patient.get('mobilephone') or noach_patient.get('homephone') or noach_patient.get('workphone')
				if phone_from_noach:
					try:
						phone_from_noach = int(phone_from_noach)
						patient.phone_no = phone_from_noach
						update_list.append('phone_no')
					except:
						note = 'nr tel: %s' % phone_from_noach
						new_note = NewInfo(patient = new_patient, note = note)
						new_note.save()						

					
				patient.save(update_fields=update_list)

				phone2 = noach_patient.get('homephone') or noach_patient.get('workphone')
				if phone2:
					print 'p2', phone2
					note = 'Dodatkowy nr tel: %s' % phone2
					new_note = NewInfo(patient = patient, note = note)
					new_note.save()
				# if audiograms in noach are newer - replace current audiograms
				if noach_patient.get('last_audiogram'):

					if noach_patient['last_audiogram']['results'].get('AirConductorLeft'):
						time_of_test = datetime.datetime.strptime(noach_patient['last_audiogram']['time_of_test'], '%Y-%m-%dT%H:%M:%S')
						print 'tot L', time_of_test
						new_left_audiogram = Audiogram(patient = patient,
														ear = 'left',
														time_of_test = time_of_test)
														
						new_left_audiogram.save()
						update_list = []

						a250Hz = noach_patient['last_audiogram']['results']['AirConductorLeft'].get(250)
						if a250Hz:
							new_left_audiogram.a250Hz = a250Hz
							update_list.append('a250Hz')
						a500Hz = noach_patient['last_audiogram']['results']['AirConductorLeft'].get(500)
						if a500Hz:
							new_left_audiogram.a500Hz = a500Hz
							update_list.append('a500Hz')
						a1kHz = noach_patient['last_audiogram']['results']['AirConductorLeft'].get(1000)
						if a1kHz:
							new_left_audiogram.a1kHz = a1kHz
							update_list.append('a1kHz')
						a2kHz = noach_patient['last_audiogram']['results']['AirConductorLeft'].get(2000)
						if a2kHz:
							new_left_audiogram.a2kHz = a2kHz
							update_list.append('a2kHz')
						a4kHz = noach_patient['last_audiogram']['results']['AirConductorLeft'].get(4000)
						if a4kHz:
							new_left_audiogram.a4kHz = a4kHz
							update_list.append('a4kHz')
						a8kHz = noach_patient['last_audiogram']['results']['AirConductorLeft'].get(8000)
						if a8kHz:
							new_left_audiogram.a8kHz = a8kHz
							update_list.append('a8kHz')

						if noach_patient['last_audiogram']['results'].get('BoneConductorLeft'):
							b250Hz = noach_patient['last_audiogram']['results']['BoneConductorLeft'].get(250)
							if b250Hz:
								new_left_audiogram.b250Hz = b250Hz
								update_list.append('b250Hz')
							b500Hz = noach_patient['last_audiogram']['results']['BoneConductorLeft'].get(500)
							if b500Hz:
								new_left_audiogram.b500Hz = b500Hz
								update_list.append('b500Hz')
							b1kHz = noach_patient['last_audiogram']['results']['BoneConductorLeft'].get(1000)
							if b1kHz:
								new_left_audiogram.b1kHz = b1kHz
								update_list.append('b1kHz')
							b2kHz = noach_patient['last_audiogram']['results']['BoneConductorLeft'].get(2000)
							if b2kHz:
								new_left_audiogram.b2kHz = b2kHz
								update_list.append('b2kHz')
							b4kHz = noach_patient['last_audiogram']['results']['BoneConductorLeft'].get(4000)
							if b4kHz:
								new_left_audiogram.b4kHz = b4kHz
								update_list.append('b4kHz')
							b8kHz = noach_patient['last_audiogram']['results']['BoneConductorLeft'].get(8000)
							if b8kHz:
								new_left_audiogram.b8kHz = b8kHz
								update_list.append('b8kHz')

						new_left_audiogram.save(update_fields=update_list)


					if noach_patient['last_audiogram']['results'].get('AirConductorRight'):
						time_of_test = datetime.datetime.strptime(noach_patient['last_audiogram']['time_of_test'], '%Y-%m-%dT%H:%M:%S')
						print 'tot R', time_of_test							
						new_right_audiogram = Audiogram(patient = patient,
														ear = 'right',
														time_of_test = time_of_test)
						new_right_audiogram.save()
						update_list = []

						a250Hz = noach_patient['last_audiogram']['results']['AirConductorRight'].get(250)
						if a250Hz:
							new_right_audiogram.a250Hz = a250Hz
							update_list.append('a250Hz')
						a500Hz = noach_patient['last_audiogram']['results']['AirConductorRight'].get(500)
						if a500Hz:
							new_right_audiogram.a500Hz = a500Hz
							update_list.append('a500Hz')
						a1kHz = noach_patient['last_audiogram']['results']['AirConductorRight'].get(1000)
						if a1kHz:
							new_right_audiogram.a1kHz = a1kHz
							update_list.append('a1kHz')
						a2kHz = noach_patient['last_audiogram']['results']['AirConductorRight'].get(2000)
						if a2kHz:
							new_right_audiogram.a2kHz = a2kHz
							update_list.append('a2kHz')
						a4kHz = noach_patient['last_audiogram']['results']['AirConductorRight'].get(4000)
						if a4kHz:
							new_right_audiogram.a4kHz = a4kHz
							update_list.append('a4kHz')
						a8kHz = noach_patient['last_audiogram']['results']['AirConductorRight'].get(8000)
						if a8kHz:
							new_right_audiogram.a8kHz = a8kHz
							update_list.append('a8kHz')

						if noach_patient['last_audiogram']['results'].get('BoneConductorRight'):
							b250Hz = noach_patient['last_audiogram']['results']['BoneConductorRight'].get(250)
							if b250Hz:
								new_right_audiogram.b250Hz = b250Hz
								update_list.append('b250Hz')
							b500Hz = noach_patient['last_audiogram']['results']['BoneConductorRight'].get(500)
							if b500Hz:
								new_right_audiogram.b500Hz = b500Hz
								update_list.append('b500Hz')
							b1kHz = noach_patient['last_audiogram']['results']['BoneConductorRight'].get(1000)
							if b1kHz:
								new_right_audiogram.b1kHz = b1kHz
								update_list.append('b1kHz')
							b2kHz = noach_patient['last_audiogram']['results']['BoneConductorRight'].get(2000)
							if b2kHz:
								new_right_audiogram.b2kHz = b2kHz
								update_list.append('b2kHz')
							b4kHz = noach_patient['last_audiogram']['results']['BoneConductorRight'].get(4000)
							if b4kHz:
								new_right_audiogram.b4kHz = b4kHz
								update_list.append('b4kHz')
							b8kHz = noach_patient['last_audiogram']['results']['BoneConductorRight'].get(8000)
							if b8kHz:
								new_right_audiogram.b8kHz = b8kHz
								update_list.append('b8kHz')

						new_right_audiogram.save(update_fields=update_list)
				remove_list.append(noach_patient['noahpatientid'])
				break
			else:
	 			# add new patient to to_be_created list
	 			if noach_patient not in to_be_created: to_be_created.append(noach_patient)

	print 'len before', len(to_be_created)
	
	# remove patients that were updated to prevent duplicating them
	
	to_be_created2 = to_be_created[:]
	
	# print 'remove_list: ', remove_list
	# o = [i['noahpatientid'] for i in to_be_created]
	# print 'to be c: ', o

	for i in to_be_created2:
		if i['noahpatientid'] in remove_list:
			to_be_created.remove(i)

	# o = [i['noahpatientid'] for i in to_be_created]
	# print 'to be c: ', o
	
	
	# create new patients
	for noach_patient in to_be_created:
		new_patient = Patient(first_name = noach_patient['first_name'],
							last_name = noach_patient['last_name'],
							date_of_birth = noach_patient.get('dateofbirth'),
							noachcreatedate = noach_patient['noachcreatedate'],
							noachID = noach_patient['noahpatientid'])
		new_patient.save()
		phone_from_noach = noach_patient.get('mobilephone') or noach_patient.get('homephone') or noach_patient.get('workphone')
		if phone_from_noach:
			try:
				phone_from_noach = int(phone_from_noach)
				new_patient(phone_no = phone_from_noach)
				new_patient.save()
			except:
				note = 'nr tel: %s' % phone_from_noach
				new_note = NewInfo(patient = new_patient, note = note)
				new_note.save()						

		phone2 = noach_patient.get('homephone') or noach_patient.get('workphone')
		if phone2:
			note = 'Dodatkowy nr tel: %s' % phone2
			new_note = NewInfo(patient = new_patient, note = note)
			new_note.save()

		if noach_patient.get('last_audiogram'):

			if noach_patient['last_audiogram']['results'].get('AirConductorLeft'):
				time_of_test = datetime.datetime.strptime(noach_patient['last_audiogram']['time_of_test'], '%Y-%m-%dT%H:%M:%S')
				print 'tot L', time_of_test
				new_left_audiogram = Audiogram(patient = new_patient,
												ear = 'left',
												time_of_test = time_of_test)
												
				new_left_audiogram.save()
				update_list = []

				a250Hz = noach_patient['last_audiogram']['results']['AirConductorLeft'].get(250)
				if a250Hz:
					new_left_audiogram.a250Hz = a250Hz
					update_list.append('a250Hz')
				a500Hz = noach_patient['last_audiogram']['results']['AirConductorLeft'].get(500)
				if a500Hz:
					new_left_audiogram.a500Hz = a500Hz
					update_list.append('a500Hz')
				a1kHz = noach_patient['last_audiogram']['results']['AirConductorLeft'].get(1000)
				if a1kHz:
					new_left_audiogram.a1kHz = a1kHz
					update_list.append('a1kHz')
				a2kHz = noach_patient['last_audiogram']['results']['AirConductorLeft'].get(2000)
				if a2kHz:
					new_left_audiogram.a2kHz = a2kHz
					update_list.append('a2kHz')
				a4kHz = noach_patient['last_audiogram']['results']['AirConductorLeft'].get(4000)
				if a4kHz:
					new_left_audiogram.a4kHz = a4kHz
					update_list.append('a4kHz')
				a8kHz = noach_patient['last_audiogram']['results']['AirConductorLeft'].get(8000)
				if a8kHz:
					new_left_audiogram.a8kHz = a8kHz
					update_list.append('a8kHz')

				if noach_patient['last_audiogram']['results'].get('BoneConductorLeft'):
					b250Hz = noach_patient['last_audiogram']['results']['BoneConductorLeft'].get(250)
					if b250Hz:
						new_left_audiogram.b250Hz = b250Hz
						update_list.append('b250Hz')
					b500Hz = noach_patient['last_audiogram']['results']['BoneConductorLeft'].get(500)
					if b500Hz:
						new_left_audiogram.b500Hz = b500Hz
						update_list.append('b500Hz')
					b1kHz = noach_patient['last_audiogram']['results']['BoneConductorLeft'].get(1000)
					if b1kHz:
						new_left_audiogram.b1kHz = b1kHz
						update_list.append('b1kHz')
					b2kHz = noach_patient['last_audiogram']['results']['BoneConductorLeft'].get(2000)
					if b2kHz:
						new_left_audiogram.b2kHz = b2kHz
						update_list.append('b2kHz')
					b4kHz = noach_patient['last_audiogram']['results']['BoneConductorLeft'].get(4000)
					if b4kHz:
						new_left_audiogram.b4kHz = b4kHz
						update_list.append('b4kHz')
					b8kHz = noach_patient['last_audiogram']['results']['BoneConductorLeft'].get(8000)
					if b8kHz:
						new_left_audiogram.b8kHz = b8kHz
						update_list.append('b8kHz')

				new_left_audiogram.save(update_fields=update_list)


			if noach_patient['last_audiogram']['results'].get('AirConductorRight'):
				time_of_test = datetime.datetime.strptime(noach_patient['last_audiogram']['time_of_test'], '%Y-%m-%dT%H:%M:%S')
				print 'tot R', time_of_test							
				new_right_audiogram = Audiogram(patient = new_patient,
												ear = 'right',
												time_of_test = time_of_test)
				new_right_audiogram.save()
				update_list = []

				a250Hz = noach_patient['last_audiogram']['results']['AirConductorRight'].get(250)
				if a250Hz:
					new_right_audiogram.a250Hz = a250Hz
					update_list.append('a250Hz')
				a500Hz = noach_patient['last_audiogram']['results']['AirConductorRight'].get(500)
				if a500Hz:
					new_right_audiogram.a500Hz = a500Hz
					update_list.append('a500Hz')
				a1kHz = noach_patient['last_audiogram']['results']['AirConductorRight'].get(1000)
				if a1kHz:
					new_right_audiogram.a1kHz = a1kHz
					update_list.append('a1kHz')
				a2kHz = noach_patient['last_audiogram']['results']['AirConductorRight'].get(2000)
				if a2kHz:
					new_right_audiogram.a2kHz = a2kHz
					update_list.append('a2kHz')
				a4kHz = noach_patient['last_audiogram']['results']['AirConductorRight'].get(4000)
				if a4kHz:
					new_right_audiogram.a4kHz = a4kHz
					update_list.append('a4kHz')
				a8kHz = noach_patient['last_audiogram']['results']['AirConductorRight'].get(8000)
				if a8kHz:
					new_right_audiogram.a8kHz = a8kHz
					update_list.append('a8kHz')

				if noach_patient['last_audiogram']['results'].get('BoneConductorRight'):
					b250Hz = noach_patient['last_audiogram']['results']['BoneConductorRight'].get(250)
					if b250Hz:
						new_right_audiogram.b250Hz = b250Hz
						update_list.append('b250Hz')
					b500Hz = noach_patient['last_audiogram']['results']['BoneConductorRight'].get(500)
					if b500Hz:
						new_right_audiogram.b500Hz = b500Hz
						update_list.append('b500Hz')
					b1kHz = noach_patient['last_audiogram']['results']['BoneConductorRight'].get(1000)
					if b1kHz:
						new_right_audiogram.b1kHz = b1kHz
						update_list.append('b1kHz')
					b2kHz = noach_patient['last_audiogram']['results']['BoneConductorRight'].get(2000)
					if b2kHz:
						new_right_audiogram.b2kHz = b2kHz
						update_list.append('b2kHz')
					b4kHz = noach_patient['last_audiogram']['results']['BoneConductorRight'].get(4000)
					if b4kHz:
						new_right_audiogram.b4kHz = b4kHz
						update_list.append('b4kHz')
					b8kHz = noach_patient['last_audiogram']['results']['BoneConductorRight'].get(8000)
					if b8kHz:
						new_right_audiogram.b8kHz = b8kHz
						update_list.append('b8kHz')

				new_right_audiogram.save(update_fields=update_list)
			
	messages.success(request, "Pacjenci zaimportowani")
	return redirect('crm:index')