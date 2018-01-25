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

from crm.models import Patient

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
        patient4 = Patient.objects.create(first_name = 'John', last_name = 'Smith4',
            date_of_birth=today-timedelta(days=3))
        patient4.create_date=now-timedelta(days=3)
        patient4.save()
    
    def test_search_last_name(self):
        '''should return one patient with last name: Smith3'''
        data={'lname': 'Smith3'}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 1)
        response_patient_last_name = response.context['patient_list'][0].last_name
        self.assertEqual(response_patient_last_name, 'Smith3')