# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.encoding import python_2_unicode_compatible
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse, HttpResponseRedirect, Http404
from .forms import PatientForm
from .models import (Patient, Audiogram, NewInfo, Hearing_Aid, NFZ_Confirmed,
                     NFZ_New, PCPR_Estimate, HA_Invoice, Audiogram, Reminder)
from .noach_file_handler import noach_file_handler
from django.core.urlresolvers import reverse
from django.db.models.functions import Lower
from django.db.models import Q
import json
today = datetime.date.today()
ears = ['left', 'right']


@login_required
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


@login_required
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
	
	# search by dates of NFZ new - only active not prevoius
	if request.GET.get('s_nfz_new_date') or request.GET.get('e_nfz_new_date'):
		nfz_start = request.GET.get('s_nfz_new_date') or '1990-01-01'
		nfz_end = request.GET.get(
			'e_nfz_new_date') or str(datetime.datetime.today().date())
		all_such_nfz = NFZ_New.objects.filter(
			date__range=[nfz_start, nfz_end], in_progress=True)
		patient_list = patient_list & patients_from_ha(all_such_nfz)

	# search by dates of NFZ confirmed - only active not prevoius
	if request.GET.get('s_nfz_date') or request.GET.get('e_nfz_date'):
		nfz_start = request.GET.get('s_nfz_date') or '1990-01-01'
		nfz_end = request.GET.get(
			'e_nfz_date') or str(datetime.datetime.today().date())
		all_such_nfz = NFZ_Confirmed.objects.filter(
			date__range=[nfz_start, nfz_end], in_progress=True)
		patient_list = patient_list & patients_from_ha(all_such_nfz)

	# search by dates of pcpr estimates - only active not prevoius
	if request.GET.get('s_pcpr_date') or request.GET.get('e_pcpr_date'):
		pcpr_start = request.GET.get('s_pcpr_date') or '1990-01-01'
		pcpr_end = request.GET.get(
			'e_pcpr_date') or str(datetime.datetime.today().date())
		all_such_pcpr = PCPR_Estimate.objects.filter(
			date__range=[pcpr_start, pcpr_end], in_progress=True)
		patient_list = patient_list & patients_from_ha(all_such_pcpr)

	# search by dates of invoice - only active not prevoius
	if request.GET.get('s_invoice_date') or request.GET.get('e_invoice_date'):
		invoice_start = request.GET.get('s_invoice_date') or '1990-01-01'
		invoice_end = request.GET.get(
			'e_invoice_date') or str(datetime.datetime.today().date())
		all_such_invoice = HA_Invoice.objects.filter(
			date__range=[invoice_start, invoice_end], in_progress=True)
		patient_list = patient_list & patients_from_ha(all_such_invoice)


	paginator = Paginator(patient_list, 50)  # Show X patients per page

	page = request.GET.get('page')
	try:
		patient_list = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page.
		patient_list = paginator.page(1)
	except EmptyPage:
		# If page is out of range (e.g. 9999), deliver last page of results.
		patient_list = paginator.page(paginator.num_pages)

	context = {	'patient_list': patient_list,
				'locations': Patient.locations,
				'ha_list': Hearing_Aid.ha_list}
	return render(request, 'crm/advanced_search.html', context)


@login_required
def create(request):
	ha_list = Hearing_Aid.ha_list
	locations = Patient.locations
	audiometrists = User.objects.all()
	context = {	'ha_list': ha_list, 'ears': ears, 'locations': locations}
	return render(request, 'crm/create.html', context)


@login_required
def edit(request, patient_id):
	# displays form for upadating patient details
	patient = get_object_or_404(Patient, pk=patient_id)
	right_hearing_aid = patient.hearing_aid_set.filter(ear="right").last()
	left_hearing_aid = patient.hearing_aid_set.filter(ear="left").last()
	nfz_new_left_qs = patient.nfz_new_set.filter(side='left')
	nfz_new_right_qs = patient.nfz_new_set.filter(side='right')
	nfz_confirmed_left_qs = patient.nfz_confirmed_set.filter(side='left')
	nfz_confirmed_right_qs = patient.nfz_confirmed_set.filter(side='right')
	left_PCPR_qs = PCPR_Estimate.objects.filter(patient=patient, ear='left')
	right_PCPR_qs = PCPR_Estimate.objects.filter(patient=patient, ear='right')
	left_invoice_qs = HA_Invoice.objects.filter(patient=patient, ear='left')
	right_invoice_qs = HA_Invoice.objects.filter(patient=patient, ear='right')
	audiometrists = User.objects.all()

	def last_and_previous(queryset):
		'''returns last obj or None of a qs as "last" and
		all but last items of such qs or None'''
		result = {'last': queryset.last(), 'previous': None}
		if queryset:
			if queryset.last().in_progress == False:
				result['last'] = None
				result['previous'] = queryset
			if len(queryset) > 1 and queryset.last().in_progress:
				result['previous'] = queryset.order_by('-id')[1:]
		return result

	context = {
			'patient': patient,
			'ha_list': Hearing_Aid.ha_list,
			'ears': ears,
            'audiometrists': audiometrists,
			'patient_notes': patient.newinfo_set.order_by('-timestamp'),
			'right_hearing_aid': right_hearing_aid,
			'left_hearing_aid': left_hearing_aid,
			'left_NFZ_new_all': last_and_previous(nfz_new_left_qs)['previous'],
			'left_NFZ_new': last_and_previous(nfz_new_left_qs)['last'],
			'right_NFZ_new_all': last_and_previous(nfz_new_right_qs)['previous'],
			'right_NFZ_new': last_and_previous(nfz_new_right_qs)['last'],
			'left_NFZ_confirmed_all': last_and_previous(nfz_confirmed_left_qs)['previous'],
			'left_NFZ_confirmed': last_and_previous(nfz_confirmed_left_qs)['last'],
			'right_NFZ_confirmed_all': last_and_previous(nfz_confirmed_right_qs)['previous'],
			'right_NFZ_confirmed': last_and_previous(nfz_confirmed_right_qs)['last'],
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


@login_required
def store(request):
	# for adding new patients to database
	patient = Patient(first_name=request.POST['fname'].capitalize(),
        last_name=request.POST['lname'].capitalize(),
		date_of_birth=request.POST['bday'],
		phone_no=request.POST['usrtel'],
		audiometrist = request.user,
		location = request.POST['location'],
        notes = request.POST.get('note')
		)
	patient.save()

	for ear in ears:
    		# add hearing aid
		if request.POST.get(ear + '_ha'):
			ha = request.POST[ear + '_ha']
			ha_make, ha_family, ha_model = ha.split('_')
			hearing_aid = Hearing_Aid(patient=patient, ha_make=ha_make, ha_family=ha_family, ha_model=ha_model, ear=ear)
			hearing_aid.save()
			if request.POST.get(ear + '_purchase_date'):
				hearing_aid.purchase_date = request.POST[ear + '_purchase_date']
				hearing_aid.save()

		if request.POST.get(ear + '_other_ha'):
			ha = request.POST[ear + '_other_ha']
			if ' ' in ha:
				ha = ha.split(' ', 1)
				ha_make, ha_family, ha_model = ha[0], ha[1].replace(' ', '_'), 'inny'
			else:
				ha_make, ha_family, ha_model = ha, 'inny', 'inny'
			hearing_aid = Hearing_Aid(patient=patient, ha_make=ha_make, ha_family=ha_family, ha_model=ha_model, ear=ear)
			hearing_aid.save()
			if request.POST.get(ear + '_purchase_date'):
				hearing_aid.purchase_date = request.POST[ear + '_purchase_date']
				hearing_aid.save()

			# add NFZ_new
		if request.POST.get(ear + '_NFZ_new'):
			nfz_new = NFZ_New.objects.create(
				patient=patient, date=request.POST[ear + '_NFZ_new'], side=ear)
			Reminder.objects.create(nfz_new=nfz_new)

			# add NFZ_confirmed
		if request.POST.get(ear + '_NFZ_confirmed_date'):
			nfz_confirmed = NFZ_Confirmed(patient=patient, date=request.POST[ear + '_NFZ_confirmed_date'], side=ear)
			nfz_confirmed.save()
			Reminder.objects.create(nfz_confirmed=nfz_confirmed)

			# add PCPR_Estimate
		if request.POST.get(ear + '_pcpr_ha'):
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
			Reminder.objects.create(pcpr=pcpr_estimate)

	messages.success(request, "Pomyślnie utworzono")
	return HttpResponseRedirect(reverse('crm:edit', args=(patient.id,)))


@login_required
def updating(request, patient_id):
	# for updating existing patients in database
	patient = get_object_or_404(Patient, pk=patient_id)
	patient.first_name = request.POST['fname'].capitalize()
	patient.last_name = request.POST['lname'].capitalize()
	patient.phone_no=request.POST['usrtel']
	patient.location = request.POST['location']
	patient.notes = request.POST['summary_note']
	update_list = ['first_name', 'last_name', 'phone_no', 'location', 'notes']
	if request.POST.get('bday'):
		patient.date_of_birth=request.POST['bday']
		update_list.append('date_of_birth')
	patient.save(update_fields=update_list)

	audiometrist = request.user
	if request.POST.get('new_note'):
		new_info = NewInfo(	patient=patient,
							note=request.POST['new_note'],
                    		audiometrist=audiometrist)
		new_info.save()

	new_action = []
	for ear in ears:
		pl_side = 'lewy' if ear == 'left' else 'prawy'
			# adding hearing aid to patient
		if request.POST.get(ear + '_ha'):
			ha = request.POST[ear + '_ha']
			ha_make, ha_family, ha_model = ha.split('_')
			hearing_aid = Hearing_Aid(patient=patient,
									ha_make=ha_make,
									ha_family=ha_family,
									ha_model=ha_model,
									ear=ear)
			hearing_aid.save()
			new_action.append('Dodano ' + pl_side + ' aparat ' + 
							hearing_aid.ha_make + ' ' + hearing_aid.ha_family + 
							' ' + hearing_aid.ha_model + '.')
			if request.POST.get(ear + '_purchase_date'):
				hearing_aid.purchase_date = request.POST[ear + '_purchase_date']
				hearing_aid.save()
			# notofies that patient has ha bought in another shop
			if request.POST.get(ear + '_ha_other'):
				hearing_aid.our = False
				hearing_aid.save()
				
			# adding hearing aid with a custom name to patient
		if request.POST.get(ear + '_other_ha'):
			ha = request.POST[ear + '_other_ha']
			if ' ' in ha:
				ha = ha.split(' ', 1)
				ha_make, ha_family, ha_model = ha[0], ha[1].replace(' ', '_'), 'inny'
			else:
				ha_make, ha_family, ha_model = ha, 'inny', 'inny'
			hearing_aid = Hearing_Aid(patient=patient, ha_make=ha_make, ha_family=ha_family, ha_model=ha_model, ear=ear)
			hearing_aid.save()
			new_action.append('Dodano ' + pl_side + ' aparat ' +
                            hearing_aid.ha_make + ' ' + hearing_aid.ha_family +
                            ' ' + hearing_aid.ha_model + '.')
			if request.POST.get(ear + '_purchase_date'):
				hearing_aid.purchase_date = request.POST[ear + '_purchase_date']
				hearing_aid.save()
			# notofies that patient has ha bought in another shop
			if request.POST.get(ear + '_ha_other'):
				hearing_aid.our = False
				hearing_aid.save()

			# adding NFZ_new to patient
			# previous NFZ if present are set to inactive
		if request.POST.get('new_NFZ_' + ear):
			nfz_new = NFZ_New.objects.filter(
                            patient=patient, side=ear, in_progress=True)
			if nfz_new:
				nfz_new.update(in_progress=False)
			new_nfz_new = NFZ_New.objects.create(
				patient=patient, side=ear, date=request.POST['new_NFZ_' + ear])
			new_action.append('Dodano niepotwierdzony ' + pl_side + ' wniosek ' +
                            'z datą ' + request.POST['new_NFZ_' + ear] + '.')
			Reminder.objects.create(nfz_new=new_nfz_new)

			# remove NFZ_new from currently active
		if request.POST.get('nfz_new_' + ear + '_remove'):
			last_in_progress = NFZ_New.objects.filter(
				patient=patient, side=ear, in_progress=True).last()
			last_in_progress.in_progress = False
			last_in_progress.save()
			new_action.append('Usunięto ' + pl_side + ' niepotwierdzony wniosek ' +
                            'z datą ' + str(last_in_progress.date) + '.')
			reminder = Reminder.objects.get(nfz_new=last_in_progress)
			reminder.active = False
			reminder.save()

			# adding NFZ_confirmed to patient
			# previous NFZ if present are set to inactive
		if request.POST.get('NFZ_' + ear):
			nfz_confirmed = NFZ_Confirmed.objects.filter(
					patient=patient, side=ear, in_progress=True)
			if nfz_confirmed:
				nfz_confirmed.update(in_progress=False)
			new_nfz_confirmed = NFZ_Confirmed.objects.create(
				patient=patient, side=ear, date=request.POST['NFZ_' + ear])
			new_action.append('Dodano potwierdzony ' + pl_side + ' wniosek ' +
                            'z datą ' + request.POST['NFZ_' + ear] + '.')
			Reminder.objects.create(nfz_confirmed=new_nfz_confirmed)


			# remove NFZ_confirmed from currently active
		if request.POST.get('nfz_' + ear + '_remove'):
			last_in_progress = NFZ_Confirmed.objects.filter(patient=patient, side=ear, in_progress=True).last()
			last_in_progress.in_progress = False
			last_in_progress.save()
			new_action.append('Usunięto ' + pl_side + ' wniosek ' +
							'z datą ' + str(last_in_progress.date) + '.')
			reminder = Reminder.objects.get(nfz_confirmed=last_in_progress)
			reminder.active = False
			reminder.save()

			# adding PCPR_Estimate
		if request.POST.get(ear + '_pcpr_ha'):
			ha = request.POST[ear + '_pcpr_ha']
			ha_make, ha_family, ha_model = ha.split('_')
			date = request.POST.get(ear + '_PCPR_date') or str(today)
			pcpr_estimate = PCPR_Estimate(
				patient=patient,
				ha_make=ha_make,
				ha_family=ha_family,
				ha_model=ha_model,
				ear=ear,
				date=date)
			pcpr_estimate.save()
			new_action.append('Dodano ' + pl_side + ' kosztorys ' + 'na ' +
				pcpr_estimate.ha_make + ' ' + pcpr_estimate.ha_family + ' ' +
                pcpr_estimate.ha_model + ', ' +
				'z datą ' + date + '.')
			Reminder.objects.create(pcpr=pcpr_estimate)

			# remove PCPR_Estimate from currently active
		if request.POST.get('pcpr_' + ear + '_remove'):
			last_pcpr_in_progress = PCPR_Estimate.objects.filter(
				patient=patient, ear=ear, in_progress=True).last()
			last_pcpr_in_progress.in_progress = False
			last_pcpr_in_progress.save()
			new_action.append('Usunięto ' + pl_side + ' kosztorys na ' +
				last_pcpr_in_progress.ha_make + ' ' + 
				last_pcpr_in_progress.ha_family + ' ' +
				last_pcpr_in_progress.ha_model + ', ' +
                'z datą ' + str(last_pcpr_in_progress.date) + '.')
			reminder = Reminder.objects.get(pcpr=last_pcpr_in_progress)
			reminder.active = False
			reminder.save()

		# invoice procedure
		if request.POST.get(ear + '_invoice_ha'):
			ha = request.POST[ear + '_invoice_ha']
			ha_make, ha_family, ha_model = ha.split('_')
			date = request.POST.get(ear + '_invoice_date') or str(today)
			invoice = HA_Invoice(
				patient=patient,
				ha_make=ha_make,
				ha_family=ha_family,
				ha_model=ha_model,
				ear=ear,
				date=date,)
			invoice.save()
			pl_side2 = 'lewą' if ear=='left' else 'prawą'
			new_action.append('Dodano ' + pl_side2 + ' fakturę ' + 'na ' +
                            invoice.ha_make + ' ' + invoice.ha_family + ' ' +
                            invoice.ha_model + ', ' +
							'z datą ' + date + '.')
			Reminder.objects.create(invoice=invoice)

		# remove invoice
		if request.POST.get(ear + '_invoice_remove'):
			last_invoice_in_progress = HA_Invoice.objects.filter(
				patient=patient, ear=ear, in_progress=True).last()
			last_invoice_in_progress.in_progress = False
			last_invoice_in_progress.save()
			pl_side2 = 'lewą' if ear == 'left' else 'prawą'
			new_action.append('Usunięto ' + pl_side2 + ' fakturę na ' +
                            last_invoice_in_progress.ha_make + ' ' +
                            last_invoice_in_progress.ha_family + ' ' +
                            last_invoice_in_progress.ha_model + ', ' +
                            'z datą ' + str(last_invoice_in_progress.date) + '.')
			reminder = Reminder.objects.get(invoice=last_invoice_in_progress)
			reminder.active = False
			reminder.save()

		# collection procedure
		if request.POST.get(ear + '_collection_confirm'):
			invoiced_ha = HA_Invoice.objects.filter(patient=patient, ear=ear).last()
			date = request.POST.get(ear + '_collection_date') or str(today)
			new_ha = Hearing_Aid.objects.create(
				patient=patient,
				ha_make = invoiced_ha.ha_make,
				ha_family = invoiced_ha.ha_family,
				ha_model = invoiced_ha.ha_model,
				purchase_date=date,
				ear=ear)

			# clear Invoice, PCPR_Estimate and NFZ_Confirmed and NFZ_New for this HA
			invoiced_ha.in_progress = False
			invoiced_ha.save()
			reminder = Reminder.objects.get(invoice=invoiced_ha)
			reminder.active = False
			reminder.save()
			pcpr_estimate = PCPR_Estimate.objects.filter(patient=patient, ear=ear).last()
			if pcpr_estimate:
				pcpr_estimate.in_progress = False
				pcpr_estimate.save()
				reminder = Reminder.objects.get(pcpr=pcpr_estimate)
				reminder.active = False
				reminder.save()
			nfz_new = NFZ_New.objects.filter(patient=patient, side=ear).last()
			if nfz_new:
				nfz_new.in_progress = False
				nfz_new.save()
				reminder = Reminder.objects.get(nfz_new=nfz_new)
				reminder.active = False
				reminder.save()
			nfz_confirmed = NFZ_Confirmed.objects.filter(patient=patient, side=ear).last()
			if nfz_confirmed:
				nfz_confirmed.in_progress = False
				nfz_confirmed.save()
				reminder = Reminder.objects.get(nfz_confirmed=nfz_confirmed)
				reminder.active = False
				reminder.save()

			# create new info instance to show in history of actions
			new_action.append('Odebrano ' + pl_side + ' aparat ' +
                            invoiced_ha.ha_make + ' ' +
                            invoiced_ha.ha_family + ' ' +
                            invoiced_ha.ha_model + ', ' +
				'z datą ' + str(invoiced_ha.date) + '.')

			# add reminder
			Reminder.objects.create(
				ha=new_ha, activation_date=today+datetime.timedelta(days=365))

			
	if request.POST.get('remove_audiogram') == 'remove':
		current_left_audiogram = patient.audiogram_set.filter(ear = 'left').order_by('-time_of_test').last()
		current_right_audiogram = patient.audiogram_set.filter(ear = 'right').order_by('-time_of_test').last()
		if current_left_audiogram: current_left_audiogram.delete()
		if current_right_audiogram: current_right_audiogram.delete()

	if new_action:
		NewInfo.objects.create(	patient=patient,
                          		note=' '.join(new_action),
								audiometrist=audiometrist)
	messages.success(request, "Zaktualizowano dane")

	return HttpResponseRedirect(reverse('crm:edit', args=(patient_id,)))


@login_required
def deleteconfirm(request, patient_id):
	patient = get_object_or_404(Patient, pk=patient_id)
	return render(request, 'crm/delete-confirm.html', {'patient': patient})


@login_required
def delete_patient(request, patient_id):
	patient = get_object_or_404(Patient, pk = patient_id)
	patient.delete()
	messages.success(request, "Pacjent %s usunięty" % patient.last_name)
	return redirect('crm:index')

@login_required
def duplicate_check(request):
	if request.GET.get('usrtel'):
		usrtel = request.GET.get('usrtel')
		patient_tel = Patient.objects.filter(phone_no__contains=int(usrtel))
		if patient_tel:
			return HttpResponse('present')
		return HttpResponse('absent')

	lname = request.GET.get('lname')
	fname = request.GET.get('fname')
	bday = request.GET.get('bday')  # string 2018-04-04
	# transform into datetime obj
	bday = datetime.date(*[int(i) for i in bday.split('-')])
	# make fname and lname filter case insensitive by __iexact
	patient_dob = Patient.objects.filter(	last_name__iexact=lname,
											first_name__iexact=fname,
											date_of_birth=bday)
	if patient_dob:
		return HttpResponse('present')
	return HttpResponse('absent')

@login_required
def reminders(request):
	reminders_qs = Reminder.objects.active()
	reminders_list = []
	for i in reminders_qs:
		if i.nfz_new:
			type = ' otrzymano NOWY wniosek NFZ'
			patient = i.nfz_new.patient
		elif i.nfz_confirmed:
			type = ' Otrzymano POTWIERDZONY wniosek NFZ'
			patient = i.nfz_confirmed.patient
		elif i.pcpr:
			type = ' wystawiono kosztorys'
			patient = i.pcpr.patient
		elif i.invoice:
			type = ' wystawiono fakturę'
			patient = i.invoice.patient
		elif i.ha:
			type = ' wydano aparat'
			patient = i.ha.patient
		subject = patient.first_name + ' ' + patient.last_name + ', w dniu: ' + \
			i.timestamp.strftime("%d.%m.%Y") + type
		reminder = {'id': i.id, 'subject': subject}
		reminders_list.append(reminder)

	return render(request, 'crm/reminders.html', {'reminders_list': reminders_list})


@login_required
def reminder(request, reminder_id):
	r = get_object_or_404(Reminder, pk=reminder_id)
	if r.nfz_new:
		type = ' otrzymano NOWY wniosek NFZ'
		patient = r.nfz_new.patient
		more = ' lewy' if r.nfz_new.side == 'left' else ' prawy'
	elif r.nfz_confirmed:
		type = ' otrzymano POTWIERDZONY wniosek NFZ'
		patient = r.nfz_confirmed.patient
		more = ' lewy' if r.nfz_confirmed.side == 'left' else ' prawy'
	elif r.pcpr:
		type = ' wystawiono kosztorys'
		patient = r.pcpr.patient
		side = 'lewy' if r.pcpr.ear=='left' else 'prawy'
		more = ' na: ' + str(r.pcpr) + ' ' + side
	elif r.invoice:
		type = ' wystawiono fakturę'
		patient = r.invoice.patient
		side = 'lewy' if r.invoice.ear == 'left' else 'prawy'
		more = ' na: ' + str(r.invoice) + ' ' + side
	elif r.ha:
		type = ' wydano aparat '
		patient = r.ha.patient
		side = 'lewy' if r.ha.ear == 'left' else 'prawy'
		more = str(r.ha) + ' ' + side
	subject = patient.first_name + ' ' + patient.last_name + ', w dniu: ' + \
		r.timestamp.strftime("%d.%m.%Y") + type + more
	
	context = {'subject': subject, 'patient': patient, 'reminder_id': r.id}
	return render(request, 'crm/reminder.html', context)


@login_required
def inactivate_reminder(request, reminder_id):
	r = get_object_or_404(Reminder, pk=reminder_id)
	r.active = False
	r.save()
	messages.success(request, "Przypomnienie usunięte")
	return redirect('crm:reminders')


@login_required
def invoice_create(request, patient_id):
	patient = get_object_or_404(Patient, pk=patient_id)
	ha_list = Hearing_Aid.ha_list
	js_data = json.dumps(ha_list)

	context = {	'patient': patient,
				'ha_list': ha_list,
             "my_data": js_data}
	return render(request, 'crm/create_invoice.html', context)


@login_required
def invoice_store(request, patient_id):
    	patient = get_object_or_404(Patient, pk=patient_id)
    	pass


@login_required
def invoice_edit(request, invoice_id):
    	pass


@login_required
def invoice_update(request, invoice_id):
    	pass

@login_required
def select_noach_file(request):
	''' enables selecting a noach file from user computer'''
	return render(request, 'crm/select_noach_file.html')


@login_required
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
