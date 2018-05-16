# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.contrib import auth
from django.core.paginator import Paginator

import pytest
from datetime import datetime, timedelta
from django.contrib.staticfiles.templatetags.staticfiles import static

from crm.models import (Patient, Hearing_Aid, NFZ_Confirmed, PCPR_Estimate,
                        NFZ_New, HA_Invoice, NewInfo, Audiogram, Reminder)

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
        self.client.login(username='john', password='glassonion')
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
        ''' scenario with only inactive (in_progres=False) latest (.last()) PCPR_Estimate
        instances'''
        self.client.login(username='john', password='glassonion')
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
        self.client.login(username='john', password='glassonion')
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
        self.client.login(username='john', password='glassonion')
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
        self.client.login(username='john', password='glassonion')
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
        self.client.login(username='john', password='glassonion')
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
                'left_pcpr_ha': 'model3_f3_b3',
                'right_pcpr_ha': 'b4_f4_m4',
                'left_PCPR_date': '2003-01-01',
                'right_PCPR_date': '2004-01-01',
                'note': 'p1_note',
                }
        url = reverse('crm:store')
        # id of new patient should be 1
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                     status_code=302, target_status_code=200)
        self.assertEqual(len(Patient.objects.all()), 1)
        self.assertEqual(len(NFZ_New.objects.all()), 2)
        self.assertEqual(len(NFZ_Confirmed.objects.all()), 2)
        self.assertEqual(len(PCPR_Estimate.objects.all()), 2)
        self.assertEqual(len(Hearing_Aid.objects.all()), 2)
        self.assertEqual(len(Reminder.objects.all()),6)


    def test_add_other_left_ha(self):
        ''' should create user with left other ha'''
        self.client.login(username='john', password='glassonion')
        data = {'fname': 'Adam',
                'lname': 'Atkins',
                'bday': '2000-01-01',
                'usrtel': 1,
                'location': 'some_location',
                'left_other_ha': 'Starkey',
                'right_other_ha': 'Beltone virte c g90'
                }
        url = reverse('crm:store')
        # id of new patient should be 1
        expected_url = reverse('crm:edit', args=(1,))
        response = self.client.post(url, data, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                     status_code=302, target_status_code=200)
        self.assertEqual(len(Patient.objects.all()), 1)
        self.assertEqual(len(Hearing_Aid.objects.all()), 2)
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
                    'summary_note': 'some note'
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
        self.assertEqual(new_info.audiometrist, adam)

    def test_adding_another_hearing_aids_with_purchase_dates(self):
        self.client.login(username='john', password='glassonion')
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
        self.assertEqual(len(left_nfz_all), 1)
        self.assertEqual(len(right_nfz_all), 1)
        self.assertEqual(str(left_nfz_all.last().date), '2001-01-01')
        self.assertEqual(str(right_nfz_all.last().date), '2001-01-02')
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Dodano niepotwierdzony lewy wniosek z datą 2001-01-01. ' + \
                        'Dodano niepotwierdzony prawy wniosek z datą 2001-01-02.'
        reminders = Reminder.objects.all()
        self.assertEqual(len(reminders), 2)
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
        Reminder.objects.create(nfz_new=n1, activation_date=today)
        Reminder.objects.create(nfz_new=n2, activation_date=today)
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
        self.assertEqual(len(left_nfz_all), 2)
        self.assertEqual(len(right_nfz_all), 2)
        self.assertEqual(str(left_nfz_all.last().date), '2001-01-01')
        self.assertEqual(str(right_nfz_all.last().date), '2001-01-02')
        self.assertEqual(response.context['reminders'], 2)

    def test_remove_NFZ(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        n1 = NFZ_New.objects.create(patient=patient1,
                                          side='left',
                                          date='2000-01-01')
        n2 = NFZ_New.objects.create(patient=patient1,
                                          side='right',
                                          date='2000-01-02')
        Reminder.objects.create(nfz_new=n1)
        Reminder.objects.create(nfz_new=n2)
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
        self.assertEqual(len(left_nfz_all), 1)
        self.assertEqual(len(right_nfz_all), 1)
        self.assertFalse(left_nfz_all.last().in_progress)
        self.assertFalse(right_nfz_all.last().in_progress)
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Usunięto lewy niepotwierdzony wniosek z datą 2000-01-01. ' + \
                        'Usunięto prawy niepotwierdzony wniosek z datą 2000-01-02.'

        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

    def test_adding_NFZ_confirmed(self):
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
        self.assertEqual(len(left_nfz_all), 1)
        self.assertEqual(len(right_nfz_all), 1)
        self.assertEqual(str(left_nfz_all.last().date), '2001-01-01')
        self.assertEqual(str(right_nfz_all.last().date), '2001-01-02')
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Dodano potwierdzony lewy wniosek z datą 2001-01-01. ' + \
                        'Dodano potwierdzony prawy wniosek z datą 2001-01-02.'
        reminders = Reminder.objects.all()
        self.assertEqual(len(reminders), 2)
        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

    def test_adding_another_NFZ_confirmed(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        n1 = NFZ_Confirmed.objects.create(patient=patient1,
                                   side='left',
                                   date='2000-01-01')
        n2 = NFZ_Confirmed.objects.create(patient=patient1,
                                     side='right',
                                     date='2000-01-02')
        Reminder.objects.create(nfz_confirmed=n1, activation_date=today)
        Reminder.objects.create(nfz_confirmed=n2, activation_date=today)
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
        self.assertEqual(response.context['reminders'],2)


    def test_remove_NFZ(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        n1 = NFZ_Confirmed.objects.create(patient=patient1,
                                     side='left',
                                     date='2000-01-01')
        n2 = NFZ_Confirmed.objects.create(patient=patient1,
                                     side='right',
                                     date='2000-01-02')
        Reminder.objects.create(nfz_confirmed=n1)
        Reminder.objects.create(nfz_confirmed=n2)
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
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Usunięto lewy wniosek z datą 2000-01-01. ' + \
                        'Usunięto prawy wniosek z datą 2000-01-02.'

        self.assertEqual(new_info.note, expected_note.decode('utf-8'))


    def test_adding_pcpr_estimates(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        data = self.data.copy()
        data['left_pcpr_ha'] = 'b1_family1_model1'
        data['right_pcpr_ha'] = 'b2_family2_model2'
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
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Dodano lewy kosztorys na b1 family1 model1, z datą 2000-01-01. ' + \
                        'Dodano prawy kosztorys na b2 family2 model2, z datą 2000-01-02.'

        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

    def test_remove_pcpr_estimates(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        p1 = PCPR_Estimate.objects.create(patient=patient1,
            ear='left', ha_make='m', ha_family='f', ha_model='m', date='2000-01-01')
        p2 = PCPR_Estimate.objects.create(patient=patient1,
            ear='right', ha_make='m1', ha_family='f1', ha_model='m1', date='2000-01-02')
        Reminder.objects.create(pcpr=p1)
        Reminder.objects.create(pcpr=p2)
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
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Usunięto lewy kosztorys na m f m, z datą 2000-01-01. ' + \
                        'Usunięto prawy kosztorys na m1 f1 m1, z datą 2000-01-02.'

        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

    def test_adding_invoice(self):
        self.client.login(username='john', password='glassonion')
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
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Dodano lewą fakturę na b1 family1 model1, z datą 2000-01-01. ' + \
                        'Dodano prawą fakturę na b1 family1 model2, z datą 2000-01-02.'

        self.assertEqual(new_info.note, expected_note.decode('utf-8'))


    def test_remove_invoice(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        i1 = HA_Invoice.objects.create(patient=patient1,
                                     ear='left', ha_make='m', ha_family='f', ha_model='m', date='2000-01-01')
        i2 = HA_Invoice.objects.create(patient=patient1,
                                     ear='right', ha_make='m1', ha_family='f1', ha_model='m1', date='2000-01-01')
        Reminder.objects.create(invoice=i1)
        Reminder.objects.create(invoice=i2)
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
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Usunięto lewą fakturę na m f m, z datą 2000-01-01. ' + \
                        'Usunięto prawą fakturę na m1 f1 m1, z datą 2000-01-01.'
        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

    def test_collection_procedure(self):
        self.client.login(username='john', password='glassonion')
        patient1 = Patient.objects.get(id=1)
        patient2 = Patient.objects.get(id=1)
        n1 = NFZ_Confirmed.objects.create(patient=patient1,
                                     side='left',
                                     date='2000-01-01')
        n2 = NFZ_Confirmed.objects.create(patient=patient1,
                                     side='right',
                                     date='2000-01-02')
        n3 = NFZ_Confirmed.objects.create(patient=patient2,
                                            side='right',
                                            date='2000-01-02')
        p1 = PCPR_Estimate.objects.create(patient=patient1,
            ear='left', ha_make='m', ha_family='f', ha_model='m', date='2000-01-01')
        p2 = PCPR_Estimate.objects.create(patient=patient1,
            ear='right', ha_make='m', ha_family='f', ha_model='m', date='2000-01-01')
        i1 = HA_Invoice.objects.create(patient=patient1,
                                  ear='left', ha_make='m', ha_family='f', ha_model='m1', date='2000-01-01')
        i2 = HA_Invoice.objects.create(patient=patient1,
                                  ear='right', ha_make='m', ha_family='f', ha_model='m2', date='2000-01-01')
        Reminder.objects.create(nfz_confirmed=n1, activation_date=today)
        Reminder.objects.create(nfz_confirmed=n2, activation_date=today)
        Reminder.objects.create(nfz_confirmed=n3, activation_date=today)
        Reminder.objects.create(pcpr=p1, activation_date=today)
        Reminder.objects.create(pcpr=p2, activation_date=today)
        Reminder.objects.create(invoice=i1, activation_date=today)
        Reminder.objects.create(invoice=i2, activation_date=today)
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

        # should create a new info to show in history of actions
        new_info = NewInfo.objects.get(id=1)
        expected_note = 'Odebrano lewy aparat m f m1, z datą 2000-01-01. ' + \
                        'Odebrano prawy aparat m f m2, z datą 2000-01-01.'
        self.assertEqual(new_info.note, expected_note.decode('utf-8'))

        # reminders
        # 6 reminders from nfz, pcpr and invoices should be set to incative,
        # additional 2 are to be created in collection, additional one should
        # be left as active
        self.assertEqual(len(Reminder.objects.all()), 9)
        self.assertEqual(len(Reminder.objects.active()), 1)

    def test_remove_audiogram(self):
        self.client.login(username='john', password='glassonion')
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


class TestRemindersView(TestCase):
    def setUp(self):
        user_john = create_user()
        patient1 = create_patient(user_john, first_name='Jóść', last_name='Óąźcsd')
        patient2 = create_patient(user_john, first_name='łas', last_name='łąć')
        NFZ_Confirmed.objects.create(patient=patient1, date=today, side='left')
        NFZ_Confirmed.objects.create(patient=patient1, date=today, side='right')


    def test_anonymous(self):
        '''should redirect to login'''
        url = reverse('crm:reminders')
        expected_url = reverse('login') + '?next=/reminders/'
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

    def test_logged_in_2_reminders(self):
        self.client.login(username='john', password='glassonion')
        Reminder.objects.create(
            nfz_confirmed=NFZ_Confirmed.objects.get(id=1), activation_date=today)
        Reminder.objects.create(
            nfz_confirmed=NFZ_Confirmed.objects.get(id=2), activation_date=today)
        response = self.client.post(reverse('crm:reminders'))
        # should give code 200
        assert response.status_code == 200
        self.assertEqual(len(response.context['reminders_list']), 2)


class TestReminderView(TestCase):
    def setUp(self):
        user_john = create_user()
        patient1 = create_patient(user_john)
        
    def test_anonymous(self):
        '''should redirect to login'''
        url = reverse('crm:reminder', args=(1,))
        expected_url = reverse('login') + '?next=/1/reminder/'
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

    def test_logged_in_nfz(self):
        self.client.login(username='john', password='glassonion')
        nfz = NFZ_Confirmed.objects.create(
            patient=Patient.objects.get(id=1), date=today, side='left')
        Reminder.objects.create(nfz_confirmed=nfz, activation_date=today)
        url = reverse('crm:reminder', args=(1,))
        response = self.client.post(url)
        # should give code 200
        assert response.status_code == 200
        self.assertEqual(response.context['reminder_id'], 1)
        exp_subj = 'John Smith1, w dniu: %s otrzymano POTWIERDZONY wniosek NFZ lewy' % today.strftime(
            "%d.%m.%Y")
        self.assertEqual(response.context['subject'], exp_subj)

    def test_logged_in_ha(self):
        self.client.login(username='john', password='glassonion')
        ha = Hearing_Aid.objects.create(
            patient=Patient.objects.get(id=1),
            ha_make='m',
            ha_family='f',
            ha_model='m1',
            ear='left'
        )
        Reminder.objects.create(
            ha=ha, activation_date=today)
        url = reverse('crm:reminder', args=(1,))
        response = self.client.post(url)
        # should give code 200
        assert response.status_code == 200
        self.assertEqual(response.context['reminder_id'], 1)
        exp_subj = 'John Smith1, w dniu: %s wydano aparat m f m1 lewy' % today.strftime(
            "%d.%m.%Y")
        self.assertEqual(response.context['subject'], exp_subj)


class TestInactivateReminderView(TestCase):
    def setUp(self):
        user_john = create_user()
        patient1 = create_patient(user_john)

    def test_anonymous(self):
        '''should redirect to login'''
        url = reverse('crm:inactivate_reminder', args=(1,))
        expected_url = reverse('login') + '?next=/1/inactivate_reminder/'
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

    def test_logged_in_nfz(self):
        self.client.login(username='john', password='glassonion')
        nfz = NFZ_Confirmed.objects.create(
            patient=Patient.objects.get(id=1), date=today, side='left')
        r = Reminder.objects.create(nfz_confirmed=nfz, activation_date=today)
        url = reverse('crm:inactivate_reminder', args=(1,))
        expected_url = reverse('crm:reminders')
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)
        r.refresh_from_db()
        self.assertFalse(r.active)


class TestInvoiceCreateView(TestCase):
    def setUp(self):
        user_john = create_user()
        patient1 = create_patient(user_john)

    def test_anonymous(self):
        '''should redirect to login'''
        url = reverse('crm:invoice_create')
        expected_url = reverse('login') + '?next=/invoice_create/'
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)

    def test_logged_in(self):
        self.client.login(username='john', password='glassonion')
        # nfz = NFZ_Confirmed.objects.create(
        #     patient=Patient.objects.get(id=1), date=today, side='left')
        # r = Reminder.objects.create(nfz_confirmed=nfz, activation_date=today)
        url = reverse('crm:inactivate_reminder', args=(1,))
        expected_url = reverse('crm:reminders')
        response = self.client.post(url, follow=True)
        # should give code 200 as follow is set to True
        assert response.status_code == 200
        self.assertRedirects(response, expected_url,
                             status_code=302, target_status_code=200)
        r.refresh_from_db()
        self.assertFalse(r.active)
