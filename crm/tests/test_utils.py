# -*- coding: utf-8 -*-
import csv
import os
import pytest
import shutil
import tempfile

from django.conf import settings
from django.test import TestCase
from mixer.backend.django import mixer
from django.core.files import File
from crm.utils import stock_update
from crm.models import SZOI_File, Hearing_Aid_Stock, Other_Item_Stock


class Test_Stock_Update(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        settings.MEDIA_ROOT = self.test_dir

    def test_stock_update_create_10HA(self):
        '''test file contains 10 lines with HA'''
        test_file = os.getcwd() + '/crm/tests/test_files/szoi10ha.csv'
        f = open(test_file)
        # should be 18 lines in the file
        self.assertEqual(sum(1 for line in f), 18)
        # create SZOI_File instance with the above file
        s = SZOI_File.objects.create(file=File(f))

        res = stock_update(s)
        # should create 10 Hearing_Aid_Stock
        self.assertEqual(Hearing_Aid_Stock.objects.all().count(), 10)

        # should create no Other_Item_Stock
        self.assertEqual(Other_Item_Stock.objects.all().count(), 0)

        # should return 10 Hearing_Aid_Stock instances
        self.assertEqual(len(res['ha_new']), 10)
        
        f.close()


    def test_stock_update_ignore_typos(self):
        '''handle typos in "ZERENA5", "Audibel SILVERTRIC" and "JUNA7 NANO"'''
        test_file = os.getcwd() + '/crm/tests/test_files/szoi_full.csv'
        f = open(test_file)

        # create SZOI_File instance with the above file
        s = SZOI_File.objects.create(file=File(f))

        res = stock_update(s)
        
        h_all = Hearing_Aid_Stock.objects.all()
        # should create 1130 Hearing_Aid_Stock
        self.assertEqual(h_all.count(), 1130)

        # should not create invalid family name 'ZERENA5'
        z5 = h_all.filter(family='ZERENA5')
        self.assertFalse(z5.exists())

        # should create valid family name 'ZERENA 5'
        z_5 = h_all.filter(family='ZERENA 5')
        self.assertTrue(z_5.exists())

        # should not create invalid family name 'JUNA7'
        j7 = h_all.filter(family='JUNA7')
        self.assertFalse(j7.exists())

        # should create valid family name 'JUNA 7'
        j_7 = h_all.filter(family='JUNA 7')
        self.assertTrue(j_7.exists())

        # should not create invalid family name containing 'SILVERTRIC'
        a_s = h_all.filter(family__icontains='SILVERTRIC')
        self.assertFalse(a_s.exists())

        # should return 10 Hearing_Aid_Stock instances
        self.assertEqual(len(res['ha_new']), 1130)

        # should return 1 updated Hearing_Aid_Stock instance as there is duplicated HA in file
        self.assertEqual(len(res['ha_update']), 1)

        f.close()

    def test_stock_update_create_17OtherDevices(self):
        '''should create 17 Other_Item_Stock devices'''
        test_file = os.getcwd() + '/crm/tests/test_files/szoi_full.csv'
        f = open(test_file)
        # create SZOI_File instance with the above file
        s = SZOI_File.objects.create(file=File(f))
        res = stock_update(s)

        # should create 17 Other_Item_Stock
        self.assertEqual(Other_Item_Stock.objects.all().count(), 17)

        # should return 17 Other_Item_Stock instances
        self.assertEqual(len(res['other_new']), 17)

        # should return no upadted Other_Item_Stock instances
        self.assertEqual(len(res['other_update']), 0)
    

    def test_stock_update_update_existing_ha_prices(self):
        '''update price of 2 HA that are already in stock'''
        # should not create new Hearing_Aid_Stock
        pass

    def test_stock_update_update_existing_other_prices(self):
        '''update price of 2 Other Devices that are already in stock'''
        pass


    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)
