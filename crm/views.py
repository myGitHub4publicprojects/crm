# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.encoding import python_2_unicode_compatible
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.forms.formsets import formset_factory
from django.core.serializers.json import DjangoJSONEncoder

from django.http import HttpResponse, HttpResponseRedirect, Http404
from .forms import PatientForm, DeviceForm, InvoiceTypeForm
from .models import (Patient, Audiogram, NewInfo, PCPR_Estimate, Invoice, Pro_Forma_Invoice,
                     Hearing_Aid, Hearing_Aid_Stock, Other_Item, Other_Item_Stock,
                     NFZ_Confirmed, NFZ_New, Reminder_Collection, Reminder_Invoice,
                     Reminder_PCPR, Reminder_NFZ_Confirmed, Reminder_NFZ_New)
from .noach_file_handler import noach_file_handler
from django.core.urlresolvers import reverse
from django.db.models.functions import Lower
from django.db.models import Q
from .other_devices import other_devices
from .utils import get_devices, process_device_formset
import json, decimal
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
		all_ha_make = Hearing_Aid.objects.filter(make=ha_make, current=True)
		patient_list = patient_list & patients_from_ha(all_ha_make)
		# print(patient_list[0].hearing_aid_set.filter(make='Oticon'))
		# print(patient_list[0].hearing_aid_set.filter(current=True))
	# search by ha make family and model
	ha_make_family_model = request.GET.get('ha_make_family_model')
	if ha_make_family_model:
		ha_make, ha_family, ha_model = ha_make_family_model.split('_')
		all_such_has = Hearing_Aid.objects.filter(make=ha_make, model=ha_model, family=ha_family)
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
			'e_pcpr_date') or str(datetime.datetime.now())
		all_such_pcpr = PCPR_Estimate.objects.filter(
			timestamp__range=[pcpr_start, pcpr_end], current=True)
		patient_ids = []
		for p in all_such_pcpr:
			if p.patient.id not in patient_ids:
				patient_ids.append(p.patient.id)
		patients = Patient.objects.filter(id__in=patient_ids)
		patient_list = patient_list & patients


	# search by dates of invoice - only active not prevoius
	if request.GET.get('s_invoice_date') or request.GET.get('e_invoice_date'):
		invoice_start = request.GET.get('s_invoice_date') or '1990-01-01'
		invoice_end = request.GET.get(
			'e_invoice_date') or str(datetime.datetime.now())
		all_such_invoice = Invoice.objects.filter(
			timestamp__range=[invoice_start, invoice_end], current=True)
		patient_ids = []
		for p in all_such_invoice:
			if p.patient.id not in patient_ids:
				patient_ids.append(p.patient.id)
		patients = Patient.objects.filter(id__in=patient_ids)
		patient_list = patient_list & patients

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
				'ha_list': get_ha_list()}
	return render(request, 'crm/advanced_search.html', context)


@login_required
def create(request):
	locations = Patient.locations
	audiometrists = User.objects.all()
	context = {	'ha_list': get_ha_list(), 'ears': ears, 'locations': locations}
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

	PCPR_estimate_all = PCPR_Estimate.objects.filter(
		patient=patient).order_by('timestamp')
	PCPR_estimate_last = PCPR_estimate_all.last()
	if PCPR_estimate_last and PCPR_estimate_last.current != False:
		PCPR_estimate_all = PCPR_estimate_all.exclude(id=PCPR_estimate_last.id)

	Invoice_all = Invoice.objects.filter(
		patient=patient).order_by('timestamp')
	Invoice_last = Invoice_all.last()
	if Invoice_last and Invoice_last.current != False:
		Invoice_all = Invoice_all.exclude(id=Invoice_last.id)

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
			'ha_list': get_ha_list(),
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
			
			'PCPR_estimate_all': PCPR_estimate_all,
			'PCPR_estimate': PCPR_estimate_last,

			'invoice_all': Invoice_all,
			'invoice': Invoice_last,
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
			hearing_aid = Hearing_Aid(
				patient=patient,
				make=ha_make,
				family=ha_family,
				model=ha_model,
				ear=ear,
				pkwiu_code='26.60.14')
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
			hearing_aid = Hearing_Aid(
				patient=patient,
				make=ha_make,
				family=ha_family,
				model=ha_model,
				ear=ear,
				pkwiu_code='26.60.14')
			hearing_aid.save()
			if request.POST.get(ear + '_purchase_date'):
				hearing_aid.purchase_date = request.POST[ear + '_purchase_date']
				hearing_aid.save()

			# add NFZ_new
		if request.POST.get(ear + '_NFZ_new'):
			nfz_new = NFZ_New.objects.create(
				patient=patient, date=request.POST[ear + '_NFZ_new'], side=ear)
			Reminder_NFZ_New.objects.create(nfz_new=nfz_new)

			# add NFZ_confirmed
		if request.POST.get(ear + '_NFZ_confirmed_date'):
			nfz_confirmed = NFZ_Confirmed(patient=patient, date=request.POST[ear + '_NFZ_confirmed_date'], side=ear)
			nfz_confirmed.save()
			Reminder_NFZ_Confirmed.objects.create(nfz_confirmed=nfz_confirmed)

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
	patient.street = request.POST['street']
	patient.house_number = request.POST['house_number']
	patient.apartment_number = request.POST['apartment_number']
	patient.city = request.POST['city']
	patient.zip_code = request.POST['zip_code']

	update_list = ['first_name', 'last_name', 'phone_no', 'location', 'notes',
                'street', 'house_number', 'apartment_number', 'zip_code', 'city']
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
	    	# inactivate previous hearing aids (current=False) if any
			old = Hearing_Aid.objects.filter(patient=patient, ear=ear)
			old.update(current=False)

			ha = request.POST[ear + '_ha']
			ha_make, ha_family, ha_model = ha.split('_')
			hearing_aid = Hearing_Aid.objects.create(patient=patient,
									make=ha_make,
									family=ha_family,
									model=ha_model,
									ear=ear,
									pkwiu_code='26.60.14')
			

			new_action.append('Dodano ' + pl_side + ' aparat ' + 
							hearing_aid.make + ' ' + hearing_aid.family + 
							' ' + hearing_aid.model + '.')
			if request.POST.get(ear + '_purchase_date'):
				hearing_aid.purchase_date = request.POST[ear + '_purchase_date']
				hearing_aid.save()
			# notofies that patient has ha bought in another shop
			if request.POST.get(ear + '_ha_other'):
				hearing_aid.our = False
				hearing_aid.save()
				
			# adding hearing aid with a custom name to patient
		if request.POST.get(ear + '_other_ha'):
    		# inactivate previous hearing aids (current=False) if any
			old = Hearing_Aid.objects.filter(patient=patient, ear=ear)
			old.update(current=False)
			ha = request.POST[ear + '_other_ha']
			if ' ' in ha:
				ha = ha.split(' ', 1)
				ha_make, ha_family, ha_model = ha[0], ha[1].replace(' ', '_'), 'inny'
			else:
				ha_make, ha_family, ha_model = ha, 'inny', 'inny'
			hearing_aid = Hearing_Aid.objects.create(patient=patient,
											make=ha_make, 
											family=ha_family,
											model=ha_model,
											ear=ear,
                                    		pkwiu_code='26.60.14')
			new_action.append('Dodano ' + pl_side + ' aparat ' +
                            hearing_aid.make + ' ' + hearing_aid.family +
                            ' ' + hearing_aid.model + '.')
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
			Reminder_NFZ_New.objects.create(nfz_new=new_nfz_new)

			# remove NFZ_new from currently active
		if request.POST.get('nfz_new_' + ear + '_remove'):
			last_in_progress = NFZ_New.objects.filter(
				patient=patient, side=ear, in_progress=True).last()
			last_in_progress.in_progress = False
			last_in_progress.save()
			new_action.append('Usunięto ' + pl_side + ' niepotwierdzony wniosek ' +
                            'z datą ' + str(last_in_progress.date) + '.')
			reminder = Reminder_NFZ_New.objects.get(nfz_new=last_in_progress)
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

			# Reminders
			# inactivate Reminder.nfz_new if any:
			nfz_new = NFZ_New.objects.filter(
					patient=patient, side=ear, in_progress=True)
			reminder_nfz_new = Reminder_NFZ_New.objects.filter(nfz_new=nfz_new)
			if reminder_nfz_new:
				reminder_nfz_new[0].active = False
				reminder_nfz_new[0].save()

			# add Reminder.nfz_confirmed
			Reminder_NFZ_Confirmed.objects.create(nfz_confirmed=new_nfz_confirmed)


			# remove NFZ_confirmed from currently active
		if request.POST.get('nfz_' + ear + '_remove'):
			last_in_progress = NFZ_Confirmed.objects.filter(patient=patient, side=ear, in_progress=True).last()
			last_in_progress.in_progress = False
			last_in_progress.save()
			new_action.append('Usunięto ' + pl_side + ' wniosek ' +
							'z datą ' + str(last_in_progress.date) + '.')
			reminder = Reminder_NFZ_Confirmed.objects.get(nfz_confirmed=last_in_progress)
			reminder.active = False
			reminder.save()



		
	# collection procedure
	if request.POST.get('collection_confirm'):
		current_invoice = Invoice.objects.get(patient=patient, current=True)
		invoiced_ha = Hearing_Aid.objects.filter(invoice=current_invoice)
		date = request.POST.get('collection_date') or str(today)
		for ha in invoiced_ha:
    		# inactivate previous hearing aids (current=False)
			old = Hearing_Aid.objects.filter(patient=patient, ear=ha.ear)
			old.update(current=False)
			# update hearing aid that are one the invoice
			ha.purchase_date=date
			ha.current = True
			ha.our = True
			ha.save()
			
			# create new info instance to show in history of actions
			pl_side = 'lewy' if ha.ear == 'left' else 'prawy'
			new_action.append('Odebrano ' + pl_side + ' aparat ' +
                    str(ha) + ', z datą ' + str(date) + '.')

			# add reminder
			Reminder_Collection.objects.create(
			ha=ha, activation_date=today+datetime.timedelta(days=365))

		# inactivate Invoice and its reminder
		current_invoice.current = False
		current_invoice.save()
		reminder = Reminder_Invoice.objects.get(invoice=current_invoice)
		reminder.active = False
		reminder.save()

		# inactivate PCPR_Estimate and its reminder 
		pcpr_estimate = PCPR_Estimate.objects.filter(patient=patient, current=True).last()
		if pcpr_estimate:
			pcpr_estimate.current = False
			pcpr_estimate.save()
			reminder = Reminder_PCPR.objects.get(pcpr=pcpr_estimate)
			reminder.active = False
			reminder.save()


		# inactivate NFZ_Confirmed and its reminder
		nfz_confirmed = NFZ_Confirmed.objects.filter(patient=patient, in_progress=True)
		if nfz_confirmed:
			for n in nfz_confirmed:
				n.in_progress = False
				n.save()
				reminder = Reminder_NFZ_Confirmed.objects.get(nfz_confirmed=n)
				reminder.active = False
				reminder.save()

		# inactivate NFZ_New and its reminder
		nfz_new = NFZ_New.objects.filter(
			patient=patient, in_progress=True)
		if nfz_new:
			for n in nfz_new:
				n.in_progress = False
				n.save()
				reminder = Reminder_NFZ_New.objects.get(nfz_new=n)
				reminder.active = False
				reminder.save()
			
		
		# remove PCPR_Estimate from currently active
	if request.POST.get('pcpr_inactivate'):
		last_pcpr = PCPR_Estimate.objects.filter(
			patient=patient).last()
		last_pcpr.current = False
		last_pcpr.save()
		new_action.append('Zdezaktywowano kosztorys z datą ' +
		                  str(last_pcpr.timestamp.date()) + '.')
		reminder = Reminder_PCPR.objects.get(pcpr=last_pcpr)
		reminder.active = False
		reminder.save()


		# remove invoice from currently active
	if request.POST.get('invoice_inactivate'):
		last_invoice = Invoice.objects.filter(
			patient=patient).last()
		last_invoice.current = False
		last_invoice.save()
		new_action.append('Zdezaktywowano fakturę z datą ' + str(last_invoice.timestamp.date()) + '.')
		reminder = Reminder_Invoice.objects.get(invoice=last_invoice)
		reminder.active = False
		reminder.save()

			
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
	all_reminders = [Reminder_NFZ_New.objects.active(),
					Reminder_NFZ_Confirmed.objects.active(),
					Reminder_PCPR.objects.active(),
					Reminder_Invoice.objects.active(),
					Reminder_Collection.objects.active()]
	
	reminders_list = []
	a = []
	for active_reminders in all_reminders:
		for i in active_reminders:
			if i.__class__.__name__ == 'Reminder_NFZ_New':
				msg = ' otrzymano NOWY wniosek NFZ'
				patient = i.nfz_new.patient
				url_address = reverse('crm:reminder_nfz_new', args=(i.id,))
			elif i.__class__.__name__ == 'Reminder_NFZ_Confirmed':
				msg = ' Otrzymano POTWIERDZONY wniosek NFZ'
				patient = i.nfz_confirmed.patient
				url_address = reverse('crm:reminder_nfz_confirmed', args=(i.id,))
			elif i.__class__.__name__ == 'Reminder_PCPR':
				msg = ' wystawiono kosztorys'
				patient = i.pcpr.patient
				url_address = reverse('crm:reminder_pcpr', args=(i.id,))
			elif i.__class__.__name__ == 'Reminder_Invoice':
				msg = ' wystawiono fakturę'
				patient = i.invoice.patient
				url_address = reverse('crm:reminder_invoice', args=(i.id,))
			elif i.__class__.__name__ == 'Reminder_Collection':
				msg = ' wydano aparat'
				patient = i.ha.patient
				url_address = reverse('crm:reminder_collection', args=(i.id,))
			subject = patient.first_name + ' ' + patient.last_name + ', w dniu: ' + \
				i.timestamp.strftime("%d.%m.%Y") + msg
			reminder = {'url_address': url_address, 'subject': subject}
			reminders_list.append(reminder)

	return render(request, 'crm/reminders.html', {'reminders_list': reminders_list})

@login_required
def reminder_nfz_new(request, reminder_id):
	r = get_object_or_404(Reminder_NFZ_New, pk=reminder_id)
	if request.method == 'POST':
		if request.POST.get('inactivate_reminder') == 'inactivate':
			r.active = False
			r.save()
			messages.success(request, "Przypomnienie usunięte")
			return redirect('crm:reminders')
	msg = ' otrzymano NOWY wniosek NFZ'
	patient = r.nfz_new.patient
	more = ' lewy' if r.nfz_new.side == 'left' else ' prawy'
	subject = patient.first_name + ' ' + patient.last_name + ', w dniu: ' + \
		r.timestamp.strftime("%d.%m.%Y") + msg + more
	context = {'subject': subject,
				'patient': patient,
				'reminder_id': r.id,
            	'url_address': reverse('crm:reminder_nfz_new', args=(r.id,))}
	return render(request, 'crm/reminder.html', context)

@login_required
def reminder_nfz_confirmed(request, reminder_id):
	r = get_object_or_404(Reminder_NFZ_Confirmed, pk=reminder_id)
	if request.method == 'POST':
		if request.POST.get('inactivate_reminder') == 'inactivate':
			r.active = False
			r.save()
			messages.success(request, "Przypomnienie usunięte")
			return redirect('crm:reminders')
	msg = ' otrzymano POTWIERDZONY wniosek NFZ'
	patient = r.nfz_confirmed.patient
	more = ' lewy' if r.nfz_confirmed.side == 'left' else ' prawy'
	subject = patient.first_name + ' ' + patient.last_name + ', w dniu: ' + \
		r.timestamp.strftime("%d.%m.%Y") + msg + more
	context = {'subject': subject,
			'patient': patient,
			'reminder_id': r.id,
            'url_address': reverse('crm:reminder_nfz_confirmed', args=(r.id,))}
	return render(request, 'crm/reminder.html', context)

@login_required
def reminder_pcpr(request, reminder_id):
	r = get_object_or_404(Reminder_PCPR, pk=reminder_id)
	if request.method == 'POST':
		if request.POST.get('inactivate_reminder') == 'inactivate':
			r.active = False
			r.save()
			messages.success(request, "Przypomnienie usunięte")
			return redirect('crm:reminders')
	msg = ' wystawiono kosztorys'
	patient = r.pcpr.patient
	subject = patient.first_name + ' ' + patient.last_name + ', w dniu: ' + \
		r.timestamp.strftime("%d.%m.%Y") + msg
	context = {'subject': subject,
            'patient': patient,
            'reminder_id': r.id,
            'url_address': reverse('crm:reminder_pcpr', args=(r.id,))}
	return render(request, 'crm/reminder.html', context)

@login_required
def reminder_invoice(request, reminder_id):
	r = get_object_or_404(Reminder_Invoice, pk=reminder_id)
	if request.method == 'POST':
		if request.POST.get('inactivate_reminder') == 'inactivate':
			r.active = False
			r.save()
			messages.success(request, "Przypomnienie usunięte")
			return redirect('crm:reminders')
	msg = ' wystawiono fakture'
	patient = r.invoice.patient
	subject = patient.first_name + ' ' + patient.last_name + ', w dniu: ' + \
		r.timestamp.strftime("%d.%m.%Y") + msg
	context = {'subject': subject,
            'patient': patient,
            'reminder_id': r.id,
            'url_address': reverse('crm:reminder_invoice', args=(r.id,))}
	return render(request, 'crm/reminder.html', context)

@login_required
def reminder_collection(request, reminder_id):
	r = get_object_or_404(Reminder_Collection, pk=reminder_id)
	if request.method == 'POST':
		if request.POST.get('inactivate_reminder') == 'inactivate':
			r.active = False
			r.save()
			messages.success(request, "Przypomnienie usunięte")
			return redirect('crm:reminders')
	msg = ' wydano aparat '
	patient = r.ha.patient
	side = 'lewy' if r.ha.ear == 'left' else 'prawy'
	more = str(r.ha) + ' ' + side
	subject = patient.first_name + ' ' + patient.last_name + ', w dniu: ' + \
		r.timestamp.strftime("%d.%m.%Y") + msg + more
	context = {'subject': subject,
            'patient': patient,
            'reminder_id': r.id,
            'url_address': reverse('crm:reminder_collection', args=(r.id,))}
	return render(request, 'crm/reminder.html', context)


@login_required
def invoice_create(request, patient_id):
	# print('in create view:')
	patient = get_object_or_404(Patient, pk=patient_id)
	print(get_devices(Hearing_Aid_Stock))
	ha_list = get_devices(Hearing_Aid_Stock)
	other_items = get_devices(Other_Item_Stock)
	json_ha_list = json.dumps(ha_list, cls= DjangoJSONEncoder)
	json_other_devices = json.dumps(other_items, cls=DjangoJSONEncoder)
	InvoiceFormSet = formset_factory(DeviceForm, extra=1)
	if request.method == 'POST':
		print(request.POST)
		form = InvoiceTypeForm(request.POST)
		formset = InvoiceFormSet(request.POST)
		if form.is_valid() and formset.is_valid():
    		
			# inactivate prevoius invoices (current=False)
			previous_inv = Invoice.objects.filter(patient=patient)
			previous_inv.update(current=False)

    		# create invoice instance
			invoice = form.save(commit=False)
			invoice.patient = patient
			invoice.save()

    		# process devices in a formset
			process_device_formset(formset, patient, invoice, today)
				
			# redirect to detail view with a success message
			messages.success(request, 'Utworzono nową fakturę.')
			return redirect('crm:invoice_detail', invoice.id)
		else:
	    	# redispaly with message
			messages.warning(request, 'Niepoprawne dane, popraw.')
    		
	else:
		form = InvoiceTypeForm()
    	
	context = {	'patient': patient,
				'ha_list': ha_list,
				"json_ha_list": json_ha_list,
            	'json_other_devices': json_other_devices,
				'form': form,
				'formset': InvoiceFormSet()}
	return render(request, 'crm/create_invoice.html', context)


@login_required
def invoice_store(request, patient_id):
	patient = get_object_or_404(Patient, pk=patient_id)
	pass


@login_required
def invoice_detail(request, invoice_id):
	invoice = get_object_or_404(Invoice, pk=invoice_id)
	ha = invoice.hearing_aid_set.all()
	other_devices = invoice.other_item_set.all()
	all_devices = list(ha) + list(other_devices)
	items = {}
	for i in all_devices:
		if str(i) not in items:
			net_price = round(((i.price_gross*100)/(100 + i.vat_rate)), 2)
			items[str(i)] = {
				# 'name': str(i),
				'pkwiu_code': i.pkwiu_code,
				'quantity': 1,
				'price_gross': i.price_gross,
				'net_price': net_price,
				'net_value': net_price,
				'vat_rate': i.vat_rate,
				'vat_amount': round(i.price_gross - decimal.Decimal(net_price), 2),
				'gross_value': i.price_gross
			 }
		else:
			items[str(i)]['quantity'] += 1
    		current_quantity = items[str(i)]['quantity']
    		items[str(i)]['net_value'] *= current_quantity
    		items[str(i)]['vat_amount'] *= current_quantity
    		items[str(i)]['gross_value'] *= current_quantity

	context = {'ha_list': items, 'invoice': invoice}
	# if this ivnvoice is the last one in the system enable its removal
	if Invoice.objects.all().last() == invoice:
		print('this is last invoice')
		context['removable'] = 'removable'
	# print(ha_list)
	return render(request, 'crm/detail_invoice.html', context)


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
