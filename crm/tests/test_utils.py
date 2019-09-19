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
        # should be 10 lines in the file
        self.assertEqual(sum(1 for line in f), 10)
        # create SZOI_File instance with the above file
        s = SZOI_File.objects.create(file=File(f))

        res = stock_update(s)
        # should create 10 Hearing_Aid_Stock
        self.assertEqual(Hearing_Aid_Stock.objects.all().count(), 10)

        # should create no Other_Item_Stock
        self.assertEqual(Other_Item_Stock.objects.all().count(), 0)

        # should return 10 Hearing_Aid_Stock instances
        self.assertEqual(len(res['ha']), 10)
        
        f.close()
        pass



    def test_stock_update_ignore_typos(self):
        '''ignore typos in "ZERENA5", "Audibel SILVERTRIC" and "JUNA7 NANO"'''
        pass

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
