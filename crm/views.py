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
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.utils.decorators import method_decorator
from django.forms.widgets import Textarea
from django.forms.models import modelform_factory

from django.http import HttpResponse, HttpResponseRedirect, Http404
from .forms import (PatientForm, DeviceForm,
                    Hearing_Aid_StockForm, Other_Item_StockForm,
                    SZOI_Usage_Form)
from .models import (Patient, NewInfo, PCPR_Estimate, Invoice,
                    Hearing_Aid, Hearing_Aid_Stock, Other_Item, Other_Item_Stock,
                    NFZ_Confirmed, Reminder_Collection, Reminder_Invoice,
					Reminder_PCPR,  Reminder_NFZ_Confirmed,
                    SZOI_File, SZOI_File_Usage)
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models.functions import Lower
from django.db.models import Q
from .other_devices import other_devices
from .utils import (get_devices, process_device_formset_invoice,
                    process_device_formset_pcpr, get_finance_context)
from .stock_updater import stock_update
import json, decimal
today = datetime.date.today()
ears = ['left', 'right']

@login_required
def index(request):
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
				'ha_list': get_devices(Hearing_Aid_Stock)}
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
		patient=patient).order_by('timestamp')
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
	patient.NIP = request.POST['NIP']

	update_list = ['first_name', 'last_name', 'phone_no', 'location', 'notes',
                'street', 'house_number', 'apartment_number', 'zip_code', 'city', 'NIP']
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
			Reminder_NFZ_Confirmed.objects.filter(
				patient=patient, active=True).update(active=False)
		# create new pcpr estimate
		new_pcpr_estimate = PCPR_Estimate.objects.create(patient=patient)
		new_pcpr_estimate.timestamp = request.POST['new_pcpr'] + "T17:41:28+00:00"
		new_pcpr_estimate.save()
		# create new pcpr estimate reminder
		Reminder_PCPR.objects.create(pcpr=new_pcpr_estimate)
		# add new note
		new_action.append('Dodano nowy kosztorys z datą ' + request.POST['new_pcpr'] + '.')
    		
	if request.POST.get('invoice'):
    	# add new invoice, set invoice reminder, inactivate previous, inactivate previous nfz and pcpr reminders
		pass

	# collection procedure
	if request.POST.get('collection_confirm'):
		# current_invoice = Invoice.objects.get(patient=patient, current=True)
		current_invoices = Invoice.objects.filter(patient=patient, current=True)
		
		invoiced_ha = Hearing_Aid.objects.filter(invoice__in=current_invoices)
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


class OtherStockCreate(CreateView):
	model = Other_Item_Stock
	form_class = Other_Item_StockForm

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(OtherStockCreate, self).dispatch(*args, **kwargs)


class OtherStockUpdate(UpdateView):
	model = Other_Item_Stock
	form_class = Other_Item_StockForm
	template_name = 'crm/update_other_stock.html'

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(OtherStockUpdate, self).dispatch(*args, **kwargs)


class OtherStockList(ListView):
	model = Other_Item_Stock
	def get(self, request, *args, **kwargs):
		self.results = Other_Item_Stock.objects.all()
		query = request.GET.get('q', '')
		if query:
			qs = Other_Item_Stock.objects.filter(
				Q(make__icontains=query) |
				Q(family__icontains=query) |
				Q(model__icontains=query)
				).distinct()
			self.results = qs

		return super(OtherStockList, self).get(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		return super(OtherStockList, self).get_context_data(results=self.results, **kwargs)

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(OtherStockList, self).dispatch(*args, **kwargs)


class OtherStockDelete(DeleteView):
	model = Other_Item_Stock
	success_url = reverse_lazy('crm:towary')

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(OtherStockDelete, self).dispatch(*args, **kwargs)


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
			for ha_update in devices['ha_update']:
				ha_update.szoi_updated = s
				ha_update.save()
			for o_new in devices['other_new']:
				o_new.szoi_new = s
				o_new.save()
			for o_update in devices['other_update']:
				o_update.szoi_updated = s
				o_update.save()

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
