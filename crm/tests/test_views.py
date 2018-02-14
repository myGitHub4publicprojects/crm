# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.contrib import auth
from django.core.paginator import Paginator

from mixer.backend.django import mixer
import pytest
from datetime import datetime, timedelta
from django.contrib.staticfiles.templatetags.staticfiles import static

from crm.models import (Patient, Hearing_Aid, NFZ_Confirmed, PCPR_Estimate,
                        HA_Invoice, NewInfo, Audiogram)

pytestmark = pytest.mark.django_db
today = datetime.today().date()
now = datetime.now()

class TestIndexView(TestCase):
    def setUp(self):
        patient1 = Patient.objects.create(first_name = 'John', last_name = 'Smith1',)
        patient2 = Patient.objects.create(first_name = 'John', last_name = 'Smith2',
            date_of_birth=today-timedelta(days=1))
        patient3 = Patient.objects.create(first_name = 'John', last_name = 'Smith3',
            date_of_birth=today-timedelta(days=2))
        patient4 = Patient.objects.create(first_name = 'John', last_name = 'Smith4',
            date_of_birth=today-timedelta(days=3))
        patient4.create_date=now-timedelta(days=3)
        patient4.save()

    def test_anonymous(self):
        url = reverse('crm:index')
        response = self.client.get(url)
        all_patients = Patient.objects.all()
        assert response.status_code == 200, 'Should be callable by anyone'
        self.assertEqual(len(response.context['patients']), 4)

    def test_order_by_date_of_birth(self):
        '''should sort patients based on date of birth, starting from those without
        a specified date, then oldest to youngest'''
        data={'order_by': 'date_of_birth'}
        url = reverse('crm:index')
        response = self.client.get(url, data)
        first_object = Patient.objects.all().first()
        first_in_context = response.context['patients'][0]
        self.assertEqual(first_object, first_in_context)
        youngest_patient = Patient.objects.get(date_of_birth=today-timedelta(days=1))
        last_in_context = response.context['patients'][-1]
        self.assertEqual(youngest_patient, last_in_context)

    def test_order_by_create_date(self):
        '''should sort patients based on create_date, starting from oldest to youngest'''
        data={'order_by': 'create_date'}
        url = reverse('crm:index')
        response = self.client.get(url, data)
        object_oldest_create_date = Patient.objects.get(id=4)
        first_in_context = response.context['patients'][0]
        self.assertEqual(object_oldest_create_date, first_in_context)
        object_latest_create_date = Patient.objects.get(id=3)
        last_in_context = response.context['patients'][-1]
        self.assertEqual(object_latest_create_date, last_in_context)

    def test_query(self):
        '''should return patients with last name containing given query'''
        data={'q': 'Smith'}
        url = reverse('crm:index')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patients']), 4)

    def test_pagination_page_over_9999(self):
        data = {'page': '99999'}
        url = reverse('crm:index')
        response = self.client.get(url, data)
        # should show last page (1)
        self.assertEqual(response.context['patients'].paginator.num_pages, 1)

class TestAdvancedSearchView(TestCase):
    def setUp(self):
        patient1 = Patient.objects.create(first_name = 'John', last_name = 'Smith1',)
        patient2 = Patient.objects.create(first_name = 'John', last_name = 'Smith2',
            date_of_birth=today-timedelta(days=1))
        patient3 = Patient.objects.create(first_name = 'John', last_name = 'Smith3',
            date_of_birth=today-timedelta(days=2))
        patient4 = Patient.objects.create(first_name = 'Adam', last_name = 'Smith4',
            date_of_birth=today-timedelta(days=3))
        patient4.create_date=now-timedelta(days=3)
        patient4.location = 'Mosina'
        patient4.save()

        ha1 = Hearing_Aid.objects.create(patient = Patient.objects.get(id=1),
                            ha_make = 'Bernafon',
                            ha_family = 'WIN',
                            ha_model = '102',
                            ear = 'left',
                            purchase_date = '2000-01-01')
        ha2 = Hearing_Aid.objects.create(patient = Patient.objects.get(id=2),
                            ha_make = 'Bernafon',
                            ha_family = 'WIN',
                            ha_model = '102',
                            ear = 'left',
                            purchase_date = '2010-01-01')
        ha3 = Hearing_Aid.objects.create(patient = Patient.objects.get(id=3),
                            ha_make = 'Phonak',
                            ha_family = 'Naida Q',
                            ha_model = '30 SP',
                            ear = 'left',
                            purchase_date = '2016-01-01')
    
    def test_search_last_name(self):
        '''should return one patient with last name: Smith3'''
        data={'lname': 'Smith3'}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 1)
        response_patient_last_name = response.context['patient_list'][0].last_name
        self.assertEqual(response_patient_last_name, 'Smith3')

    def test_search_first_name(self):
        '''should return one patient with first name: Adam'''
        data={'fname': 'Adam'}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 1)
        response_patient_first_name = response.context['patient_list'][0].first_name
        self.assertEqual(response_patient_first_name, 'Adam')

    def test_search_location(self):
        '''should return one patient with location: Mosina'''
        data={'loc': 'Mosina'}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 1)
        response_patient_location = response.context['patient_list'][0].location
        self.assertEqual(response_patient_location, 'Mosina')

    def test_search_hearing_aid_make(self):
        '''should return patients wearing hearing aids by Bernafon (2)'''
        ha1 = Hearing_Aid.objects.get(id=1)
        ha2 = Hearing_Aid.objects.get(id=2)
        ha3 = Hearing_Aid.objects.get(id=3)
        data={'ha_make': 'Bernafon'}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 2)

    def test_search_hearing_aid_make_family_model(self):
        '''should return patients wearing Phonak Naida Q 30 SP aid (1)'''
        ha1 = Hearing_Aid.objects.get(id=1)
        ha2 = Hearing_Aid.objects.get(id=2)
        ha3 = Hearing_Aid.objects.get(id=3)
        data={'ha_make_family_model': 'Phonak_Naida Q_30 SP'}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 1)

    def test_search_hearing_aid_by_purchase_date_only_lower_band(self):
        '''only lower band of dates is given - upper band should default to today
        should return only patients with hearing aids purchased after the lower band date'''
        ha1 = Hearing_Aid.objects.get(id=1)
        ha2 = Hearing_Aid.objects.get(id=2)
        ha3 = Hearing_Aid.objects.get(id=3)
        lower_band = '2000-01-02'
        data={'s_purch_date': lower_band}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 2)

    def test_search_hearing_aid_by_purchase_date_only_upper_band(self):
        '''only upper band of dates is given - lower band should default to '1990-01-01'
        should return only patients with hearing aids purchased before the upper band date'''
        ha1 = Hearing_Aid.objects.get(id=1)
        ha2 = Hearing_Aid.objects.get(id=2)
        ha3 = Hearing_Aid.objects.get(id=3)
        upper_band = '2000-01-02'
        data={'e_purch_date': upper_band}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 1)

    def test_search_hearing_aid_by_purchase_date_both_lower_and_upper_band(self):
        '''both lower and upper band of dates is given, should return only patients
        with hearing aids purchased after the lower band and before the upper band date'''
        ha1 = Hearing_Aid.objects.get(id=1)
        ha2 = Hearing_Aid.objects.get(id=2)
        ha3 = Hearing_Aid.objects.get(id=3)
        lower_band = '2000-01-01'
        upper_band = '2000-01-02'
        data={'s_purch_date': lower_band, 'e_purch_date': upper_band}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 1)

    def test_search_nfz_confirmed_by_date_both_lower_and_upper_band(self):
        '''both lower and upper band of dates is given, should return only patients
        with NFZ confirmed after the lower band and before the upper band date'''
        patient1 = Patient.objects.get(id=1)
        patient2 = Patient.objects.get(id=2)
        patient3 = Patient.objects.get(id=3)
        NFZ_Confirmed.objects.create(patient=patient1, date='2001-01-01', side='left')
        NFZ_Confirmed.objects.create(patient=patient2, date='2001-01-01', side='left')
        NFZ_Confirmed.objects.create(patient=patient1, date='2002-01-01', side='left')
        # date out of range
        NFZ_Confirmed.objects.create(patient=patient3, date='2003-01-01', side='left')
        # inactive
        NFZ_Confirmed.objects.create(patient=patient3, date='2002-01-01', side='left',
                                        in_progress=False)
        lower_band = '2000-01-01'
        upper_band = '2002-01-02'
        data={'s_nfz_date': lower_band, 'e_nfz_date': upper_band}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 2)


    def test_search_pcpr_estimate_date_both_lower_and_upper_band(self):
        '''both lower and upper band of dates is given, should return only patients
        with NFZ confirmed after the lower band and before the upper band date'''
        patient1 = Patient.objects.get(id=1)
        patient2 = Patient.objects.get(id=2)
        patient3 = Patient.objects.get(id=3)
        PCPR_Estimate.objects.create(
            patient=patient1, date='2001-01-01', ear='left',
            ha_make='a', ha_family='b', ha_model='c')
        PCPR_Estimate.objects.create(
            patient=patient2, date='2001-01-01', ear='left',
            ha_make='a', ha_family='b', ha_model='c')
        PCPR_Estimate.objects.create(
            patient=patient1, date='2002-01-01', ear='left',
            ha_make='a', ha_family='b', ha_model='c')
            # date out of range
        PCPR_Estimate.objects.create(
            patient=patient3, date='2003-01-01', ear='left',
            ha_make='a', ha_family='b', ha_model='c')
            # inactive
        PCPR_Estimate.objects.create(
            patient=patient3, date='2001-01-01', ear='left',
            ha_make='a', ha_family='b', ha_model='c', in_progress=False)
        lower_band = '2000-01-01'
        upper_band = '2002-01-02'
        data = {'s_pcpr_date': lower_band, 'e_pcpr_date': upper_band}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 2)

    def test_search_ha_invoice_date_both_lower_and_upper_band(self):
        '''both lower and upper band of dates is given, should return only patients
        with NFZ confirmed after the lower band and before the upper band date'''
        patient1 = Patient.objects.get(id=1)
        patient2 = Patient.objects.get(id=2)
        patient3 = Patient.objects.get(id=3)
        HA_Invoice.objects.create(
            patient=patient1, date='2001-01-01', ear='left',
            ha_make='a', ha_family='b', ha_model='c')
        HA_Invoice.objects.create(
            patient=patient2, date='2001-01-01', ear='left',
            ha_make='a', ha_family='b', ha_model='c')
        HA_Invoice.objects.create(
            patient=patient1, date='2002-01-01', ear='left',
            ha_make='a', ha_family='b', ha_model='c')
        # date out of range
        HA_Invoice.objects.create(
            patient=patient3, date='2003-01-01', ear='left',
            ha_make='a', ha_family='b', ha_model='c')
        # inactive
        HA_Invoice.objects.create(
            patient=patient3, date='2001-01-01', ear='left',
            ha_make='a', ha_family='b', ha_model='c', in_progress=False)
        lower_band = '2000-01-01'
        upper_band = '2002-01-02'
        data = {'s_invoice_date': lower_band, 'e_invoice_date': upper_band}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 2)

class TestCreateView(TestCase):
    def test_anonymous(self):
        url = reverse('crm:create')
        response = self.client.get(url)
        assert response.status_code == 200, 'Should be callable by anyone'


class TestEditView(TestCase):
    def setUp(self):
        patient1 = Patient.objects.create(first_name = 'John', last_name = 'Smith1',)
        patient2 = Patient.objects.create(first_name = 'John', last_name = 'Smith2',)
        patient3 = Patient.objects.create(first_name = 'John', last_name = 'Smith3',)
    def test_anonymous(self):
        patient1 = Patient.objects.get(id=1)
        response = self.client.get(reverse('crm:edit', args=(patient1.id,)))
        assert response.status_code == 200, 'Should be callable by anyone'

    def test_patient_with_only_inactive_NFZ_confirmed(self):
        ''' scenario with only inactive (in_progres=False) latest (.last()) NFZ confirmed
        instances '''
        patient1 = Patient.objects.get(id=1)
        nfz1 = NFZ_Confirmed.objects.create(patient=patient1,
                            date = today,
                            side = 'left',
                            in_progress = False)
        nfz2 = NFZ_Confirmed.objects.create(patient=patient1,
                            date = today,
                            side = 'right',
                            in_progress = False)
        response = self.client.get(reverse('crm:edit', args=(patient1.id,)))
        self.assertIsNone(response.context['left_NFZ_confirmed'])
        self.assertIsNone(response.context['right_NFZ_confirmed'])

    def test_patient_with_only_one_active_NFZ_confirmed(self):
        ''' scenario with only left active (in_progres=True)
        latest (.last()) NFZ confirmed instance 
        there is also one, former, inactive left instance'''
        patient1 = Patient.objects.get(id=1)
        nfz0 = NFZ_Confirmed.objects.create(patient=patient1,
                            date = today,
                            side = 'left',
                            in_progress = False)
        nfz1 = NFZ_Confirmed.objects.create(patient=patient1,
                            date = today,
                            side = 'left',
                            in_progress = True)
        nfz2 = NFZ_Confirmed.objects.create(patient=patient1,
                            date = today,
                            side = 'right',
                            in_progress = False)
        response = self.client.get(reverse('crm:edit', args=(patient1.id,)))
        self.assertIsNotNone(response.context['left_NFZ_confirmed'])
        self.assertEqual(response.context['left_NFZ_confirmed'], nfz1)
        self.assertEqual(len(response.context['left_NFZ_confirmed_all']), 1)
        self.assertIsNone(response.context['right_NFZ_confirmed'])
        
    def test_patient_with_both_active_NFZ_confirmed(self):
        ''' scenario with left and right active (in_progres=True)
        latest (.last()) NFZ confirmed instance 
        there are also former, inactive left and right instance'''
        patient1 = Patient.objects.get(id=1)
        nfz0 = NFZ_Confirmed.objects.create(patient=patient1,
                            date = today,
                            side = 'left',
                            in_progress = False)
        nfz1 = NFZ_Confirmed.objects.create(patient=patient1,
                            date = today,
                            side = 'left',
                            in_progress = True)
        nfz2 = NFZ_Confirmed.objects.create(patient=patient1,
                            date = today,
                            side = 'right',
                            in_progress = False)
        nfz3 = NFZ_Confirmed.objects.create(patient=patient1,
                            date = today,
                            side = 'right',
                            in_progress = True)
        response = self.client.get(reverse('crm:edit', args=(patient1.id,)))
        self.assertIsNotNone(response.context['left_NFZ_confirmed'])
        self.assertEqual(response.context['left_NFZ_confirmed'], nfz1)
        self.assertEqual(len(response.context['left_NFZ_confirmed_all']), 1)
        self.assertIsNotNone(response.context['right_NFZ_confirmed'])
        self.assertEqual(response.context['right_NFZ_confirmed'], nfz3)
        self.assertEqual(len(response.context['right_NFZ_confirmed_all']), 1)

    def test_patient_with_only_inactive_PCPR_Estimate(self):
        ''' scenario with only inactive (in_progres=False) latest (.last()) PCPR_Estimate
        instances'''
        patient1 = Patient.objects.get(id=1)
        pcpr1 = PCPR_Estimate.objects.create(patient=patient1,
                            ha_make = 'Bernafon',
                            ha_family = 'WIN',
                            ha_model = '102',
                            ear = 'left',
                            date = today,
                            in_progress = False)
        pcpr2 = PCPR_Estimate.objects.create(patient=patient1,
                            ha_make = 'Bernafon',
                            ha_family = 'WIN',
                            ha_model = '102',
                            ear = 'right',
                            date = today,
                            in_progress = False)
        response = self.client.get(reverse('crm:edit', args=(patient1.id,)))
        self.assertIsNone(response.context['left_PCPR_estimate'])
        self.assertEqual(len(response.context['left_PCPR_estimate_all']), 1)
        self.assertIsNone(response.context['right_PCPR_estimate'])
        self.assertEqual(len(response.context['right_PCPR_estimate_all']), 1)

    def test_patient_with_two_active_and_two_inactive_PCPR_Estimate(self):
        ''' scenario with active (both left and right) and two inactive (in_progres=False)
        latest (.last()) PCPR_Estimate instances '''
        patient1 = Patient.objects.get(id=1)
        pcpr0 = PCPR_Estimate.objects.create(patient=patient1,
                            ha_make = 'Bernafon',
                            ha_family = 'WIN',
                            ha_model = '102',
                            ear = 'left',
                            date = today,
                            in_progress = False)
        pcpr1 = PCPR_Estimate.objects.create(patient=patient1,
                            ha_make = 'Bernafon',
                            ha_family = 'WIN',
                            ha_model = '102',
                            ear = 'left',
                            date = today,
                            in_progress = True)
        pcpr2 = PCPR_Estimate.objects.create(patient=patient1,
                            ha_make = 'Bernafon',
                            ha_family = 'WIN',
                            ha_model = '102',
                            ear = 'right',
                            date = today,
                            in_progress = False)
        pcpr3 = PCPR_Estimate.objects.create(patient=patient1,
                            ha_make = 'Bernafon',
                            ha_family = 'WIN',
                            ha_model = '102',
                            ear = 'right',
                            date = today,
                            in_progress = True)
        response = self.client.get(reverse('crm:edit', args=(patient1.id,)))
        self.assertEqual(response.context['left_PCPR_estimate'], pcpr1)
        self.assertEqual(len(response.context['left_PCPR_estimate_all']), 1)
        self.assertEqual(response.context['right_PCPR_estimate'], pcpr3)
        self.assertEqual(len(response.context['right_PCPR_estimate_all']), 1)

    def test_patient_with_only_inactive_HA_Invoice(self):
        ''' scenario with only inactive (in_progres=False) latest (.last()) HA_Invoice
        instances '''
        patient1 = Patient.objects.get(id=1)
        invoice1 = HA_Invoice.objects.create(patient=patient1,
                            ha_make = 'Bernafon',
                            ha_family = 'WIN',
                            ha_model = '102',
                            ear = 'left',
                            date = today,
                            in_progress = False)
        invoice2 = HA_Invoice.objects.create(patient=patient1,
                            ha_make = 'Bernafon',
                            ha_family = 'WIN',
                            ha_model = '102',
                            ear = 'right',
                            date = today,
                            in_progress = False)
        invoice3 = HA_Invoice.objects.create(patient=patient1,
                            ha_make='Bernafon',
                            ha_family='WIN',
                            ha_model='102',
                            ear='right',
                            date=today,
                            in_progress=False)
        response = self.client.get(reverse('crm:edit', args=(patient1.id,)))
        self.assertIsNone(response.context['left_invoice'])
        self.assertEqual(len(response.context['left_invoice_all']), 1)
        self.assertIsNone(response.context['right_invoice'])
        self.assertEqual(len(response.context['right_invoice_all']), 2)

    def test_patient_with_two_active_and_two_inactive_HA_Invoice(self):
        ''' scenario with active (both left and right) and two inactive (in_progres=False)
        latest (.last()) HA_Invoice instances '''
        patient1 = Patient.objects.get(id=1)
        invoice0 = HA_Invoice.objects.create(patient=patient1,
                            ha_make = 'Bernafon',
                            ha_family = 'WIN',
                            ha_model = '102',
                            ear = 'left',
                            date = today,
                            in_progress = False)
        invoice1 = HA_Invoice.objects.create(patient=patient1,
                            ha_make = 'Bernafon',
                            ha_family = 'WIN',
                            ha_model = '102',
                            ear = 'left',
                            date = today,
                            in_progress = True)
        invoice2 = HA_Invoice.objects.create(patient=patient1,
                            ha_make = 'Bernafon',
                            ha_family = 'WIN',
                            ha_model = '102',
                            ear = 'right',
                            date = today,
                            in_progress = False)
        invoice3 = HA_Invoice.objects.create(patient=patient1,
                            ha_make = 'Bernafon',
                            ha_family = 'WIN',
                            ha_model = '102',
                            ear = 'right',
                            date = today,
                            in_progress = True)
        response = self.client.get(reverse('crm:edit', args=(patient1.id,)))
        self.assertEqual(response.context['left_invoice'], invoice1)
        self.assertEqual(len(response.context['left_invoice_all']), 1)
        self.assertEqual(response.context['right_invoice'], invoice3)
        self.assertEqual(len(response.context['right_invoice_all']), 1)

    def test_patient_with_two_left_and_two_right_Audiograms(self):
        ''' scenario with two left and two right Audiogram instances '''
        patient1 = Patient.objects.get(id=1)
        aud0 = Audiogram.objects.create(patient=patient1,
                            time_of_test=now - timedelta(days=1),
                            ear = 'left')
        aud1 = Audiogram.objects.create(patient=patient1,
                            time_of_test=now,
                            ear = 'left')
        aud2 = Audiogram.objects.create(patient=patient1,
                            time_of_test=now - timedelta(days=1),
                            ear = 'right')
        aud3 = Audiogram.objects.create(patient=patient1,
                            time_of_test=now,
                            ear = 'right')
        response = self.client.get(reverse('crm:edit', args=(patient1.id,)))
        self.assertEqual(response.context['left_audiogram'], aud1)
        self.assertEqual(response.context['right_audiogram'], aud3)


class TestStoreView(TestCase):
    def setUp(self):
        patient1 = Patient.objects.create(
            first_name='John', last_name='Smith1',)
        patient2 = Patient.objects.create(
            first_name='John', last_name='Smith2',)
        patient3 = Patient.objects.create(
            first_name='John', last_name='Smith3',)

    def test_anonymous(self):
        data = {'fname': 'Adam',
                'lname': 'Atkins',
                'bday': '2000-01-01',
                'usrtel': 1,
                'audiometrist': 'Olo',
                'location': 'some_location',
                'left_ha': 'model1_family1_brand1',
                'right_ha': 'model2_family2_brand2',
                'left_purchase_date': '1999-01-01',
                'right_purchase_date': '1999-01-02',
                'left_NFZ_confirmed_date': '2001-01-01',
                'right_NFZ_confirmed_date': '2002-02-02',
                'left_ha_estimate': 'model3_f3_b3',
                'right_ha_estimate': 'b4_f4_m4',
                'left_pcpr_etimate_date': '2003-01-01',
                'right_pcpr_etimate_date': '2004-01-01',
                'note': 'p1_note',
                }

        url = reverse('crm:store')
        # id of new patient is set to 4 as there are already 3 in from setUp function
        expected_url = reverse('crm:edit', args=(4,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                     status_code=302, target_status_code=200)

class TestUpdatingView(TestCase):
    data = {'fname': 'Adam',
                    'lname': 'Atkins',
                    'usrtel': 1,
                    'location': 'some_location',

                    }
    def setUp(self):
        patient1 = Patient.objects.create(first_name = 'John', last_name = 'Smith1',)
        patient2 = Patient.objects.create(first_name = 'John', last_name = 'Smith2',)
        patient3 = Patient.objects.create(first_name = 'John', last_name = 'Smith3',)
    def test_change_name_tel_location(self):
        patient1 = Patient.objects.get(id=1)
        data = self.data.copy()
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        patient1.refresh_from_db()
        self.assertEqual(patient1.first_name, 'Adam')
        self.assertEqual(patient1.last_name, 'Atkins')
        self.assertEqual(patient1.phone_no, 1)
        self.assertEqual(patient1.location, 'some_location')

    def test_add_audiometrist_birth_day_note(self):
        patient1 = Patient.objects.get(id=1)
        data = self.data.copy()
        data['new_note'] = 'p_note'
        data['bday'] = '2000-01-01'
        data['audiometrist'] = 'John'
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        patient1.refresh_from_db()
        self.assertEqual(str(patient1.date_of_birth), '2000-01-01')
        new_note = NewInfo.objects.get(id=1)
        self.assertEqual(new_note.note, 'p_note')
        self.assertEqual(new_note.audiometrist, 'John')

    def test_adding_hearing_aids(self):
        patient1 = Patient.objects.get(id=1)
        data = self.data.copy()
        data['left_ha'] = 'b1_family1_model1'
        data['right_ha'] = 'b2_family2_model2'
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        left_ha_all = Hearing_Aid.objects.filter(patient=patient1, ear='left')
        right_ha_all = Hearing_Aid.objects.filter(patient=patient1, ear='right')
        self.assertEqual(len(left_ha_all), 1)
        self.assertEqual(len(right_ha_all), 1)
        self.assertEqual(left_ha_all.last().ha_model, 'model1')
        self.assertEqual(right_ha_all.last().ha_model, 'model2')
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Dodano lewy aparat b1 family1 model1. ' + \
                        'Dodano prawy aparat b2 family2 model2.'

        self.assertEqual(new_info.note, expected_note)

    def test_adding_another_hearing_aids_with_purchase_dates(self):
        patient1 = Patient.objects.get(id=1)
        Hearing_Aid.objects.create(patient=patient1,
                                    ear='left',
                                    ha_make='m',
                                    ha_family='f',
                                    ha_model='m')
        Hearing_Aid.objects.create(patient=patient1,
                                    ear='right',
                                    ha_make='m',
                                    ha_family='f',
                                    ha_model='m')
        data = self.data.copy()
        data['left_ha'] = 'b1_family1_model1'
        data['right_ha'] = 'b2_family2_model2'
        data['left_purchase_date'] = '2001-01-01'
        data['right_purchase_date'] = '2001-01-02'
        data['left_ha_other'] = True
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        left_ha_all = Hearing_Aid.objects.filter(patient=patient1, ear='left')
        right_ha_all = Hearing_Aid.objects.filter(
            patient=patient1, ear='right')
        self.assertEqual(len(left_ha_all), 2)
        self.assertEqual(len(right_ha_all), 2)
        self.assertEqual(left_ha_all.last().ha_model, 'model1')
        self.assertEqual(right_ha_all.last().ha_model, 'model2')
        self.assertEqual(str(left_ha_all.last().purchase_date), '2001-01-01')
        self.assertEqual(str(right_ha_all.last().purchase_date), '2001-01-02')
        self.assertFalse(left_ha_all.last().our)

    def test_adding_NFZ_confirmed(self):
        patient1 = Patient.objects.get(id=1)
        data = self.data.copy()
        data['NFZ_left'] = '2001-01-01'
        data['NFZ_right'] = '2001-01-02'
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        left_nfz_all = NFZ_Confirmed.objects.filter(patient=patient1, side='left')
        right_nfz_all = NFZ_Confirmed.objects.filter(patient=patient1, side='right')
        self.assertEqual(len(left_nfz_all), 1)
        self.assertEqual(len(right_nfz_all), 1)
        self.assertEqual(str(left_nfz_all.last().date), '2001-01-01')
        self.assertEqual(str(right_nfz_all.last().date), '2001-01-02')

    def test_adding_another_NFZ(self):
        patient1 = Patient.objects.get(id=1)
        NFZ_Confirmed.objects.create(patient=patient1,
                                   side='left',
                                   date='2000-01-01')
        NFZ_Confirmed.objects.create(patient=patient1,
                                     side='right',
                                     date='2000-01-02')
        data = self.data.copy()
        data['NFZ_left'] = '2001-01-01'
        data['NFZ_right'] = '2001-01-02'
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)


        left_nfz_all = NFZ_Confirmed.objects.filter(patient=patient1, side='left')
        right_nfz_all = NFZ_Confirmed.objects.filter(
            patient=patient1, side='right')
        self.assertEqual(len(left_nfz_all), 2)
        self.assertEqual(len(right_nfz_all), 2)
        self.assertEqual(str(left_nfz_all.last().date), '2001-01-01')
        self.assertEqual(str(right_nfz_all.last().date), '2001-01-02')


    def test_remove_NFZ(self):
        patient1 = Patient.objects.get(id=1)
        NFZ_Confirmed.objects.create(patient=patient1,
                                     side='left',
                                     date='2000-01-01')
        NFZ_Confirmed.objects.create(patient=patient1,
                                     side='right',
                                     date='2000-01-02')
        data = self.data.copy()
        data['nfz_left_remove'] = True
        data['nfz_right_remove'] = True
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        left_nfz_all = NFZ_Confirmed.objects.filter(
            patient=patient1, side='left')
        right_nfz_all = NFZ_Confirmed.objects.filter(
            patient=patient1, side='right')
        self.assertEqual(len(left_nfz_all), 1)
        self.assertEqual(len(right_nfz_all), 1)
        self.assertFalse(left_nfz_all.last().in_progress)
        self.assertFalse(right_nfz_all.last().in_progress)


    def test_adding_pcpr_estimates(self):
        patient1 = Patient.objects.get(id=1)
        data = self.data.copy()
        data['left_pcpr_ha'] = 'b1_family1_model1'
        data['right_pcpr_ha'] = 'b1_family1_model2'
        data['left_PCPR_date'] = '2000-01-01'
        data['right_PCPR_date'] = '2000-01-02'
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        left_pcpr_all = PCPR_Estimate.objects.filter(patient=patient1, ear='left')
        right_pcpr_all = PCPR_Estimate.objects.filter(
            patient=patient1, ear='right')
        self.assertEqual(len(left_pcpr_all), 1)
        self.assertEqual(len(right_pcpr_all), 1)
        self.assertEqual(left_pcpr_all.last().ha_model, 'model1')
        self.assertEqual(right_pcpr_all.last().ha_model, 'model2')
        self.assertEqual(str(left_pcpr_all.last().date), '2000-01-01')

    def test_remove_pcpr_estimates(self):
        patient1 = Patient.objects.get(id=1)
        PCPR_Estimate.objects.create(patient=patient1,
            ear='left', ha_make='m', ha_family='f', ha_model='m', date='2000-01-01')
        PCPR_Estimate.objects.create(patient=patient1,
            ear='right', ha_make='m', ha_family='f', ha_model='m', date='2000-01-01')
        data = self.data.copy()
        data['pcpr_left_remove'] = True
        data['pcpr_right_remove'] = True
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        left_pcpr_all = PCPR_Estimate.objects.filter(patient=patient1, ear='left')
        right_pcpr_all = PCPR_Estimate.objects.filter(
            patient=patient1, ear='right')
        self.assertEqual(len(left_pcpr_all), 1)
        self.assertEqual(len(right_pcpr_all), 1)
        self.assertFalse(left_pcpr_all.last().in_progress)
        self.assertFalse(right_pcpr_all.last().in_progress)

    def test_adding_invoice(self):
        patient1 = Patient.objects.get(id=1)
        data = self.data.copy()
        data['left_invoice_ha'] = 'b1_family1_model1'
        data['right_invoice_ha'] = 'b1_family1_model2'
        data['left_invoice_date'] = '2000-01-01'
        data['right_invoice_date'] = '2000-01-02'
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        left_invoice_all = HA_Invoice.objects.filter(
            patient=patient1, ear='left')
        right_invoice_all = HA_Invoice.objects.filter(
            patient=patient1, ear='right')
        self.assertEqual(len(left_invoice_all), 1)
        self.assertEqual(len(right_invoice_all), 1)
        self.assertEqual(left_invoice_all.last().ha_model, 'model1')
        self.assertEqual(right_invoice_all.last().ha_model, 'model2')
        self.assertEqual(str(left_invoice_all.last().date), '2000-01-01')


    def test_remove_invoice(self):
        patient1 = Patient.objects.get(id=1)
        HA_Invoice.objects.create(patient=patient1,
                                     ear='left', ha_make='m', ha_family='f', ha_model='m', date='2000-01-01')
        HA_Invoice.objects.create(patient=patient1,
                                     ear='right', ha_make='m', ha_family='f', ha_model='m', date='2000-01-01')
        data = self.data.copy()
        data['left_invoice_remove'] = True
        data['right_invoice_remove'] = True
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        left_invoice_all = HA_Invoice.objects.filter(
            patient=patient1, ear='left')
        right_invoice_all = HA_Invoice.objects.filter(
            patient=patient1, ear='right')
        self.assertEqual(len(left_invoice_all), 1)
        self.assertEqual(len(right_invoice_all), 1)
        self.assertFalse(left_invoice_all.last().in_progress)
        self.assertFalse(right_invoice_all.last().in_progress)

    def test_collection_procedure(self):
        patient1 = Patient.objects.get(id=1)
        NFZ_Confirmed.objects.create(patient=patient1,
                                     side='left',
                                     date='2000-01-01')
        NFZ_Confirmed.objects.create(patient=patient1,
                                     side='right',
                                     date='2000-01-02')
        PCPR_Estimate.objects.create(patient=patient1,
            ear='left', ha_make='m', ha_family='f', ha_model='m', date='2000-01-01')
        PCPR_Estimate.objects.create(patient=patient1,
            ear='right', ha_make='m', ha_family='f', ha_model='m', date='2000-01-01')
        HA_Invoice.objects.create(patient=patient1,
                                  ear='left', ha_make='m', ha_family='f', ha_model='m1', date='2000-01-01')
        HA_Invoice.objects.create(patient=patient1,
                                  ear='right', ha_make='m', ha_family='f', ha_model='m2', date='2000-01-01')
        data = self.data.copy()
        data['left_collection_confirm'] = True
        data['right_collection_confirm'] = True
        data['left_collection_date'] = '2001-01-01'
        data['right_collection_date'] = '2001-01-02'
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        # should create left and right Hearing_Aid instance
        left_ha = Hearing_Aid.objects.filter(patient=patient1, ear='left').first()
        self.assertEqual(left_ha.ha_model, 'm1')
        self.assertEqual(str(left_ha.purchase_date), '2001-01-01')

        right_ha = Hearing_Aid.objects.filter(patient=patient1, ear='right').first()
        self.assertEqual(right_ha.ha_model, 'm2')
        self.assertEqual(str(right_ha.purchase_date), '2001-01-02')

        # should set NFZ confirmed to inactive
        left_nfz_all = NFZ_Confirmed.objects.filter(
            patient=patient1, side='left')
        right_nfz_all = NFZ_Confirmed.objects.filter(
            patient=patient1, side='right')
        self.assertFalse(left_nfz_all.last().in_progress)
        self.assertFalse(right_nfz_all.last().in_progress)

        # should set PCPR estimates to inactive
        left_pcpr_all = PCPR_Estimate.objects.filter(
            patient=patient1, ear='left')
        right_pcpr_all = PCPR_Estimate.objects.filter(
            patient=patient1, ear='right')
        self.assertFalse(left_pcpr_all.last().in_progress)
        self.assertFalse(right_pcpr_all.last().in_progress)

        # should set invoices to inactive
        left_invoice_all = HA_Invoice.objects.filter(
            patient=patient1, ear='left')
        right_invoice_all = HA_Invoice.objects.filter(
            patient=patient1, ear='right')
        self.assertFalse(left_invoice_all.last().in_progress)
        self.assertFalse(right_invoice_all.last().in_progress)

    def test_remove_audiogram(self):
        patient1 = Patient.objects.get(id=1)
        Audiogram.objects.create(patient=patient1, ear='left')
        
        data = self.data.copy()
        data['remove_audiogram'] = 'remove'
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        left_audiogram_all = Audiogram.objects.filter(
            patient=patient1, ear='left')
        right_audiogram_all = Audiogram.objects.filter(
            patient=patient1, ear='right')
        
        self.assertEqual(len(left_audiogram_all), 0)
        self.assertEqual(len(right_audiogram_all), 0)


class TestDeleteView(TestCase):

    def test_setup(self):
        patient = Patient.objects.create(first_name='a', last_name='b')
        url = reverse('crm:deleteconfirm', args=(1,))
        response = self.client.get(url)
        assert response.status_code == 200, 'Should be callable by anyone'

class TestDeletePatientView(TestCase):
    
    def test_setup(self):
        patient = Patient.objects.create(first_name='a', last_name='b')
        url = reverse('crm:delete', args=(1,))
        expected_url = reverse('crm:index')
        response = self.client.post(url,follow=True)
        assert response.status_code == 200, 'Should redirect'
        # should redirect to expected_url
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)
        # patient should have been deleted
        self.assertFalse(Patient.objects.all().exists())

