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

from crm.models import Patient, Hearing_Aid, NFZ_Confirmed, PCPR_Estimate

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
        # admin = User.objects.create_user(is_staff=True,
        #                                 username='adminuser', 
        #                                 email='oo@gmail.com',
        #                                 password='somepass')

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
        self.assertIsNotNone(response.context['right_NFZ_confirmed'])
        self.assertEqual(response.context['right_NFZ_confirmed'], nfz3)

    def test_patient_with_only_inactive_PCPR_Estimate(self):
        ''' scenario with only inactive (in_progres=False) latest (.last()) PCPR_Estimate
        instances '''
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
        self.assertIsNone(response.context['right_PCPR_estimate'])

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
        self.assertEqual(response.context['right_PCPR_estimate'], pcpr3)


        # there are only inactive (in_progres=False) latest (.last()) PCPR_Estimate instances

        # there is left active (in_progres=True) latest (.last()) PCPR_Estimate instance

        # there are only inactive (in_progres=False) latest (.last()) HA_Invoice instances

        # there is left active (in_progres=True) latest (.last()) HA_Invoice instance