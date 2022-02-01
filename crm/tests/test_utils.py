# -*- coding: utf-8 -*-
from django.test import TestCase

from crm.models import Hearing_Aid_Stock
from crm.utils import get_devices


class Test_Get_Devices(TestCase):
    def test_get_devices_1HA(self):
        # 1 HA in db
        Hearing_Aid_Stock.objects.create(
            make='Berna',
            family='WIN',
            model='102'
        )

        # should create a dict
        self.assertEqual(get_devices(Hearing_Aid_Stock), {
                         'Berna': {'WIN': ['102']}})

    def test_get_devices_2HA_same_make(self):
        # 2 HA in db, same make
        Hearing_Aid_Stock.objects.create(
            make='Berna',
            family='WIN',
            model='102'
        )
        Hearing_Aid_Stock.objects.create(
            make='Berna',
            family='WIN2',
            model='1022'
        )
        # should create a dict
        self.assertEqual(get_devices(Hearing_Aid_Stock), {
                         'Berna': {'WIN': ['102'], 'WIN2': ['1022']}})

    def test_get_devices_2HA_same_family(self):
        # 2 HA in db, same family
        Hearing_Aid_Stock.objects.create(
            make='Berna',
            family='WIN',
            model='102'
        )
        Hearing_Aid_Stock.objects.create(
            make='Berna',
            family='WIN',
            model='1022'
        )
        # should create a dict
        self.assertEqual(get_devices(Hearing_Aid_Stock), {
                         'Berna': {'WIN': ['102', '1022']}})

    def test_get_devices_2HA_same_model(self):
        # 2 HA in db, same model, should have only one in resulting dict
        Hearing_Aid_Stock.objects.create(
            make='Berna',
            family='WIN',
            model='102'
        )
        Hearing_Aid_Stock.objects.create(
            make='Berna',
            family='WIN',
            model='102'
        )
        # should create a dict
        self.assertEqual(get_devices(Hearing_Aid_Stock), {
                         'Berna': {'WIN': ['102']}})
