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

from crm.models import Patient, Hearing_Aid

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
	                                    ear = 'left')
        ha2 = Hearing_Aid.objects.create(patient = Patient.objects.get(id=2),
                                        ha_make = 'Bernafon',
	                                    ha_family = 'WIN',
	                                    ha_model = '102',
	                                    ear = 'left')
        ha3 = Hearing_Aid.objects.create(patient = Patient.objects.get(id=3),
                                        ha_make = 'Phonak',
	                                    ha_family = 'Naida Q',
	                                    ha_model = '30 SP',
	                                    ear = 'left')
    
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