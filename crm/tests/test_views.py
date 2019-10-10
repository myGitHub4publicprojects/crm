# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.contrib import auth
from django.core.paginator import Paginator
from django.contrib.messages import get_messages
from mixer.backend.django import mixer

import os
import pytest
import shutil
import tempfile

from django.conf import settings
from django.core.files import File
from datetime import datetime, timedelta
from django.contrib.staticfiles.templatetags.staticfiles import static

from crm.models import (Patient, NewInfo, PCPR_Estimate, Invoice,
                     Hearing_Aid, Hearing_Aid_Stock, Other_Item, Other_Item_Stock,
                     NFZ_Confirmed, NFZ_New, Reminder_Collection, Reminder_Invoice,
                     Reminder_PCPR, Reminder_NFZ_Confirmed, Reminder_NFZ_New,
                        SZOI_File, SZOI_File_Usage, SZOI_Errors, Corrective_Invoice)

pytestmark = pytest.mark.django_db
today = datetime.today().date()
now = datetime.now()


def create_user(username='john', email='jlennon@beatles.com', password='glassonion'):
    return User.objects.create_user(username=username, email=email, password=password)


def create_patient(audiometrist,    first_name='John', 
                                    last_name='Smith1',
                                    date_of_birth=None):
    return Patient.objects.create(  first_name=first_name,
                                    last_name=last_name,
                                    audiometrist=audiometrist,
                                    date_of_birth=date_of_birth)
class TestIndexView(TestCase):
    def setUp(self):
        user_john = create_user()
        patient1 = create_patient(user_john)
        patient2 = create_patient(user_john, date_of_birth=today-timedelta(days=1))
        patient3 = create_patient(user_john, date_of_birth=today-timedelta(days=2))
        patient4 = create_patient(user_john, date_of_birth=today-timedelta(days=3))
        patient4.create_date = now-timedelta(days=3)
        patient4.save()


    def test_anonymous(self):
        url = reverse('crm:index')
        expected_url = reverse('login') + '?next=/'
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)


    def test_logged_in(self):
        self.client.login(username='john', password='glassonion')
        url = reverse('crm:index')
        response = self.client.get(url)
        all_patients = Patient.objects.all()
        assert response.status_code == 200, 'Should be callable by logged in user'
        self.assertEqual(len(response.context['patients']), 4)

    def test_order_by_date_of_birth(self):
        '''should sort patients based on date of birth, starting from those without
        a specified date, then oldest to youngest'''
        self.client.login(username='john', password='glassonion')
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
        self.client.login(username='john', password='glassonion')
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
        self.client.login(username='john', password='glassonion')
        data={'q': 'Smith'}
        url = reverse('crm:index')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patients']), 4)

    def test_pagination_page_over_9999(self):
        self.client.login(username='john', password='glassonion')
        data = {'page': '99999'}
        url = reverse('crm:index')
        response = self.client.get(url, data)
        # should show last page (1)
        self.assertEqual(response.context['patients'].paginator.num_pages, 1)

class TestAdvancedSearchView(TestCase):
    def setUp(self):
        user_john = create_user()
        patient1 = create_patient(user_john, first_name='Adam', last_name='Smith1')
        patient2 = create_patient(user_john, first_name='John', last_name='Smith2')
        patient3 = create_patient(user_john, first_name='John', last_name='Smith3')
        patient4 = create_patient(user_john, first_name='John',
            last_name='Smith4', date_of_birth=today-timedelta(days=3))

        patient4.location = 'Mosina'
        patient4.save()

        ha1 = Hearing_Aid.objects.create(patient = Patient.objects.get(id=1),
                            make = 'Bernafon',
                            family = 'WIN',
                            model = '102',
                            ear = 'left',
                            purchase_date = '2000-01-01')
        ha2 = Hearing_Aid.objects.create(patient = Patient.objects.get(id=2),
                            make='Bernafon',
                            family='WIN',
                            model='102',
                            ear = 'left',
                            purchase_date = '2010-01-01')
        ha3 = Hearing_Aid.objects.create(patient = Patient.objects.get(id=3),
                            make = 'Phonak',
                            family = 'Naida Q',
                            model = '30 SP',
                            ear = 'left',
                            purchase_date = '2016-01-01')
    
    def test_search_last_name(self):
        '''should return one patient with last name: Smith3'''
        self.client.login(username='john', password='glassonion')
        data={'lname': 'Smith3'}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 1)
        response_patient_last_name = response.context['patient_list'][0].last_name
        self.assertEqual(response_patient_last_name, 'Smith3')

    def test_search_first_name(self):
        '''should return one patient with first name: Adam'''
        self.client.login(username='john', password='glassonion')
        data={'fname': 'Adam'}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 1)
        response_patient_first_name = response.context['patient_list'][0].first_name
        self.assertEqual(response_patient_first_name, 'Adam')

    def test_search_location(self):
        '''should return one patient with location: Mosina'''
        self.client.login(username='john', password='glassonion')
        data={'loc': 'Mosina'}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 1)
        response_patient_location = response.context['patient_list'][0].location
        self.assertEqual(response_patient_location, 'Mosina')

    def test_search_hearing_aid_make(self):
        '''should return patients wearing hearing aids by Bernafon (2)'''
        self.client.login(username='john', password='glassonion')
        ha1 = Hearing_Aid.objects.get(id=1)
        ha2 = Hearing_Aid.objects.get(id=2)
        ha3 = Hearing_Aid.objects.get(id=3)
        data={'ha_make': 'Bernafon'}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 2)

    def test_search_hearing_aid_make_family_model(self):
        '''should return patients wearing Phonak Naida Q 30 SP aid (1)'''
        self.client.login(username='john', password='glassonion')
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
        self.client.login(username='john', password='glassonion')
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
        self.client.login(username='john', password='glassonion')
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
        self.client.login(username='john', password='glassonion')
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
        self.client.login(username='john', password='glassonion')
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

    def test_search_nfz_new_date_only_lower_band(self):
        '''only lower band of dates is given - upper band should default to today
        should return only patients with nfz new after the lower band date'''
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        patient2 = Patient.objects.get(id=2)
        patient3 = Patient.objects.get(id=3)
        patient4 = Patient.objects.get(id=4)
        # date out of range
        NFZ_New.objects.create(
            patient=patient1, date='2001-01-01', side='left')
        NFZ_New.objects.create(
            patient=patient2, date='2002-01-01', side='left')
        NFZ_New.objects.create(
            patient=patient3, date='2003-01-01', side='left')
        # inactive
        NFZ_New.objects.create(patient=patient4, date='2002-01-01', side='left',
                               in_progress=False)
        lower_band = '2002-01-01'
        data = {'s_nfz_new_date': lower_band}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 2)

    def test_search_nfz_new_by_date_both_lower_and_upper_band(self):
        '''both lower and upper band of dates is given, should return only patients
        with NFZ new after the lower band and before the upper band date'''
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        patient2 = Patient.objects.get(id=2)
        patient3 = Patient.objects.get(id=3)
        NFZ_New.objects.create(patient=patient1, date='2001-01-01', side='left')
        NFZ_New.objects.create(patient=patient2, date='2001-01-01', side='left')
        NFZ_New.objects.create(patient=patient1, date='2002-01-01', side='left')
        # date out of range
        NFZ_New.objects.create(patient=patient3, date='2003-01-01', side='left')
        # inactive
        NFZ_New.objects.create(patient=patient3, date='2002-01-01', side='left',
                                        in_progress=False)
        lower_band = '2000-01-01'
        upper_band = '2002-01-02'
        data={'s_nfz_new_date': lower_band, 'e_nfz_new_date': upper_band}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 2)


    def test_search_pcpr_estimate_date_both_lower_and_upper_band(self):
        '''both lower and upper band of dates is given, should return only patients
        with NFZ confirmed after the lower band and before the upper band date'''
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        patient2 = Patient.objects.get(id=2)
        patient3 = Patient.objects.get(id=3)

        pcpr1 = PCPR_Estimate.objects.create(
            patient=patient1,
            current=True,)
        pcpr1.timestamp = '2000-01-01 00:00:00'
        pcpr1.save()
        
        pcpr2 = PCPR_Estimate.objects.create(
            patient=patient2,
            current=True,)
        pcpr2.timestamp = '2002-01-01 00:00:00'
        pcpr2.save()

        pcpr3 = PCPR_Estimate.objects.create(
            patient=patient3,
            current=True,)
        pcpr3.timestamp = '2003-01-01 00:00:00'
        pcpr3.save()

        lower_band = '2001-01-01'
        upper_band = '2003-01-01'
        data = {'s_pcpr_date': lower_band, 'e_pcpr_date': upper_band}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 2)

    def test_search_ha_invoice_date_both_lower_and_upper_band(self):
        '''both lower and upper band of dates is given, should return only patients
        with NFZ confirmed after the lower band and before the upper band date'''
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        patient2 = Patient.objects.get(id=2)
        patient3 = Patient.objects.get(id=3)

        invoice1 = Invoice.objects.create(
            patient=patient1,
            payed=True,
            type='cash',
            current=True,)
        invoice1.timestamp = '2000-01-01 00:00:00'
        invoice1.save()
        
        invoice2 = Invoice.objects.create(
            patient=patient2,
            payed=True,
            type='cash',
            current=True,)
        invoice2.timestamp = '2002-01-01 00:00:00'
        invoice2.save()

        invoice3 = Invoice.objects.create(
            patient=patient3,
            payed=True,
            type='cash',
            current=True,)
        invoice3.timestamp = '2003-01-01 00:00:00'
        invoice3.save()

        lower_band = '2000-01-01'
        upper_band = '2002-01-02'
        data = {'s_invoice_date': lower_band, 'e_invoice_date': upper_band}
        url = reverse('crm:advanced_search')
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['patient_list']), 2)

class TestCreateView(TestCase):
    def test_anonymous(self):
        url = reverse('crm:create')
        expected_url = reverse('login') + '?next=/create/'
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

    def test_logged_in(self):
        create_user()
        self.client.login(username='john', password='glassonion')
        url = reverse('crm:create')
        response = self.client.post(url)
        assert response.status_code == 200


class TestEditView(TestCase):
    def setUp(self):
        user_john = create_user()
        patient1 = create_patient(user_john)
        patient2 = create_patient(user_john,
            date_of_birth=today-timedelta(days=1), last_name = 'Smith2')
        patient3 = create_patient(user_john,
            date_of_birth=today-timedelta(days=2), last_name='Smith3')
    def test_anonymous(self):
        '''should redirect to login'''
        patient1 = Patient.objects.get(id=1)
        url = reverse('crm:edit', args=(patient1.id,))
        expected_url = reverse('login') + '?next=/' + str(patient1.id) + '/edit/'
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

    def test_logged_in(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        response = self.client.get(reverse('crm:edit', args=(patient1.id,)))
        assert response.status_code == 200, 'Should be callable by logged in user'


    def test_patient_with_both_active_NFZ_new(self):
        ''' scenario with left and right active (in_progres=True)
        latest (.last()) NFZ new instance 
        there are also former, inactive left and right instance'''
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        nfz0 = NFZ_New.objects.create(patient=patient1,
                            date = today,
                            side = 'left',
                            in_progress = False)
        nfz1 = NFZ_New.objects.create(patient=patient1,
                            date = today,
                            side = 'left',
                            in_progress = True)
        nfz2 = NFZ_New.objects.create(patient=patient1,
                            date = today,
                            side = 'right',
                            in_progress = False)
        nfz3 = NFZ_New.objects.create(patient=patient1,
                            date = today,
                            side = 'right',
                            in_progress = True)
        response = self.client.get(reverse('crm:edit', args=(patient1.id,)))
        self.assertIsNotNone(response.context['left_NFZ_new'])
        self.assertEqual(response.context['left_NFZ_new'], nfz1)
        self.assertEqual(len(response.context['left_NFZ_new_all']), 1)
        self.assertIsNotNone(response.context['right_NFZ_new'])
        self.assertEqual(response.context['right_NFZ_new'], nfz3)
        self.assertEqual(len(response.context['right_NFZ_new_all']), 1)


    def test_patient_with_only_inactive_NFZ_confirmed(self):
        ''' scenario with only inactive (in_progres=False) latest (.last()) NFZ confirmed
        instances '''
        self.client.login(username='john', password='glassonion')
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
        self.client.login(username='john', password='glassonion')
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
        self.client.login(username='john', password='glassonion')
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
        ''' scenario with only inactive (current=False) latest PCPR_Estimate
        instances'''
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        pcpr1 = PCPR_Estimate.objects.create(
            patient=patient1,
            current = False)
        pcpr2 = PCPR_Estimate.objects.create(
            patient=patient1,
            current=False)
        response = self.client.get(reverse('crm:edit', args=(patient1.id,)))

        self.assertEqual(len(response.context['PCPR_estimate_all']), 2)


    def test_patient_with_one_active_and_two_inactive_PCPR_Estimate(self):
        ''' scenario with one active and two inactive (current=False)
        latest PCPR_Estimate instances '''
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        pcpr0 = PCPR_Estimate.objects.create(
            patient=patient1,
            current=False)
        pcpr1 = PCPR_Estimate.objects.create(
            patient=patient1,
            current=False)
        pcpr2 = PCPR_Estimate.objects.create(
            patient=patient1,
            current=True)

        response = self.client.get(reverse('crm:edit', args=(patient1.id,)))
        # self.assertEqual(response.context['PCPR_estimate'], pcpr2)
        self.assertEqual(response.context['PCPR_estimate'], pcpr2)
        self.assertEqual(len(response.context['PCPR_estimate_all']),2)

    def test_patient_with_only_inactive_Invoice(self):
        ''' scenario with only inactive (in_progres=False) Invoice instances '''
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        invoice1 = Invoice.objects.create(
            patient=patient1,
            current=False)
        invoice2 = Invoice.objects.create(
            patient=patient1,
            current = False)
        invoice3 = Invoice.objects.create(
            patient=patient1,
            current=False)
        response = self.client.get(reverse('crm:edit', args=(patient1.id,)))

        self.assertEqual(len(response.context['invoice_all']), 3)
        self.assertEqual(len(response.context['invoice_active']), 0)

    def test_patient_with_one_active_and_two_inactive_Invoice(self):
        ''' scenario with one active and two inactive (current=False)
        Invoice instances '''
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        invoice1 = Invoice.objects.create(
            patient=patient1,
            current=False)
        invoice2 = Invoice.objects.create(
            patient=patient1,
            current = False)
        invoice3 = Invoice.objects.create(
            patient=patient1,
            current=True)

        response = self.client.get(reverse('crm:edit', args=(patient1.id,)))
        self.assertEqual(response.context['invoice_active'].count(), 1)
        self.assertEqual(response.context['invoice_all'].count(), 2)


class TestStoreView(TestCase):
    
    def setUp(self):
        create_user()

    def test_anonymous(self):
        url = reverse('crm:store')
        expected_url = reverse('login') + '?next=/store/'
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

    def test_logged_in(self):
        self.client.login(username='john', password='glassonion')
        data = {'fname': 'Adam',
                'lname': 'Atkins',
                'bday': '2000-01-01',
                'usrtel': 1,
                'location': 'some_location',
                'left_ha': 'model1_family1_brand1',
                'right_ha': 'model2_family2_brand2',
                'left_purchase_date': '1999-01-01',
                'right_purchase_date': '1999-01-02',
                'left_NFZ_new': '2001-01-01',
                'right_NFZ_new': '2001-01-01',
                'left_NFZ_confirmed_date': '2001-01-01',
                'right_NFZ_confirmed_date': '2002-02-02',
                'note': 'p1_note',
                'street': 'some_street',
                'house_number': '1',
                'apartment_number': '2',
                'city': 'some_city',
                'zip_code': 'zip_c'
                }

        url = reverse('crm:store')
        # id of new patient should be 1
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                     status_code=302, target_status_code=200)
        self.assertEqual(Patient.objects.all().count(), 1)
        self.assertEqual(NFZ_New.objects.all().count(), 2)
        self.assertEqual(NFZ_Confirmed.objects.all().count(), 2)
        self.assertEqual(Hearing_Aid.objects.all().count(), 2)
        self.assertEqual(Reminder_NFZ_New.objects.all().count(), 2)
        self.assertEqual(Reminder_NFZ_Confirmed.objects.all().count(), 2)


    def test_add_other_left_ha(self):
        ''' should create user with left other ha'''
        self.client.login(username='john', password='glassonion')
        data = {'fname': 'Adam',
                'lname': 'Atkins',
                'bday': '2000-01-01',
                'usrtel': 1,
                'location': 'some_location',
                'left_other_ha': 'Starkey',
                'right_other_ha': 'Beltone virte c g90',
                'street': 'some_street',
                'house_number': '1',
                'apartment_number': '2',
                'city': 'some_city',
                'zip_code': 'zip_c'
                }
        url = reverse('crm:store')
        # id of new patient should be 1
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                     status_code=302, target_status_code=200)
        self.assertEqual(Patient.objects.all().count(), 1)
        self.assertEqual(Hearing_Aid.objects.all().count(), 2)
        patient = Patient.objects.get(id=1)
        left_ha = Hearing_Aid.objects.filter(patient=patient, ear='left')[0]
        right_ha = Hearing_Aid.objects.filter(patient=patient, ear='right')[0]
        self.assertEqual(str(left_ha), 'Starkey inny inny')
        self.assertEqual(str(right_ha), 'Beltone virte_c_g90 inny')



class TestUpdatingView(TestCase):
    data = {'fname': 'Adam',
            'lname': 'Atkins',
            'usrtel': 1,
            'location': 'some_location',
            'summary_note': 'some note',
            'street': 'some_street',
            'house_number': '1',
            'apartment_number': '2',
            'city': 'some_city',
            'zip_code': 'zip_c',
            'NIP': '223322332'
            }
    def setUp(self):
        user_john = create_user()
        patient1 = create_patient(user_john)
        patient2 = create_patient(user_john,
                date_of_birth=today-timedelta(days=1), last_name='Smith2')
        patient3 = create_patient(user_john,
                date_of_birth=today-timedelta(days=2), last_name='Smith3')

    def test_anonymous(self):
        '''should redirect to login'''
        patient1 = Patient.objects.get(id=1)
        url = reverse('crm:edit', args=(patient1.id,))
        expected_url = reverse('login') + '?next=/' + \
            str(patient1.id) + '/edit/'
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)
    
    def test_change_name_tel_location(self):
        self.client.login(username='john', password='glassonion')
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

    def test_add_birth_day_new_note_change_patient_note(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        data = self.data.copy()
        data['summary_note'] = 'summary'
        data['bday'] = '2000-01-01'
        data['new_note'] = 'new note'
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)
        
        new_info = NewInfo.objects.get(id=1)
        patient1.refresh_from_db()
        self.assertEqual(str(patient1.date_of_birth), '2000-01-01')
        self.assertEqual(patient1.notes, 'summary')
        self.assertEqual(new_info.note, 'new note')

    # test adding note or action by other audiometrist
    # should show who created and who added new note
    def test_add_new_note_by_other_audiometrist(self):
        adam = User.objects.create_user(username='adam',
                                email='jlennon@beatles.com',
                                password='oleole')
        john = User.objects.get(id=1)
        self.client.login(username='adam', password='oleole')
        patient1 = Patient.objects.get(id=1)
        data = self.data.copy()
        data['new_note'] = 'some new info'
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        patient1.refresh_from_db()
        new_info = NewInfo.objects.get(id=1)
        # audiometrist who created the patient
        self.assertEqual(patient1.audiometrist, john)
        self.assertEqual(new_info.note, 'some new info')
        # audiometrist who added new note
        self.assertEqual(new_info.audiometrist, adam)



    def test_adding_hearing_aids_by_other_audiometrist(self):
        adam = User.objects.create_user(username='adam',
                                        email='jlennon@beatles.com',
                                        password='oleole')
        self.client.login(username='adam', password='oleole')
        patient1 = Patient.objects.get(id=1)
        Hearing_Aid.objects.create(patient=patient1,
                                    ear='left',
                                    make='m',
                                    family='f',
                                    model='m1',
                                   pkwiu_code='26.60.14')
        Hearing_Aid.objects.create(patient=patient1,
                                    ear='right',
                                    make='m',
                                    family='f',
                                    model='m2',
                                   pkwiu_code='26.60.14')
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
        self.assertEqual(left_ha_all.count(), 2)
        self.assertEqual(right_ha_all.count(), 2)
        self.assertEqual(left_ha_all.last().model, 'model1')
        self.assertEqual(right_ha_all.last().model, 'model2')
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Dodano lewy aparat b1 family1 model1. ' + \
                        'Dodano prawy aparat b2 family2 model2.'

        self.assertEqual(new_info.note, expected_note)
        self.assertEqual(new_info.audiometrist, adam)
        
        # previous hearing aids should be inactivated (current=False)
        previous_left = left_ha_all.get(model='m1')
        self.assertFalse(previous_left.current)
        previous_right = right_ha_all.get(model='m2')
        self.assertFalse(previous_right.current)

        # new hearing aids should be active (current=True)
        new_left = left_ha_all.get(model='model1')
        self.assertTrue(new_left.current)
        new_right = right_ha_all.get(model='model2')
        self.assertTrue(new_right.current)

    def test_adding_another_hearing_aids_with_purchase_dates(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        Hearing_Aid.objects.create(patient=patient1,
                                    ear='left',
                                    make='m',
                                    family='f',
                                    model='m1',
                                   pkwiu_code='26.60.14')
        Hearing_Aid.objects.create(patient=patient1,
                                    ear='right',
                                    make='m',
                                    family='f',
                                    model='m2',
                                   pkwiu_code='26.60.14')
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
        self.assertEqual(left_ha_all.count(), 2)
        self.assertEqual(right_ha_all.count(), 2)
        self.assertEqual(left_ha_all.last().model, 'model1')
        self.assertEqual(right_ha_all.last().model, 'model2')
        self.assertEqual(str(left_ha_all.last().purchase_date), '2001-01-01')
        self.assertEqual(str(right_ha_all.last().purchase_date), '2001-01-02')
        self.assertFalse(left_ha_all.last().our)
                
        # previous hearing aids should be inactivated (current=False)
        previous_left = left_ha_all.get(model='m1')
        self.assertFalse(previous_left.current)
        previous_right = right_ha_all.get(model='m2')
        self.assertFalse(previous_right.current)

        # new hearing aids should be active (current=True)
        new_left = left_ha_all.get(model='model1')
        self.assertTrue(new_left.current)
        new_right = right_ha_all.get(model='model2')
        self.assertTrue(new_right.current)

    def test_adding_other_hearing_aids_with_text_input_names(self):
        '''user inputs name of hearing aid in text field'''
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        data = self.data.copy()
        data['left_other_ha'] = 'Starkey'
        data['right_other_ha'] = 'Beltona iic virto t70'
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

        left_ha = Hearing_Aid.objects.filter(patient=patient1, ear='left')[0]
        right_ha = Hearing_Aid.objects.filter(patient=patient1, ear='right')[0]
        self.assertEqual(str(left_ha), 'Starkey inny inny')
        self.assertEqual(str(right_ha), 'Beltona iic_virto_t70 inny')
        self.assertEqual(str(left_ha.purchase_date), '2001-01-01')
        self.assertEqual(str(right_ha.purchase_date), '2001-01-02')
        self.assertFalse(left_ha.our)

    def test_adding_NFZ_new(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        data = self.data.copy()
        data['new_NFZ_left'] = '2001-01-01'
        data['new_NFZ_right'] = '2001-01-02'
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        left_nfz_all = NFZ_New.objects.filter(
            patient=patient1, side='left')
        right_nfz_all = NFZ_New.objects.filter(
            patient=patient1, side='right')
        self.assertEqual(left_nfz_all.count(), 1)
        self.assertEqual(right_nfz_all.count(), 1)
        self.assertEqual(str(left_nfz_all.last().date), '2001-01-01')
        self.assertEqual(str(right_nfz_all.last().date), '2001-01-02')
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Dodano niepotwierdzony lewy wniosek z datą 2001-01-01. ' + \
                        'Dodano niepotwierdzony prawy wniosek z datą 2001-01-02.'
        reminders = Reminder_NFZ_New.objects.all()
        self.assertEqual(reminders.count(), 2)
        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

    def test_adding_another_NFZ_new(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        n1 = NFZ_New.objects.create(patient=patient1,
                                          side='left',
                                          date='2000-01-01')
        n2 = NFZ_New.objects.create(patient=patient1,
                                          side='right',
                                          date='2000-01-02')
        Reminder_NFZ_New.objects.create(nfz_new=n1, activation_date=today)
        Reminder_NFZ_New.objects.create(nfz_new=n2, activation_date=today)
        data = self.data.copy()
        data['new_NFZ_left'] = '2001-01-01'
        data['new_NFZ_right'] = '2001-01-02'
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        left_nfz_all = NFZ_New.objects.filter(
            patient=patient1, side='left')
        right_nfz_all = NFZ_New.objects.filter(
            patient=patient1, side='right')
        self.assertEqual(left_nfz_all.count(), 2)
        self.assertEqual(right_nfz_all.count(), 2)
        self.assertEqual(str(left_nfz_all.last().date), '2001-01-01')
        self.assertEqual(str(right_nfz_all.last().date), '2001-01-02')
        self.assertEqual(response.context['reminders'], 2)

    def test_remove_NFZ_New(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        n1 = NFZ_New.objects.create(patient=patient1,
                                          side='left',
                                          date='2000-01-01')
        n2 = NFZ_New.objects.create(patient=patient1,
                                          side='right',
                                          date='2000-01-02')
        Reminder_NFZ_New.objects.create(nfz_new=n1)
        Reminder_NFZ_New.objects.create(nfz_new=n2)
        data = self.data.copy()
        data['nfz_new_left_remove'] = True
        data['nfz_new_right_remove'] = True
        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        left_nfz_all = NFZ_New.objects.filter(
            patient=patient1, side='left')
        right_nfz_all = NFZ_New.objects.filter(
            patient=patient1, side='right')
        self.assertEqual(left_nfz_all.count(), 1)
        self.assertEqual(right_nfz_all.count(), 1)
        self.assertFalse(left_nfz_all.last().in_progress)
        self.assertFalse(right_nfz_all.last().in_progress)
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Usunięto lewy niepotwierdzony wniosek z datą 2000-01-01. ' + \
                        'Usunięto prawy niepotwierdzony wniosek z datą 2000-01-02.'

        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

        # should inactivate 2 Reminder.nfz_new
        left_nfz_new_all = NFZ_New.objects.filter(
            patient=patient1, side='left')
        right_nfz_new_all = NFZ_New.objects.filter(
            patient=patient1, side='right')
        left_new_nfz = left_nfz_new_all[0]
        right_new_nfz = right_nfz_new_all[0]
        left_new_reminders = Reminder_NFZ_New.objects.filter(
            nfz_new=left_new_nfz)
        self.assertEqual(left_new_reminders.count(), 1)
        right_new_reminders = Reminder_NFZ_New.objects.filter(
            nfz_new=right_new_nfz)
        self.assertEqual(right_new_reminders.count(), 1)
        self.assertFalse(left_new_reminders.last().active)
        self.assertFalse(right_new_reminders.last().active)

        # there should be 2 Reminders in total (2 inactive)
        reminders = Reminder_NFZ_New.objects.all()
        self.assertEqual(reminders.count(), 2)

    def test_adding_NFZ_confirmed_no_NFZ_New(self):
        self.client.login(username='john', password='glassonion')
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
        self.assertEqual(left_nfz_all.count(), 1)
        self.assertEqual(right_nfz_all.count(), 1)
        self.assertEqual(str(left_nfz_all.last().date), '2001-01-01')
        self.assertEqual(str(right_nfz_all.last().date), '2001-01-02')
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Dodano potwierdzony lewy wniosek z datą 2001-01-01. ' + \
                        'Dodano potwierdzony prawy wniosek z datą 2001-01-02.'
        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

        # should create 2 reminders (Reminder.nfz_confirmed)
        left_nfz = left_nfz_all[0]
        right_nfz = right_nfz_all[0]
        left_reminder = Reminder_NFZ_Confirmed.objects.filter(nfz_confirmed=left_nfz)
        self.assertEqual(left_reminder.count(), 1)
        right_reminder = Reminder_NFZ_Confirmed.objects.filter(nfz_confirmed=right_nfz)
        self.assertEqual(right_reminder.count(), 1)
        reminders = Reminder_NFZ_Confirmed.objects.all()
        self.assertEqual(reminders.count(), 2)
        

    def test_adding_NFZ_confirmed_previous_NFZ_New(self):
        '''confirmed NFZ are added where NFZ_New instances already exists,
        reminders about NFZ_New should be deactivated'''
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        n1 = NFZ_New.objects.create(patient=patient1,
                                   side='left',
                                   date='2000-01-01')
        n2 = NFZ_New.objects.create(patient=patient1,
                                     side='right',
                                     date='2000-01-02')
        Reminder_NFZ_New.objects.create(nfz_new=n1, activation_date=today)
        Reminder_NFZ_New.objects.create(nfz_new=n2, activation_date=today)
        data = self.data.copy()
        data['NFZ_left'] = '2001-01-01'
        data['NFZ_right'] = '2001-01-02'
        url = reverse('crm:updating', args=(patient1.id,))
        response = self.client.post(url, data, follow=True)
       
        left_nfz_confirmed_all = NFZ_Confirmed.objects.filter(
            patient=patient1, side='left')
        right_nfz_confirmed_all = NFZ_Confirmed.objects.filter(
            patient=patient1, side='right')
        self.assertEqual(left_nfz_confirmed_all.count(), 1)
        self.assertEqual(right_nfz_confirmed_all.count(), 1)
        self.assertEqual(str(left_nfz_confirmed_all.last().date), '2001-01-01')
        self.assertEqual(str(right_nfz_confirmed_all.last().date), '2001-01-02')

        # should inactivate 2 Reminder.nfz_new
        left_nfz_new_all = NFZ_New.objects.filter(
            patient=patient1, side='left')
        right_nfz_new_all = NFZ_New.objects.filter(
            patient=patient1, side='right')
        left_new_nfz = left_nfz_new_all[0]
        right_new_nfz = right_nfz_new_all[0]
        left_new_reminders = Reminder_NFZ_New.objects.filter(
            nfz_new=left_new_nfz)
        self.assertEqual(left_new_reminders.count(), 1)
        right_new_reminders = Reminder_NFZ_New.objects.filter(
            nfz_new=right_new_nfz)
        self.assertEqual(right_new_reminders.count(), 1)
        self.assertFalse(left_new_reminders.last().active)
        self.assertFalse(right_new_reminders.last().active)

        # and create 2 Reminder.nfz_confirmed (active)
        left_confirmed_nfz = left_nfz_confirmed_all[0]
        right_confirmed_nfz = right_nfz_confirmed_all[0]
        left_confirmed_reminders = Reminder_NFZ_Confirmed.objects.filter(
            nfz_confirmed=left_confirmed_nfz)
        self.assertEqual(left_confirmed_reminders.count(), 1)
        right_confirmed_reminders = Reminder_NFZ_Confirmed.objects.filter(
            nfz_confirmed=right_confirmed_nfz)
        self.assertEqual(right_confirmed_reminders.count(), 1)
        self.assertTrue(left_confirmed_reminders.last().active)
        self.assertTrue(right_confirmed_reminders.last().active)

        # there should be 2 Reminder_NFZ_Confirmed
        reminders = Reminder_NFZ_Confirmed.objects.all()
        self.assertEqual(reminders.count(), 2)


    def test_adding_another_NFZ_confirmed(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        n1 = NFZ_Confirmed.objects.create(patient=patient1,
                                   side='left',
                                   date='2000-01-01')
        n2 = NFZ_Confirmed.objects.create(patient=patient1,
                                     side='right',
                                     date='2000-01-02')
        Reminder_NFZ_Confirmed.objects.create(nfz_confirmed=n1, activation_date=today)
        Reminder_NFZ_Confirmed.objects.create(nfz_confirmed=n2, activation_date=today)
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
        self.assertEqual(left_nfz_all.count(), 2)
        self.assertEqual(right_nfz_all.count(), 2)
        self.assertEqual(str(left_nfz_all.last().date), '2001-01-01')
        self.assertEqual(str(right_nfz_all.last().date), '2001-01-02')
        self.assertEqual(response.context['reminders'],2)


    def test_remove_NFZ_Confirmed(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        n1 = NFZ_Confirmed.objects.create(patient=patient1,
                                     side='left',
                                     date='2000-01-01')
        n2 = NFZ_Confirmed.objects.create(patient=patient1,
                                     side='right',
                                     date='2000-01-02')
        Reminder_NFZ_Confirmed.objects.create(nfz_confirmed=n1)
        Reminder_NFZ_Confirmed.objects.create(nfz_confirmed=n2)
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

        left_nfz_confirmed_all = NFZ_Confirmed.objects.filter(
            patient=patient1, side='left')
        right_nfz_confirmed_all = NFZ_Confirmed.objects.filter(
            patient=patient1, side='right')
        self.assertEqual(left_nfz_confirmed_all.count(), 1)
        self.assertEqual(right_nfz_confirmed_all.count(), 1)
        self.assertFalse(left_nfz_confirmed_all.last().in_progress)
        self.assertFalse(right_nfz_confirmed_all.last().in_progress)
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Usunięto lewy wniosek z datą 2000-01-01. ' + \
                        'Usunięto prawy wniosek z datą 2000-01-02.'

        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

        # should inactivate 2 Reminder.nfz_confirmed
        left_nfz_confirmed_all = NFZ_Confirmed.objects.filter(
            patient=patient1, side='left')
        right_nfz_confirmed_all = NFZ_Confirmed.objects.filter(
            patient=patient1, side='right')
        left_confirmed_nfz = left_nfz_confirmed_all[0]
        right_confirmed_nfz = right_nfz_confirmed_all[0]
        left_confirmed_reminders = Reminder_NFZ_Confirmed.objects.filter(
            nfz_confirmed=left_confirmed_nfz)
        self.assertEqual(left_confirmed_reminders.count(), 1)
        right_confirmed_reminders = Reminder_NFZ_Confirmed.objects.filter(
            nfz_confirmed=right_confirmed_nfz)
        self.assertEqual(right_confirmed_reminders.count(), 1)
        self.assertFalse(left_confirmed_reminders.last().active)
        self.assertFalse(right_confirmed_reminders.last().active)

        # there should be 2 Reminders in total (2 inactive)
        reminders = Reminder_NFZ_Confirmed.objects.all()
        self.assertEqual(reminders.count(), 2)


#     def test_adding_pcpr_estimates(self):
#         self.client.login(username='john', password='glassonion')
#         patient1 = Patient.objects.get(id=1)
#         n1 = NFZ_New.objects.create(patient=patient1,
#                                     side='left',
#                                     date='2000-01-01')
#         n2 = NFZ_New.objects.create(patient=patient1,
#                                     side='right',
#                                     date='2000-01-02')
#         Reminder.objects.create(nfz_new=n1, activation_date=today)
#         Reminder.objects.create(nfz_new=n2, activation_date=today)

#         n1 = NFZ_Confirmed.objects.create(patient=patient1,
#                                      side='left',
#                                      date='2000-01-01')
#         n2 = NFZ_Confirmed.objects.create(patient=patient1,
#                                      side='right',
#                                      date='2000-01-02')
#         Reminder.objects.create(nfz_confirmed=n1)
#         Reminder.objects.create(nfz_confirmed=n2)


#         data = self.data.copy()
#         data['left_pcpr_ha'] = 'b1_family1_model1'
#         data['right_pcpr_ha'] = 'b2_family2_model2'
#         data['left_PCPR_date'] = '2000-01-01'
#         data['right_PCPR_date'] = '2000-01-02'
#         url = reverse('crm:updating', args=(patient1.id,))
#         expected_url = reverse('crm:edit', args=(1,))
#         response = self.client.post(url, data, follow=True)
#         # should give code 200 as follow is set to True
#         assert response.status_code == 200
#         self.assertRedirects(response, expected_url,
#                              status_code=302, target_status_code=200)

#         left_pcpr_all = PCPR_Estimate.objects.filter(patient=patient1, ear='left')
#         right_pcpr_all = PCPR_Estimate.objects.filter(
#             patient=patient1, ear='right')
#         self.assertEqual(len(left_pcpr_all), 1)
#         self.assertEqual(len(right_pcpr_all), 1)
#         self.assertEqual(left_pcpr_all.last().ha_model, 'model1')
#         self.assertEqual(right_pcpr_all.last().ha_model, 'model2')
#         self.assertEqual(str(left_pcpr_all.last().date), '2000-01-01')
#         new_info = NewInfo.objects.get(id=1)
#         expected_note = 'Dodano lewy kosztorys na b1 family1 model1, z datą 2000-01-01. ' + \
#                         'Dodano prawy kosztorys na b2 family2 model2, z datą 2000-01-02.'

#         self.assertEqual(new_info.note, expected_note.decode('utf-8'))

#         # reminders
#         # should inactivate Reminder.nfz_new and Reminder.nfz_confirmed if any
#         left_nfz_new_all = NFZ_New.objects.filter(
#             patient=patient1, side='left')
#         right_nfz_new_all = NFZ_New.objects.filter(
#             patient=patient1, side='right')
#         left_new_nfz = left_nfz_new_all[0]
#         right_new_nfz = right_nfz_new_all[0]
#         left_new_reminders = Reminder.objects.filter(
#             nfz_new=left_new_nfz)
#         self.assertEqual(len(left_new_reminders), 1)
#         right_new_reminders = Reminder.objects.filter(
#             nfz_new=right_new_nfz)
#         self.assertEqual(len(right_new_reminders), 1)
#         self.assertFalse(left_new_reminders.last().active)
#         self.assertFalse(right_new_reminders.last().active)

#         left_nfz_confirmed_all = NFZ_Confirmed.objects.filter(
#             patient=patient1, side='left')
#         right_nfz_confirmed_all = NFZ_Confirmed.objects.filter(
#             patient=patient1, side='right')
#         left_confirmed_nfz = left_nfz_confirmed_all[0]
#         right_confirmed_nfz = right_nfz_confirmed_all[0]
#         left_confirmed_reminders = Reminder.objects.filter(
#             nfz_confirmed=left_confirmed_nfz)
#         self.assertEqual(len(left_confirmed_reminders), 1)
#         right_confirmed_reminders = Reminder.objects.filter(
#             nfz_confirmed=right_confirmed_nfz)
#         self.assertEqual(len(right_confirmed_reminders), 1)
#         self.assertFalse(left_confirmed_reminders.last().active)
#         self.assertFalse(right_confirmed_reminders.last().active)

#         # there should be 6 Reminders in total (4 inactive and 2 active Reminder.pcpr)
#         reminders = Reminder.objects.all()
#         self.assertEqual(len(reminders), 6)

    def test_remove_pcpr_estimates(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        p1 = PCPR_Estimate.objects.create(
            patient=patient1,
            current=False)
        p1.timestamp = '2000-01-01'
        p1.save()
        p2 = PCPR_Estimate.objects.create(
            patient=patient1,
            current=True)
        p2.timestamp = '2000-01-02'
        p2.save()
        Reminder_PCPR.objects.create(pcpr=p1)
        Reminder_PCPR.objects.create(pcpr=p2)
        data = self.data.copy()
        data['pcpr_inactivate'] = True

        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        pcpr_all = PCPR_Estimate.objects.filter(patient=patient1)
        self.assertEqual(pcpr_all.count(), 2)
        self.assertFalse(pcpr_all.last().current)

        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Zdezaktywowano kosztorys z datą 2000-01-02.'

        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

        # reminders
        # should inactivate Reminder.pcpr
        pcpr2 = PCPR_Estimate.objects.filter(
            patient=patient1, id=2)

        reminders = Reminder_PCPR.objects.filter(
            pcpr=pcpr2)
        self.assertEqual(reminders.count(), 1)
        self.assertFalse(reminders.last().active)

    
    def test_remove_invoice(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        i1 = Invoice.objects.create(patient=patient1,
                                     payed=True,
                                     type='cash',
                                     current=False)
        i2= Invoice.objects.create(patient=patient1,
                                     payed=True,
                                     type='cash',
                                     current=True)
        i2.timestamp = '2000-01-01'
        i2.save()
        Reminder_Invoice.objects.create(invoice=i1)
        Reminder_Invoice.objects.create(invoice=i2)
        data = self.data.copy()
        data['invoice_inactivate'] = True

        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        invoice_all = Invoice.objects.filter(
            patient=patient1)
        self.assertEqual(invoice_all.count(), 2)
        self.assertFalse(invoice_all.last().current)
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Zdezaktywowano fakturę z datą 2000-01-01.'
        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

        # reminders
        # should inactivate Reminder.invoice
        invoice = invoice_all.last()
        reminders = Reminder_Invoice.objects.filter(
            invoice=invoice)
        self.assertEqual(reminders.count(), 1)
        self.assertFalse(reminders.last().active)

    def test_collection_procedure_with_1_active_invoice(self):
        # there is one active invoice
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        new1 = NFZ_New.objects.create(patient=patient1,
                                    side='left',
                                    date='2000-01-01')
        new2 = NFZ_New.objects.create(patient=patient1,
                                    side='right',
                                    date='2000-01-02')
        n1 = NFZ_Confirmed.objects.create(patient=patient1,
                                     side='left',
                                     date='2000-01-01')
        n2 = NFZ_Confirmed.objects.create(patient=patient1,
                                     side='right',
                                     date='2000-01-02')
        p1 = PCPR_Estimate.objects.create(
            patient=patient1,
            current=True)
        i1 = Invoice.objects.create(
            patient=patient1,
            current=True)
        Hearing_Aid.objects.create(patient=patient1,
                                    ear='left',
                                    make='m',
                                    family='f',
                                    model='m1',
                                   pkwiu_code='26.60.14',
                                   estimate=p1,
                                   invoice=i1,
                                    purchase_date='2000-01-02',
                                    our=False,
                                    current=False)
        Hearing_Aid.objects.create(patient=patient1,
                                    ear='right',
                                    make='m',
                                    family='f',
                                    model='m2',
                                   pkwiu_code='26.60.14',
                                   estimate=p1,
                                    invoice=i1,
                                    purchase_date='2000-01-02',
                                    our=False,
                                    current=False)
        Hearing_Aid.objects.create(patient=patient1,
                                    ear='left',
                                    make='m',
                                    family='f',
                                    model='m1old',
                                   pkwiu_code='26.60.14',
                                    purchase_date='2000-01-02',
                                    our=False,
                                    current=True)
        Hearing_Aid.objects.create(patient=patient1,
                                    ear='right',
                                    make='m',
                                    family='f',
                                    model='m2old',
                                   pkwiu_code='26.60.14',
                                    purchase_date='2000-01-02',
                                    our=False,
                                    current=True)
        Reminder_NFZ_New.objects.create(nfz_new=new1, activation_date=today)
        Reminder_NFZ_New.objects.create(nfz_new=new2, activation_date=today)
        Reminder_NFZ_Confirmed.objects.create(nfz_confirmed=n1, activation_date=today)
        Reminder_NFZ_Confirmed.objects.create(nfz_confirmed=n2, activation_date=today)
        Reminder_PCPR.objects.create(pcpr=p1, activation_date=today)
        Reminder_Invoice.objects.create(invoice=i1, activation_date=today)
        data = self.data.copy()
        data['collection_confirm'] = True
        data['collection_date'] = '2000-01-02'

        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        # should modify left and right Hearing_Aid instance that were on the invoice
        left_ha = Hearing_Aid.objects.filter(patient=patient1, ear='left').first()
        self.assertEqual(left_ha.model, 'm1')
        self.assertEqual(str(left_ha.purchase_date), '2000-01-02')
        self.assertTrue(left_ha.our)
        self.assertTrue(left_ha.current)

        right_ha = Hearing_Aid.objects.filter(patient=patient1, ear='right').first()
        self.assertEqual(right_ha.model, 'm2')
        self.assertEqual(str(right_ha.purchase_date), '2000-01-02')
        self.assertTrue(right_ha.our)
        self.assertTrue(right_ha.current)

        # should inactivate previous hearing aids (current=false)
        previous_left = Hearing_Aid.objects.get(model='m1old')
        self.assertFalse(previous_left.current)
        previous_right = Hearing_Aid.objects.get(model='m2old')
        self.assertFalse(previous_right.current)


        # should set NFZ New if any to inactive
        left_nfz_all = NFZ_New.objects.filter(
            patient=patient1, side='left')
        right_nfz_all = NFZ_New.objects.filter(
            patient=patient1, side='right')
        self.assertFalse(left_nfz_all.last().in_progress)
        self.assertFalse(right_nfz_all.last().in_progress)

        # should set NFZ confirmed to inactive
        left_nfz_all = NFZ_Confirmed.objects.filter(
            patient=patient1, side='left')
        right_nfz_all = NFZ_Confirmed.objects.filter(
            patient=patient1, side='right')
        self.assertFalse(left_nfz_all.last().in_progress)
        self.assertFalse(right_nfz_all.last().in_progress)

        # should set last PCPR estimate to inactive
        pcpr_all = PCPR_Estimate.objects.filter(
            patient=patient1)
        self.assertFalse(pcpr_all.last().current)

        # should set invoices to inactive
        invoice_all = Invoice.objects.filter(
            patient=patient1)
        self.assertFalse(invoice_all.last().current)

        # should create a new info to show in history of actions
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Odebrano lewy aparat m f m1, z datą 2000-01-02. ' + \
                        'Odebrano prawy aparat m f m2, z datą 2000-01-02.'
        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

        # reminders       
        # there should be 2 Reminder_NFZ_New (one for each side), both inactive
        left_nfz_new_all = NFZ_New.objects.filter(
            patient=patient1, side='left')
        right_nfz_new_all = NFZ_New.objects.filter(
            patient=patient1, side='right')
        left_new_nfz = left_nfz_new_all[0]
        right_new_nfz = right_nfz_new_all[0]
        left_new_reminders = Reminder_NFZ_New.objects.filter(
            nfz_new=left_new_nfz)
        self.assertEqual(left_new_reminders.count(), 1)
        right_new_reminders = Reminder_NFZ_New.objects.filter(
            nfz_new=right_new_nfz)
        self.assertEqual(right_new_reminders.count(), 1)
        self.assertFalse(left_new_reminders.last().active)
        self.assertFalse(right_new_reminders.last().active)

        # there should be 2 Reminder_NFZ_Confirmed (one for each side), both inactive
        left_nfz_confirmed_all = NFZ_Confirmed.objects.filter(
            patient=patient1, side='left')
        right_nfz_confirmed_all = NFZ_Confirmed.objects.filter(
            patient=patient1, side='right')
        left_confirmed_nfz = left_nfz_confirmed_all[0]
        right_confirmed_nfz = right_nfz_confirmed_all[0]
        left_confirmed_reminders = Reminder_NFZ_Confirmed.objects.filter(
            nfz_confirmed=left_confirmed_nfz)
        self.assertEqual(left_confirmed_reminders.count(), 1)
        right_confirmed_reminders = Reminder_NFZ_Confirmed.objects.filter(
            nfz_confirmed=right_confirmed_nfz)
        self.assertEqual(right_confirmed_reminders.count(), 1)
        self.assertFalse(left_confirmed_reminders.last().active)
        self.assertFalse(right_confirmed_reminders.last().active)

        # there should be one Reminder_PCPR, inactive
        pcpr_all = PCPR_Estimate.objects.filter(
            patient=patient1)
        pcpr_reminders = Reminder_PCPR.objects.filter(
            pcpr=pcpr_all.last())
        self.assertEqual(pcpr_reminders.count(), 1)
        self.assertFalse(pcpr_reminders.last().active)

        # there should be one Reminder_Invoice, inactive
        invoice_all = Invoice.objects.filter(
            patient=patient1)
        invoice_reminders = Reminder_Invoice.objects.filter(
            invoice=invoice_all.last())
        self.assertEqual(invoice_reminders.count(), 1)
        self.assertFalse(invoice_reminders.last().active)


        # there should be 2 Reminder_Collection instances, both active
        collection_reminders = Reminder_Collection.objects.all()
        self.assertEqual(collection_reminders.count(), 2)
        self.assertTrue(collection_reminders.first().active)
        self.assertTrue(collection_reminders.last().active)


    def test_collection_procedure_with_2_active_invoices(self):
        # there are 2 active invoices, one with HAs and one with
        # other item
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)

        p1 = PCPR_Estimate.objects.create(
            patient=patient1,
            current=True)
       
        i1 = Invoice.objects.create(
            patient=patient1,
            current=True)
        i2 = Invoice.objects.create(
            patient=patient1,
            current=True)
        Hearing_Aid.objects.create(patient=patient1,
                                   ear='left',
                                   make='m',
                                   family='f',
                                   model='m1',
                                   pkwiu_code='26.60.14',
                                   estimate=p1,
                                   invoice=i1,
                                   purchase_date='2000-01-02',
                                   our=False,
                                   current=False)
        Hearing_Aid.objects.create(patient=patient1,
                                   ear='right',
                                   make='m',
                                   family='f',
                                   model='m2',
                                   pkwiu_code='26.60.14',
                                   estimate=p1,
                                   invoice=i1,
                                   purchase_date='2000-01-02',
                                   our=False,
                                   current=False)
        Hearing_Aid.objects.create(patient=patient1,
                                   ear='left',
                                   make='m',
                                   family='f',
                                   model='m1old',
                                   pkwiu_code='26.60.14',
                                   purchase_date='2000-01-02',
                                   our=False,
                                   current=True)
        Hearing_Aid.objects.create(patient=patient1,
                                   ear='right',
                                   make='m',
                                   family='f',
                                   model='m2old',
                                   pkwiu_code='26.60.14',
                                   purchase_date='2000-01-02',
                                   our=False,
                                   current=True)
        Other_Item.objects.create(patient=patient1,                        
                                   make='o',
                                   family='fo',
                                   model='mo',
                                   pkwiu_code='26.60.14',
                                   invoice=i2)
        Reminder_Invoice.objects.create(invoice=i1, activation_date=today)
        Reminder_Invoice.objects.create(invoice=i2, activation_date=today)
        Reminder_PCPR.objects.create(pcpr=p1, activation_date=today)
        data = self.data.copy()
        data['collection_confirm'] = True
        data['collection_date'] = '2000-01-02'

        url = reverse('crm:updating', args=(patient1.id,))
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)

        # should modify left and right Hearing_Aid instance that were on the invoice
        left_ha = Hearing_Aid.objects.filter(
            patient=patient1, ear='left').first()
        self.assertEqual(left_ha.model, 'm1')
        self.assertEqual(str(left_ha.purchase_date), '2000-01-02')
        self.assertTrue(left_ha.our)
        self.assertTrue(left_ha.current)

        right_ha = Hearing_Aid.objects.filter(
            patient=patient1, ear='right').first()
        self.assertEqual(right_ha.model, 'm2')
        self.assertEqual(str(right_ha.purchase_date), '2000-01-02')
        self.assertTrue(right_ha.our)
        self.assertTrue(right_ha.current)

        # should inactivate previous hearing aids (current=false)
        previous_left = Hearing_Aid.objects.get(model='m1old')
        self.assertFalse(previous_left.current)
        previous_right = Hearing_Aid.objects.get(model='m2old')
        self.assertFalse(previous_right.current)

        # should set last PCPR estimate to inactive
        pcpr_all = PCPR_Estimate.objects.filter(
            patient=patient1)
        self.assertFalse(pcpr_all.last().current)

        # should set all invoices to inactive
        invoice_all = Invoice.objects.filter(
            patient=patient1, current=True)
        self.assertFalse(invoice_all)

        # should create a new info to show in history of actions
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Odebrano lewy aparat m f m1, z datą 2000-01-02. ' + \
                        'Odebrano prawy aparat m f m2, z datą 2000-01-02.'
        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

        # reminders
        # there should be one Reminder_PCPR, inactive
        pcpr_all = PCPR_Estimate.objects.filter(
            patient=patient1)
        pcpr_reminders = Reminder_PCPR.objects.filter(
            pcpr=pcpr_all.last())
        self.assertEqual(pcpr_reminders.count(), 1)
        self.assertFalse(pcpr_reminders.last().active)

        # there should be two Reminder_Invoice, inactive
        self.assertEqual(Reminder_Invoice.objects.all().count(), 2)
        self.assertFalse(Reminder_Invoice.objects.filter(active=True))

        # there should be 2 Reminder_Collection instances, both active
        self.assertEqual(Reminder_Collection.objects.all().count(), 2)
        self.assertTrue(Reminder_Collection.objects.filter(active=True), 2)


class TestDeleteView(TestCase):
    def setUp(self):
        user_john = create_user()
        patient1 = create_patient(user_john)
        
    def test_anonymous(self):
        '''should redirect to login'''
        patient1 = Patient.objects.get(id=1)
        url = reverse('crm:deleteconfirm', args=(patient1.id,))
        expected_url = reverse('login') + '?next=/' + \
            str(patient1.id) + '/deleteconfirm/'
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

    def test_setup_logged_in(self):
        self.client.login(username='john', password='glassonion')
        patient = Patient.objects.get(id=1)
        url = reverse('crm:deleteconfirm', args=(1,))
        response = self.client.get(url)
        assert response.status_code == 200, 'Should be callable by logged in user'

class TestDeletePatientView(TestCase):
    def setUp(self):
        user_john = create_user()
        patient1 = create_patient(user_john)

    def test_anonymous(self):
        '''should redirect to login'''
        patient1 = Patient.objects.get(id=1)
        url = reverse('crm:delete', args=(patient1.id,))
        expected_url = reverse('login') + '?next=/' + \
            str(patient1.id) + '/delete/'
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)
    
    def test_setup_logged_in(self):
        self.client.login(username='john', password='glassonion')
        url = reverse('crm:delete', args=(1,))
        expected_url = reverse('crm:index')
        response = self.client.post(url,follow=True)
        assert response.status_code == 200, 'Should redirect'
        # should redirect to expected_url
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)
        # patient should have been deleted
        self.assertFalse(Patient.objects.all().exists())


class TestReminderNFZNewView(TestCase):
    def setUp(self):
        user_john = create_user()
        patient1 = create_patient(user_john)

    def test_one(self):
        self.client.login(username='john', password='glassonion')
        nfz = NFZ_New.objects.create(
            patient=Patient.objects.get(id=1), date=today, side='left')
        Reminder_NFZ_New.objects.create(nfz_new=nfz, activation_date=today)
        url = reverse('crm:reminder_nfz_new', args=(1,))
        response = self.client.post(url)
        # should give code 200
        assert response.status_code == 200
        self.assertEqual(response.context['reminder_id'], 1)
        exp_subj = 'John Smith1, w dniu: %s otrzymano NOWY wniosek NFZ lewy' % today.strftime(
            "%d.%m.%Y")
        self.assertEqual(response.context['subject'], exp_subj)
        self.assertEqual(response.context['url_address'], url)


    def test_inactivate_reminder_nfz_new(self):
        self.client.login(username='john', password='glassonion')
        nfz = NFZ_New.objects.create(
            patient=Patient.objects.get(id=1), date=today, side='left')
        Reminder_NFZ_New.objects.create(nfz_new=nfz, activation_date=today)
        data = {'inactivate_reminder': 'inactivate'}
        url = reverse('crm:reminder_nfz_new', args=(1,))
        # should give code 200
        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200
        # should inactivate reminder
        self.assertFalse(Reminder_NFZ_New.objects.get(id=1).active)

class TestReminderNFZConfirmedView(TestCase):
    def setUp(self):
        user_john = create_user()
        patient1 = create_patient(user_john)

    def test_one(self):
        self.client.login(username='john', password='glassonion')
        nfz = NFZ_Confirmed.objects.create(
            patient=Patient.objects.get(id=1), date=today, side='left')
        Reminder_NFZ_Confirmed.objects.create(nfz_confirmed=nfz, activation_date=today)
        url = reverse('crm:reminder_nfz_confirmed', args=(1,))
        response = self.client.post(url)
        # should give code 200
        assert response.status_code == 200
        self.assertEqual(response.context['reminder_id'], 1)
        exp_subj = 'John Smith1, w dniu: %s otrzymano POTWIERDZONY wniosek NFZ lewy' % today.strftime(
            "%d.%m.%Y")
        self.assertEqual(response.context['subject'], exp_subj)

    def test_inactivate_reminder_nfz_confirmed(self):
        self.client.login(username='john', password='glassonion')
        nfz = NFZ_Confirmed.objects.create(
            patient=Patient.objects.get(id=1), date=today, side='left')
        Reminder_NFZ_Confirmed.objects.create(nfz_confirmed=nfz, activation_date=today)

        data = {'inactivate_reminder': 'inactivate'}
        # should give code 200
        url = reverse('crm:reminder_nfz_confirmed', args=(1,))
        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200
        # should inactivate reminder
        self.assertFalse(Reminder_NFZ_Confirmed.objects.get(id=1).active)


class TestReminderPCPRView(TestCase):
    def setUp(self):
        user_john = create_user()
        patient1 = create_patient(user_john)

    def test_one(self):
        self.client.login(username='john', password='glassonion')
        pcpr = PCPR_Estimate.objects.create(patient=Patient.objects.get(id=1))
        
        Reminder_PCPR.objects.create(pcpr=pcpr)
        url = reverse('crm:reminder_pcpr', args=(1,))
        response = self.client.get(url)
        # should give code 200
        assert response.status_code == 200
        self.assertEqual(response.context['reminder_id'], 1)
        exp_subj = 'John Smith1, w dniu: %s wystawiono kosztorys' % today.strftime(
            "%d.%m.%Y")
        self.assertEqual(response.context['subject'], exp_subj)

    def test_inactivate_reminder_pcpr(self):
        self.client.login(username='john', password='glassonion')
        pcpr = PCPR_Estimate.objects.create(patient=Patient.objects.get(id=1))

        Reminder_PCPR.objects.create(pcpr=pcpr)
        data = {'inactivate_reminder': 'inactivate'}
        url = reverse('crm:reminder_pcpr', args=(1,))
        response = self.client.post(url, data, follow=True)        # should give code 200
        assert response.status_code == 200
        # should inactivate reminder
        self.assertFalse(Reminder_PCPR.objects.get(id=1).active)

class TestReminderInvoiceView(TestCase):
    def setUp(self):
        user_john = create_user()
        patient1 = create_patient(user_john)

    def test_one(self):
        self.client.login(username='john', password='glassonion')
        invoice = Invoice.objects.create(
            patient=Patient.objects.get(id=1), type='cash', payed=True)

        Reminder_Invoice.objects.create(invoice=invoice)
        url = reverse('crm:reminder_invoice', args=(1,))
        response = self.client.get(url)
        # should give code 200
        assert response.status_code == 200
        self.assertEqual(response.context['reminder_id'], 1)
        exp_subj = 'John Smith1, w dniu: %s wystawiono fakture' % today.strftime(
            "%d.%m.%Y")
        self.assertEqual(response.context['subject'], exp_subj)

    def test_inactivate_reminder_invoice(self):
        self.client.login(username='john', password='glassonion')
        invoice = Invoice.objects.create(
            patient=Patient.objects.get(id=1), type='cash', payed=True)

        Reminder_Invoice.objects.create(invoice=invoice)
        data = {'inactivate_reminder': 'inactivate'}
        url = reverse('crm:reminder_invoice', args=(1,))
        # should give code 200
        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200
        # should inactivate reminder
        self.assertFalse(Reminder_Invoice.objects.get(id=1).active)

    
class TestReminderCollectionView(TestCase):
    def setUp(self):
        user_john = create_user()
        patient1 = create_patient(user_john)

    def test_one_present(self):
        self.client.login(username='john', password='glassonion')
        ha1 = Hearing_Aid.objects.create(patient=Patient.objects.get(id=1),
                                    ear='left',
                                    make='m',
                                    family='f',
                                    model='m1',
                                   pkwiu_code='26.60.14',
                                    purchase_date='2000-01-02',
                                    our=False,
                                    current=False)

        Reminder_Collection.objects.create(ha=ha1)
        url = reverse('crm:reminder_collection', args=(1,))
        response = self.client.get(url)
        # should give code 200
        assert response.status_code == 200
        self.assertEqual(response.context['reminder_id'], 1)
        exp_subj = 'John Smith1, w dniu: %s wydano aparat m f m1 lewy' % today.strftime(
            "%d.%m.%Y")
        self.assertEqual(response.context['subject'], exp_subj)

    def test_inactivate_reminder_collection(self):
        self.client.login(username='john', password='glassonion')
        ha1 = Hearing_Aid.objects.create(patient=Patient.objects.get(id=1),
                                         ear='left',
                                         make='m',
                                         family='f',
                                         model='m1',
                                         pkwiu_code='26.60.14',
                                         purchase_date='2000-01-02',
                                         our=False,
                                         current=False)

        Reminder_Collection.objects.create(ha=ha1)

        data = {'inactivate_reminder': 'inactivate'}
        url = reverse('crm:reminder_collection', args=(1,))
        response = self.client.post(url, data, follow=True)        # should give code 200
        assert response.status_code == 200
        # should inactivate reminder
        self.assertFalse(Reminder_Collection.objects.get(id=1).active)


class TestInvoiceCreateView(TestCase):
    def setUp(self):
        user_john = create_user()
        create_patient(user_john)

    def test_anonymous(self):
        '''should redirect to login'''
        url = reverse('crm:invoice_create', args=(1,))
        expected_url = reverse('login') + '?next=/1/invoice_create/'
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

    def test_logged_in_with_valid_data_for_ha(self):
        '''should create:
        one hearing aid (current=False),
        one invoice instance with one position - hearing aid,
        for a given patient,
        invoice type should be 'transfer',
        invoice note: 'test note',
        invoice date not provided - should default to today
        should also:
        redirect to detail view'''
        Invoice.objects.create(patient=Patient.objects.get(id=1))
        Invoice.objects.create(patient=Patient.objects.get(id=1))
        self.client.login(username='john', password='glassonion')
        url = reverse('crm:invoice_create', args=(1,))
        expected_url = reverse('crm:invoice_detail', args=(3,))
        data = {
            # form data
            'type': 'transfer',
            'note': 'test note',
            'current': True,

            # formset data
            # these are needed for formset to work
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,

            # formset forms data
            'form-0-device_type': 'ha',
            'form-0-make': 'Bernafon',
            'form-0-family': 'WIN',
            'form-0-model': '102',
            'form-0-price_gross': 107,
            'form-0-vat_rate': '8',
            'form-0-pkwiu_code': '11.22',
            'form-0-quantity': 1,
            'form-0-ear': 'right',
        }

        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)
        invoice = Invoice.objects.get(pk=3)

        ha = Hearing_Aid.objects.get(pk=1)
        # should create only one Hearing_Aid obj
        self.assertEqual(Hearing_Aid.objects.all().count(), 1)
        # created HA should not be active
        self.assertFalse(ha.current)
        # should create one new invoice obj (there are also 2 old)
        self.assertEqual(Invoice.objects.all().count(), 3)
        # this invoice should be tied to hearing aid
        self.assertEqual(ha.invoice, invoice)
        # hearing aid make should be 'Bernafon'
        self.assertEqual(ha.make, 'Bernafon')
        # new invoice should be active (current=True)
        self.assertTrue(invoice.current)
        # new invoice should have a type of 'transfer'
        self.assertEqual(invoice.type, 'transfer')
        # new invoice should have a note: 'test note'
        self.assertEqual(invoice.note, 'test note')

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Utworzono nową fakturę.')

        # there should be one NewInfo instance
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Dodano fakturę nr: %s' % invoice.id

        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

        self.assertEqual(invoice.date, today)

        # n1 = NFZ_New.objects.create(patient=patient1,
        #                             side='left',
        #                             date='2000-01-01')
        # n2 = NFZ_New.objects.create(patient=patient1,
        #                             side='right',
        #                             date='2000-01-02')
        # Reminder_NFZ_New.objects.create(nfz_new=n1, activation_date=today)
        # Reminder_NFZ_New.objects.create(nfz_new=n2, activation_date=today)

        # n1 = NFZ_Confirmed.objects.create(patient=patient1,
        #                                   side='left',
        #                                   date='2000-01-01')
        # n2 = NFZ_Confirmed.objects.create(patient=patient1,
        #                                   side='right',
        #                                   date='2000-01-02')
        # Reminder_NFZ_Confirmed.objects.create(nfz_confirmed=n1, activation_date=today)
        # Reminder_NFZ_Confirmed.objects.create(nfz_confirmed=n2, activation_date=today)

        # p1 = PCPR_Estimate.objects.create(patient=patient1,
        #         ear='left', ha_make='m', ha_family='f', ha_model='m', date='2000-01-01')
        # p2 = PCPR_Estimate.objects.create(patient=patient1,
        #         ear='right', ha_make='m1', ha_family='f1', ha_model='m1', date='2000-01-02')


        # remiders
        # remove Reminder.nfz_new, Reminder.nfz_confirmed and Reminder.pcpr
        # left_nfz_new_all = NFZ_New.objects.filter(
        #     patient=patient1, side='left')
        # right_nfz_new_all = NFZ_New.objects.filter(
        #     patient=patient1, side='right')
        # left_new_nfz = left_nfz_new_all[0]
        # right_new_nfz = right_nfz_new_all[0]
        # left_new_reminders = Reminder_NFZ_New.objects.filter(
        #     nfz_new=left_new_nfz)
        # self.assertEqual(left_new_reminders.count(), 1)
        # right_new_reminders = Reminder_NFZ_New.objects.filter(
        #     nfz_new=right_new_nfz)
        # self.assertEqual(right_new_reminders.count(), 1)
        # self.assertFalse(left_new_reminders.last().active)
        # self.assertFalse(right_new_reminders.last().active)

        # left_nfz_confirmed_all = NFZ_Confirmed.objects.filter(
        #     patient=patient1, side='left')
        # right_nfz_confirmed_all = NFZ_Confirmed.objects.filter(
        #     patient=patient1, side='right')
        # left_confirmed_nfz = left_nfz_confirmed_all[0]
        # right_confirmed_nfz = right_nfz_confirmed_all[0]
        # left_confirmed_reminders = Reminder_NFZ_Confirmed.objects.filter(
        #     nfz_confirmed=left_confirmed_nfz)
        # self.assertEqual(left_confirmed_reminders.count(), 1)
        # right_confirmed_reminders = Reminder_NFZ_Confirmed.objects.filter(
        #     nfz_confirmed=right_confirmed_nfz)
        # self.assertEqual(right_confirmed_reminders.count(), 1)
        # self.assertFalse(left_confirmed_reminders.last().active)
        # self.assertFalse(right_confirmed_reminders.last().active)

        # left_pcpr_all = PCPR_Estimate.objects.filter(
        #     patient=patient1, ear='left')
        # right_pcpr_all = PCPR_Estimate.objects.filter(
        #     patient=patient1, ear='right')
        # left_pcpr = left_pcpr_all[0]
        # right_pcpr = right_pcpr_all[0]
        # left_confirmed_reminders = Reminder_PCPR.objects.filter(
        #     pcpr=left_pcpr)
        # self.assertEqual(left_confirmed_reminders.count(), 1)
        # right_confirmed_reminders = Reminder_PCPR.objects.filter(
        #     pcpr=right_pcpr)
        # self.assertEqual(right_confirmed_reminders.count(), 1)
        # self.assertFalse(left_confirmed_reminders.last().active)
        # self.assertFalse(right_confirmed_reminders.last().active)



    def test_logged_in_with_invalid_form_data(self):
        '''should redisplay invoice_create page with a warning message'''
        self.client.login(username='john', password='glassonion')
        url = reverse('crm:invoice_create', args=(1,))
        data = {
            # form data
            'type': '', # this should make the form invalid

            # formset data
            # these are needed for formset to work
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,

            # formset forms data
            'form-0-device_type': 'ha',
            'form-0-make': 'Bernafon',
            'form-0-family': 'WIN',
            'form-0-model': '102',
            'form-0-price_gross': 107,
            'form-0-vat_rate': '8',
            'form-0-ear': 'right',
        }
        response = self.client.post(url, data, follow=True)

        assert response.status_code == 200

        # should not create invoice obj
        self.assertEqual(Invoice.objects.all().count(), 0)

        # should not create Hearing_Aid obj
        self.assertEqual(Hearing_Aid.objects.all().count(), 0)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Niepoprawne dane, popraw.')




    def test_logged_in_with_valid_data_for_other_device(self):
        '''should create:
        one instance of other device,
        one invoice instance with one position - wkładka uszna,
        for a given patient,
        invoice date was set to tomorrow,
        should redirect to detail view'''
        self.client.login(username='john', password='glassonion')
        url = reverse('crm:invoice_create', args=(1,))
        expected_url = reverse('crm:invoice_detail', args=(1,))
        data = {
            # form data
            'type': 'transfer',
            'date': today + timedelta(days=1),

            # formset data
            # these are needed for formset to work
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,

            # formset forms data
            'form-0-device_type': 'other',
            'form-0-make': 'Audioservice',
            'form-0-family': 'wkładka uszna',
            'form-0-model': 'twarda',
            'form-0-price_gross': 17,
            'form-0-vat_rate': '8',
            'form-0-pkwiu_code': '11.22',
            'form-0-quantity': 1,
            'form-0-ear': 'right',  # this will not be saved anywhere, but requred
                                    # for the form to be valid
        }

        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        invoice = Invoice.objects.get(pk=1)

        other = Other_Item.objects.get(pk=1)
        # should create only one Other_Item obj
        self.assertEqual(Other_Item.objects.all().count(), 1)
        # should create only one invoice obj
        self.assertEqual(Invoice.objects.all().count(), 1)
        # this invoice should be tied to 'other device'
        self.assertEqual(other.invoice, invoice)
        # other item make should be 'Audioservice'
        self.assertEqual(other.make, 'Audioservice')

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Utworzono nową fakturę.')

        self.assertEqual(invoice.date, today + timedelta(days=1))


class TestCorrectiveInvoiceCreateView(TestCase):
    def setUp(self):
        user_john = create_user()
        create_patient(user_john)

    def test_anonymous(self):
        '''should redirect to login'''
        url = reverse('crm:corrective_invoice_create', args=(1,))
        expected_url = reverse('login') + '?next=/1/corrective_invoice_create/'
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

    def test_logged_in_with_valid_data_for_ha(self):
        '''should create:
        one corrective invoice,
        invoice note: 'new note',
        invoice date not provided - should default to today
        should also:
        redirect to corretive invoice detail view
        corresponding invoice items should remain unchanged
        corresponding invoice remider should be inactivated'''
        i= Invoice.objects.create(patient=Patient.objects.get(id=1))
        mixer.blend('crm.Reminder_Invoice', invoice=i)
        mixer.blend('crm.Hearing_Aid', current=False, invoice=i)
        mixer.blend('crm.Other_Item', invoice=i)
        self.client.login(username='john', password='glassonion')
        url = reverse('crm:corrective_invoice_create', args=(1,))
        expected_url = reverse('crm:corrective_invoice_detail', args=(1,))
        data = {
            # form data
            'ha': [1],
            'other': [1],
            'note': 'new note',
        }

        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)
        cinvoice = Corrective_Invoice.objects.get(pk=1)

        h = Hearing_Aid.objects.all().first()
        # should be only one Hearing_Aid obj
        self.assertEqual(Hearing_Aid.objects.all().count(), 1)
        # HA should not be active
        self.assertFalse(h.current)
        # this corrective_invoice should be tied to hearing aid
        self.assertEqual(h.corrective_invoice, cinvoice)
        # HA should still have invoice
        i = Invoice.objects.get(id=1)
        self.assertEqual(h.invoice, i)

        o = Other_Item.objects.all().first()
        # should be only one Other_Item obj
        self.assertEqual(Other_Item.objects.all().count(), 1)
        # this corrective_invoice should be tied to Other_Item
        self.assertEqual(o.corrective_invoice, cinvoice)
        # Other_Item should still have invoice
        i = Invoice.objects.get(id=1)
        self.assertEqual(o.invoice, i)

        # new cinvoice should have a note: 'new note'
        self.assertEqual(cinvoice.note, 'new note')

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Utworzono nową fakturę korektę.')

        # there should be one NewInfo instance
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Dodano fakturę korektę nr: %s' % cinvoice.id
        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

        # inactivate reminder
        r = Reminder_Invoice.objects.all()
        # should be one reminder
        self.assertEqual(r.count(), 1)
        # reminder should be inactive
        self.assertFalse(r.first().active)

        # corrective invoice date should be today
        self.assertEqual(cinvoice.date, today)

    def test_logged_in_with_valid_data_for_ha_date_provided(self):
        '''corrective invoice date should be tomorrow'''
        i = Invoice.objects.create(patient=Patient.objects.get(id=1))
        mixer.blend('crm.Reminder_Invoice', invoice=i)
        mixer.blend('crm.Hearing_Aid', current=False, invoice=i)
        self.client.login(username='john', password='glassonion')
        url = reverse('crm:corrective_invoice_create', args=(1,))
        data = {
            # form data
            'ha': [1],
            'other': [],
            'date': today + timedelta(days=1),
        }

        self.client.post(url, data, follow=True)
        
        # corrective invoice date should be tomorrow
        cinvoice = Corrective_Invoice.objects.get(pk=1)
        self.assertEqual(cinvoice.date, today + timedelta(days=1))


class TestInvoiceUpdateView(TestCase):
    def setUp(self):
        user_john = create_user()
        create_patient(user_john)

    def test_anonymous(self):
        '''should redirect to login'''
        url = reverse('crm:invoice_update', args=(1,))
        expected_url = reverse('login') + '?next=/1/invoice_update/'
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

    def test_logged_in_with_valid_data(self):
        '''should modify:
        note, current, payed, type, date
        redirect to invoice detail view'''
        i = Invoice.objects.create(
            patient=Patient.objects.get(id=1),
            type='transfer',
            current=True,
            payed=False,
            note='test note óŹł',
            date = datetime.now() - timedelta(days=1)
        )

        self.client.login(username='john', password='glassonion')
        url = reverse('crm:invoice_update', args=(1,))
        expected_url = reverse('crm:invoice_detail', args=(1,))
        data = {
            # form data
            'type': 'cash',
            'note': 'test note',
            'current': False,
            'payed': True,
            'date': today
        }

        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        # should be one Invoice
        self.assertEqual(Invoice.objects.all().count(), 1)
        # should modify invoice type to be 'cash'
        invoice = Invoice.objects.all().first()
        self.assertEqual(invoice.type, 'cash')
        # should modify invoice current to be False
        self.assertEqual(invoice.current, False)
        # should modify invoice payed to be True
        self.assertEqual(invoice.payed, True)
        # should modify invoice note to be 'test note'
        self.assertEqual(invoice.note, 'test note')
        # should modify invoice date to be today
        self.assertEqual(invoice.date, today)


class TestSZOI_UsageCreate(TestCase):
    def setUp(self):
        create_user()
        self.test_dir = tempfile.mkdtemp()
        settings.MEDIA_ROOT = self.test_dir

    def test_anonymous(self):
        '''should redirect to login'''
        url = reverse('crm:szoi_detail', args=(1,))
        expected_url = reverse('login') + '?next=/1/szoi_detail/'
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

    def test_szoi_usage_10HA(self):
        '''there is 10 HA in a file, no preexisting'''
        test_file = os.getcwd() + '/crm/tests/test_files/szoi10HA.xls'
        # create SZOI_File instance with the above file
        f = open(test_file)
        s = SZOI_File.objects.create(file=File(f))

        self.client.login(username='john', password='glassonion')
        url = reverse('crm:szoi_usage_create')
        expected_url = reverse('crm:szoi_usage_detail', args=(1,))
        data = {
            # form data
            'szoi_file': s.id,
        }

        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        szoi_all = SZOI_File_Usage.objects.all()
        szoi = szoi_all.first()
        # should be one SZOI_File_Usage instance
        self.assertEqual(szoi_all.count(), 1)

        # should be 10 HA Stock instances
        self.assertEqual(Hearing_Aid_Stock.objects.all().count(), 10)

        # should be 0 Other instances
        self.assertEqual(Other_Item_Stock.objects.all().count(), 0)

        # there should be 10 new HA Stock associated with SZOI_File_Usage instance
        self.assertEqual(szoi.ha_szoi_new.all().count(), 10)

        errors = SZOI_Errors.objects.all()
        # should create 0 SZOI_Errors instances
        self.assertEqual(errors.count(), 0)

        f.close()

    def test_szoi_usage_10HA_update(self):
        '''there is 10 HA in a file, 2 preexisting'''
        mixer.blend('crm.Hearing_Aid_Stock',
                    make='Bernafon',
                    family='ZERENA 9',
                    model='B 105',
                    price_gross=1)
        mixer.blend('crm.Hearing_Aid_Stock',
                    make='Audibel',
                    family='A4 IQ GOLD',
                    model='ITE',
                    price_gross=1)
        test_file = os.getcwd() + '/crm/tests/test_files/szoi10HA.xls'
        # create SZOI_File instance with the above file
        f = open(test_file)
        s = SZOI_File.objects.create(file=File(open(test_file)))

        self.client.login(username='john', password='glassonion')
        url = reverse('crm:szoi_usage_create')
        expected_url = reverse('crm:szoi_usage_detail', args=(1,))
        data = {
            # form data
            'szoi_file': s.id,
        }

        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        # new price of ZERENA 9 B 105 should be 8100
        z9 = Hearing_Aid_Stock.objects.get(
            make='Bernafon',
            family='ZERENA 9',
            model='B 105'
        )
        self.assertEqual(z9.price_gross, 8100)

        # new price of Audibel A4 IQ GOLD ITE should be 5400
        a4 = Hearing_Aid_Stock.objects.get(
            make='Audibel',
            family='A4 IQ GOLD',
            model='ITE'
        )
        self.assertEqual(a4.price_gross, 5400)

        szoi_all = SZOI_File_Usage.objects.all()
        szoi = szoi_all.first()
        # should be one SZOI_File_Usage instance
        self.assertEqual(szoi_all.count(), 1)

        # should be 10 HA Stock instances
        self.assertEqual(Hearing_Aid_Stock.objects.all().count(), 10)

        # should be 0 Other instances
        self.assertEqual(Other_Item_Stock.objects.all().count(), 0)

        # there should be 8 new HA Stock associated with SZOI_File_Usage instance
        self.assertEqual(szoi.ha_szoi_new.all().count(), 8)

        # there should be 2 updated HA Stock associated with SZOI_File_Usage instance
        self.assertEqual(szoi.ha_szoi_updated.all().count(), 2)

        errors = SZOI_Errors.objects.all()
        # should create 0 SZOI_Errors instances
        self.assertEqual(errors.count(), 0)

        f.close()

    def test_szoi_usage_update_other(self):
        '''there are 2 preexisting other devices'''
        mixer.blend('crm.Other_Item_Stock',
                    make='Audioservice',
                    family='WKŁADKA USZNA',
                    model='TWARDA',
                    price_gross=1)
        mixer.blend('crm.Other_Item_Stock',
                    make='Phonak',
                    family='PHONAK ROGER',
                    model='ROGER CLIP-ON MIC + 2 X ROGER X (03)',
                    price_gross=1)
        test_file = os.getcwd() + '/crm/tests/test_files/szoi_full2.xls'
        # create SZOI_File instance with the above file
        f = open(test_file)
        s = SZOI_File.objects.create(file=File(open(test_file)))

        self.client.login(username='john', password='glassonion')
        url = reverse('crm:szoi_usage_create')
        expected_url = reverse('crm:szoi_usage_detail', args=(1,))
        data = {
            # form data
            'szoi_file': s.id,
        }

        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        # new price of Audioservice WKŁADKA USZNA MIĘKKA KOMFORT should be 3
        a1 = Other_Item_Stock.objects.get(
            make='Audioservice',
            family='WKŁADKA USZNA',
            model='MIĘKKA KOMFORT',
        )
        self.assertEqual(a1.price_gross, 3)

        # new price of Phonak ROGER CLIP-ON MIC + 2 X ROGER X (03) should be 4
        p1 = Other_Item_Stock.objects.get(
            make='Phonak',
            family='PHONAK ROGER',
            model='ROGER CLIP-ON MIC + 2 X ROGER X (03)',
        )
        self.assertEqual(p1.price_gross, 4)

        szoi_all = SZOI_File_Usage.objects.all()
        szoi = szoi_all.first()

        # should be 10 Other instances
        self.assertEqual(Other_Item_Stock.objects.all().count(), 17)

        # there should be 15 new Other associated with SZOI_File_Usage instance
        self.assertEqual(szoi.other_szoi_new.all().count(), 15)

        # there should be 2 updated Other Stock associated with SZOI_File_Usage instance
        self.assertEqual(szoi.other_szoi_updated.all().count(), 2)

        errors = SZOI_Errors.objects.all()
        # should create 0 SZOI_Errors instances
        self.assertEqual(errors.count(), 0)

        f.close()

    def test_szoi_usage_10HA_errors(self):
        '''second and third lines in a file have only 2 items,
        fourth line has none of the expected text'''
        test_file = os.getcwd() + '/crm/tests/test_files/szoi10haError_shortLine.xls'
        # create SZOI_File instance with the above file
        f = open(test_file)
        s = SZOI_File.objects.create(file=File(f))

        self.client.login(username='john', password='glassonion')
        url = reverse('crm:szoi_usage_create')
        expected_url = reverse('crm:szoi_usage_detail', args=(1,))
        data = {
            # form data
            'szoi_file': s.id,
        }

        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

        szoi_all = SZOI_File_Usage.objects.all()
        szoi = szoi_all.first()
        # should be one SZOI_File_Usage instance
        self.assertEqual(szoi_all.count(), 1)

        # should be 7 HA Stock instances
        self.assertEqual(Hearing_Aid_Stock.objects.all().count(), 7)

        # should be 0 Other instances
        self.assertEqual(Other_Item_Stock.objects.all().count(), 0)

        # there should be 7 new HA Stock associated with SZOI_File_Usage instance
        self.assertEqual(szoi.ha_szoi_new.all().count(), 7)

        errors = SZOI_Errors.objects.all()
        # should create 3 SZOI_Errors instances
        self.assertEqual(errors.count(), 3)

        f.close()


    def test_szoi_usage_1131HA_17Other(self):
        pass


    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)
