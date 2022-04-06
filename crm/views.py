# -*- coding: utf-8 -*-
import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone as tz
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.utils.decorators import method_decorator

from django.http import HttpResponse, HttpResponseRedirect
from .forms import (Hearing_Aid_StockForm, SZOI_Usage_Form)
from .models import (Patient, NewInfo, PCPR_Estimate, Invoice,
                    Hearing_Aid, Hearing_Aid_Stock,
                    NFZ_Confirmed, Reminder_Collection, Reminder_Invoice,
					Reminder_PCPR,  Reminder_NFZ_Confirmed,
                    SZOI_File, SZOI_File_Usage)
from django.urls import reverse, reverse_lazy
from django.db.models.functions import Lower
from django.db.models import Q
from .utils import get_devices
from .stock_updater import stock_update
today = tz.now()
ears = ['left', 'right']


class Index(LoginRequiredMixin, ListView):
	model = Patient
	paginate_by = 50
	template_name = 'crm/patient_list.html'

	def get_context_data(self, **kwargs):
		# prepare copy of url parameters without 'page'
		# this enables pagination with search filters
		GET_params = self.request.GET.copy()
		if 'page' in GET_params:
			GET_params.pop('page')
		context = {'GET_params': GET_params}
		kwargs.update(context)
		return super().get_context_data(**kwargs)

	def get_ordering(self):
		ordering = self.request.GET.get('order_by', 'create_date')
		return ordering


@login_required
def advancedsearch(request):
	patient_list = Patient.objects.all().order_by(Lower('last_name'))
	results = False
	lname = request.GET.get('lname')
	if lname:
		results = True
		patient_list = patient_list.filter(last_name__icontains=lname)
	fname = request.GET.get('fname')
	if fname:
		results = True
		patient_list = patient_list.filter(first_name__icontains=fname)
	loc = request.GET.get('loc')
	if loc:
		results = True
		patient_list = patient_list.filter(location=loc)

	def patients_from_ha(HA_queryset):
		patients_id = [i.patient.id for i in HA_queryset]
		return Patient.objects.filter(id__in=patients_id)

    # search by patient.active
	active_patients = request.GET.get('only_active_patients')
	if active_patients:
		results = True
		patient_list = patient_list & Patient.objects.filter(active=True)

    # search by patient.requires_action
	requireing_action = request.GET.get('only_requiring_action')
	if requireing_action:
		results = True
		patient_list = patient_list & Patient.objects.filter(requires_action=True)

    # search by patient.phone_no
	phone_number = request.GET.get('phone_number')
	if phone_number:
		results = True
		patient_list = patient_list & Patient.objects.filter(phone_no__icontains=phone_number)

    # search by patient.notes
	search_phrase = request.GET.get('search_phrase_notes')
	if search_phrase:
		results = True
		patients_notes = Patient.objects.filter(notes__icontains=search_phrase)
		patient_list = patient_list & patients_notes

    # search by NewInfo.note
	search_phrase = request.GET.get('search_phrase_newinfo')
	if search_phrase:
		results = True
		patient_list = patient_list & Patient.objects.filter(
			newinfo__note__icontains=search_phrase)

    # search by ha make
	ha_make = request.GET.get('ha_make')
	if ha_make:
		results = True
		all_ha_make = Hearing_Aid.objects.filter(make=ha_make, current=True)
		patient_list = patient_list & patients_from_ha(all_ha_make)
	# search by ha make family and model
	ha_make_family_model = request.GET.get('ha_make_family_model')
	if ha_make_family_model:
		results = True
		ha_make, ha_family, ha_model = ha_make_family_model.split('_')
		all_such_has = Hearing_Aid.objects.filter(make=ha_make, model=ha_model, family=ha_family)
		patient_list = patient_list & patients_from_ha(all_such_has)

	# search by dates of purchase
	if request.GET.get('s_purch_date') or request.GET.get('e_purch_date'):
		results = True
		ha_purchase_start = request.GET.get('s_purch_date') or '1990-01-01'
		ha_purchase_end = request.GET.get('e_purch_date') or str(datetime.datetime.today().date())
		all_such_has = Hearing_Aid.objects.filter(
			purchase_date__range=[ha_purchase_start,ha_purchase_end])
		patient_list = patient_list & patients_from_ha(all_such_has)
	

	# search by dates of NFZ confirmed - only active not prevoius
	if request.GET.get('s_nfz_date') or request.GET.get('e_nfz_date'):
		results = True
		nfz_start = request.GET.get('s_nfz_date') or '1990-01-01'
		nfz_end = request.GET.get(
			'e_nfz_date') or str(datetime.datetime.today().date())
		all_such_nfz = NFZ_Confirmed.objects.filter(
			date__range=[nfz_start, nfz_end], in_progress=True)
		patient_list = patient_list & patients_from_ha(all_such_nfz)

	# search by dates of pcpr estimates - only active not prevoius
	if request.GET.get('s_pcpr_date') or request.GET.get('e_pcpr_date'):
		results = True
		if request.GET.get('s_pcpr_date'):
			pcpr_start = request.GET.get('s_pcpr_date') + "T00:00:00+03:00"
		else:
			pcpr_start = "1990-01-01T00:00:00+03:00"
		if request.GET.get('e_pcpr_date'):
			pcpr_end = request.GET.get('e_pcpr_date') + "T21:00:00+03:00"
		else:
			pcpr_end = today

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
		results = True
		if request.GET.get('s_invoice_date'):
			invoice_start = request.GET.get('s_invoice_date') + "T00:00:30+03:00"
		else:
			invoice_start = "1990-01-01T00:00:00+03:00"
		if request.GET.get('e_invoice_date'):
			invoice_end = request.GET.get('e_invoice_date') + "T21:00:00+03:00"
		else:
			invoice_end = today
		all_such_invoice = Invoice.objects.filter(
			timestamp__range=[invoice_start, invoice_end], current=True)
		patient_ids = []
		for p in all_such_invoice:
			if p.patient.id not in patient_ids:
				patient_ids.append(p.patient.id)
		patients = Patient.objects.filter(id__in=patient_ids)
		patient_list = patient_list & patients

	# prepare copy of url parameters without 'page'
	# this enables pagination with search filters
	GET_params = request.GET.copy()
	if 'page' in GET_params:
		GET_params.pop('page')

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
				'ha_list': get_devices(Hearing_Aid_Stock),
				'results': results,
				'GET_params': GET_params}
	return render(request, 'crm/advanced_search.html', context)


@login_required
def create(request):
	locations = Patient.locations
	audiometrists = User.objects.all()
	context = {	'ha_list': get_devices(Hearing_Aid_Stock), 'ears': ears, 'locations': locations}
	return render(request, 'crm/create.html', context)


@login_required
def edit(request, patient_id):
	# displays form for upadating patient details
	patient = get_object_or_404(Patient, pk=patient_id)
	right_hearing_aid = patient.hearing_aid_set.filter(ear="right", current=True).last()
	left_hearing_aid = patient.hearing_aid_set.filter(
		ear="left", current=True).last()

	nfz_confirmed_left_qs = patient.nfz_confirmed_set.filter(side='left')
	nfz_confirmed_right_qs = patient.nfz_confirmed_set.filter(side='right')

	PCPR_estimate_all = PCPR_Estimate.objects.filter(
		patient=patient).order_by('-timestamp')
	PCPR_estimate_last_active = PCPR_estimate_all.filter(current=True).last()
	if PCPR_estimate_last_active != None:
		PCPR_estimate_all = PCPR_estimate_all.exclude(
			id=PCPR_estimate_last_active.id)

	Invoice_all = Invoice.objects.filter(
		patient=patient,
		current=False
        ).order_by('-timestamp')
	Invoice_active = Invoice.objects.filter(
		patient=patient,
		current=True
        ).order_by('-timestamp')

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
			'ha_list': get_devices(Hearing_Aid_Stock),
			'ears': ears,
            'audiometrists': audiometrists,
			'patient_notes': patient.newinfo_set.order_by('-timestamp'),
			'right_hearing_aid': right_hearing_aid,
			'left_hearing_aid': left_hearing_aid,
			'left_NFZ_confirmed_all': last_and_previous(nfz_confirmed_left_qs)['previous'],
			'left_NFZ_confirmed': last_and_previous(nfz_confirmed_left_qs)['last'],
			'right_NFZ_confirmed_all': last_and_previous(nfz_confirmed_right_qs)['previous'],
			'right_NFZ_confirmed': last_and_previous(nfz_confirmed_right_qs)['last'],
			
			'PCPR_estimate_all': PCPR_estimate_all,
			'PCPR_estimate': PCPR_estimate_last_active,

			'invoice_all': Invoice_all,
			'invoice_active': Invoice_active,
			}

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
        notes = request.POST.get('note'),
        street=request.POST.get('street'),
        house_number=request.POST.get('house_number'),
		apartment_number=request.POST.get('apartment_number'),
		city=request.POST.get('city'),
        zip_code=request.POST.get('zip_code'),
        NIP=request.POST.get('NIP')
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
				ear=ear)
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
				ear=ear)
			hearing_aid.save()
			if request.POST.get(ear + '_purchase_date'):
				hearing_aid.purchase_date = request.POST[ear + '_purchase_date']
				hearing_aid.save()

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
                'street', 'house_number', 'apartment_number', 'zip_code', 'city', 'NIP']
	if request.POST.get('bday'):
		patient.date_of_birth=request.POST['bday']
		update_list.append('date_of_birth')
	patient.save(update_fields=update_list)
	audiometrist = request.user

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
									ear=ear)
			

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
											ear=ear)
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

	if request.POST.get('new_pcpr'):
    	# add new pcpr estimate, inactivate previous pcpr and reminder, inactivate nfz reminder, set new pcpr reminder
		# inactivate previous pcpr estimates, add new note
		pcpr_current = PCPR_Estimate.objects.filter(patient=patient, current=True)
		if pcpr_current:
			PCPR_Estimate.objects.filter(patient=patient, current=True).update(current=False)
			# inactivate preious reminders 
			for single_pcpr_current in pcpr_current:
				Reminder_PCPR.objects.filter(pcpr=single_pcpr_current).update(active=False)
		# inactivate both sides Reminder_NFZ_Confirmed
		nfz_confirmed = NFZ_Confirmed.objects.filter(patient=patient, in_progress=True)
		if Reminder_NFZ_Confirmed.objects.filter(nfz_confirmed__in=nfz_confirmed, active=True):
			Reminder_NFZ_Confirmed.objects.filter(active=True).update(active=False)
		# create new pcpr estimate
		new_pcpr_estimate = PCPR_Estimate.objects.create(patient=patient)
		new_pcpr_estimate.timestamp = request.POST['new_pcpr'] + "T17:41:28+00:00"
		new_pcpr_estimate.save()
		# create new pcpr estimate reminder
		Reminder_PCPR.objects.create(pcpr=new_pcpr_estimate)
		# add new note
		new_action.append('Dodano nowy kosztorys z datą ' + request.POST['new_pcpr'] + '.')
    		
	if request.POST.get('new_invoice'):
    	# add new invoice, set invoice reminder, inactivate previous invoice and its reminder,
		# inactivate previous nfz and pcpr reminders, set new invoice reminder, add new note

		invoice_current = Invoice.objects.filter(patient=patient, current=True)
		if invoice_current:
			Invoice.objects.filter(
				patient=patient, current=True).update(current=False)
			# inactivate preious reminders
			for single_invoice_current in invoice_current:
				Reminder_Invoice.objects.filter(invoice=single_invoice_current).update(active=False)
		# inactivate both sides Reminder_NFZ_Confirmed and Reminder_PCPR
		nfz_confirmed = NFZ_Confirmed.objects.filter(
			patient=patient, in_progress=True)
		if Reminder_NFZ_Confirmed.objects.filter(nfz_confirmed__in=nfz_confirmed, active=True):
			Reminder_NFZ_Confirmed.objects.filter(active=True).update(active=False)
		pcprs = PCPR_Estimate.objects.filter(
						patient=patient, current=True)
		if Reminder_PCPR.objects.filter(pcpr__in=pcprs, active=True):
			Reminder_PCPR.objects.filter(active=True).update(active=False)
		# create new invoice
		new_invoice = Invoice.objects.create(patient=patient)
		new_invoice.timestamp = request.POST['new_invoice'] + "T17:41:28+00:00"
		new_invoice.save()
		# create new invoice reminder
		Reminder_Invoice.objects.create(invoice=new_invoice)
		# add new note
		new_action.append('Dodano nową fakturę z datą ' +
		                  request.POST['new_invoice'] + '.')
	# collection procedure
	if request.POST.get('collection_confirm'):
		# create new HAs and add it to Patient as current
		date = request.POST.get('collection_date') or str(today.date())
		newly_created_ha = []
		for ear in ears:
			if request.POST.get('collection_make_' + ear):
					print('request for ', ear, 'collection_make_' + ear)
					# set previous HA current=False
					old_ha = Hearing_Aid.objects.filter(patient=patient, ear=ear)
					old_ha.update(current=False)
					# create new ha
					make = request.POST.get('collection_make_' + ear)
					family = request.POST.get('collection_family_' + ear)
					model = request.POST.get('collection_model_' + ear)
					ha = Hearing_Aid.objects.create(
						make=make,
						family=family,
						model=model,
						ear=ear,
						patient=patient,
						purchase_date=date
					)
					newly_created_ha.append(ha)
					
		# create new info instance to show in history of actions
		ha_plural = 'y' if len(newly_created_ha)==2 else ''
		new_action.append('Odebrano aparat' + ha_plural + ', z datą ' + date + '.')

		# add reminder
		for ha in newly_created_ha:
			Reminder_Collection.objects.create(
			ha=ha, activation_date=today+datetime.timedelta(days=365))


		# inactivate Invoice and its reminder
		current_invoices = Invoice.objects.filter(patient=patient, current=True)
		for current_invoice in current_invoices:
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

		# inactivate Patient's .active and .requires_action fields
		patient.active=False
		patient.requires_action=False
		patient.save()

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

	if request.POST.get('patient_activate') == 'on' and not patient.active and not request.POST.get('collection_confirm'):
		patient.active = True
		patient.save()
		NewInfo.objects.create(	patient=patient,
									note='aktywacja - klient w trakcie zakupu',
									audiometrist=audiometrist)

	if request.POST.get('patient_activate') == None and patient.active:
		patient.active = False
		patient.save()
		NewInfo.objects.create(	patient=patient,
									note='deaktywacja - klient poza procesem zakupu',
									audiometrist=audiometrist)

	if request.POST.get('requires_action') == 'on' and not patient.requires_action and not request.POST.get('collection_confirm'):
		patient.requires_action = True
		patient.save()
		NewInfo.objects.create(	patient=patient,
                          		note='klient wymaga uwagi',
								audiometrist=audiometrist)

	if request.POST.get('requires_action') == None and patient.requires_action:
		patient.requires_action = False
		patient.save()
		NewInfo.objects.create(	patient=patient,
                          		note='deaktywacja klient wymaga uwagi',
								audiometrist=audiometrist)
	if new_action:
		NewInfo.objects.create(	patient=patient,
                          		note=' '.join(new_action),
								audiometrist=audiometrist)

	if request.POST.get('new_note'):
		NewInfo.objects.create(	patient=patient,
							note=request.POST['new_note'],
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
	all_reminders = [Reminder_NFZ_Confirmed.objects.active(),
					Reminder_PCPR.objects.active(),
					Reminder_Invoice.objects.active(),
					Reminder_Collection.objects.active()]
	
	reminders_list = []
	a = []
	for active_reminders in all_reminders:
		for i in active_reminders:
			if i.__class__.__name__ == 'Reminder_NFZ_Confirmed':
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


class HAStockCreate(CreateView):
	model = Hearing_Aid_Stock
	form_class = Hearing_Aid_StockForm
	template_name = 'crm/create_ha_stock.html'

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(HAStockCreate, self).dispatch(*args, **kwargs)


class HAStockUpdate(UpdateView):
	model = Hearing_Aid_Stock
	form_class = Hearing_Aid_StockForm
	template_name = 'crm/update_ha_stock.html'

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(HAStockUpdate, self).dispatch(*args, **kwargs)


class HAStockList(ListView):
	model = Hearing_Aid_Stock

	def get(self, request, *args, **kwargs):
		self.results = Hearing_Aid_Stock.objects.all()
		query = request.GET.get('q', '')
		if query:
			qs = Hearing_Aid_Stock.objects.filter(
                            Q(make__icontains=query) |
                            Q(family__icontains=query) |
                            Q(model__icontains=query)
                        ).distinct()
			self.results = qs

		return super(HAStockList, self).get(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		return super(HAStockList, self).get_context_data(results=self.results, **kwargs)

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(HAStockList, self).dispatch(*args, **kwargs)


class HAStockDelete(DeleteView):
	model = Hearing_Aid_Stock
	success_url = reverse_lazy('crm:towary')

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(HAStockDelete, self).dispatch(*args, **kwargs)



class SZOICreate(CreateView):
	model = SZOI_File
	fields = ['file']

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(SZOICreate, self).dispatch(*args, **kwargs)

class SZOIDetail(DetailView):
	model = SZOI_File

	def get_context_data(self, **kwargs):
		context = super(SZOIDetail, self).get_context_data(**kwargs)
		context['form'] = SZOI_Usage_Form
		szoi_file = self.get_object()
		context['szoi_usage_list'] = szoi_file.szoi_file_usage_set.all()
		return context

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(SZOIDetail, self).dispatch(*args, **kwargs)


class SZOIList(ListView):
	model = SZOI_File

	def dispatch(self, *args, **kwargs):
		return super(SZOIList, self).dispatch(*args, **kwargs)

class SZOI_UsageCreate(CreateView):
	model = SZOI_File_Usage

	def post(self, request, *args, **kwargs):
		form = SZOI_Usage_Form(request.POST)
		if form.is_valid():
			szoi_file = form.cleaned_data['szoi_file']
			# create SZOI_File_Usage instance
			s = SZOI_File_Usage.objects.create(
				szoi_file=szoi_file
				)

			# process csv file
			devices = stock_update(szoi_file, s)

			# add ha and other to SZOI_File_Usage instance
			for ha_new in devices['ha_new']:
				ha_new.szoi_new = s
				ha_new.save()
			for o_new in devices['other_new']:
				o_new.szoi_new = s
				o_new.save()

			return redirect('crm:szoi_usage_detail', s.id)

		else:
			self.object = self.get_object()
			context = super(SZOI_UsageCreate, self).get_context_data(**kwargs)
			context['form'] = form
			return self.render_to_response( context=context)

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(SZOI_UsageCreate, self).dispatch(*args, **kwargs)

class SZOI_UsageDetail(DetailView):
	model = SZOI_File_Usage

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(SZOI_UsageDetail, self).dispatch(*args, **kwargs)
