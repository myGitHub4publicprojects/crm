# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import pytest
import shutil
import tempfile


from django.conf import settings
from django.test import TestCase
from mixer.backend.django import mixer
from django.core.files import File
from crm.stock_updater import stock_update
from crm.models import (SZOI_File, Hearing_Aid_Stock, SZOI_File_Usage,SZOI_Errors)


class Test_Stock_Update(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        settings.MEDIA_ROOT = self.test_dir

    def test_stock_update_empty(self):
        '''test file is empty'''
        test_file = os.getcwd() + '/crm/tests/test_files/empty.xls'
        f = open(test_file)
       # create SZOI_File and SZOI_File_Usage instance with the above file
        szoi_file = SZOI_File.objects.create(file=File(f))
        szoi_file_usage = SZOI_File_Usage.objects.create(szoi_file=szoi_file)

        stock_update(szoi_file, szoi_file_usage)
        # should create 0 Hearing_Aid_Stock
        self.assertEqual(Hearing_Aid_Stock.objects.all().count(), 0)

        f.close()


    def test_stock_update_create_10HA(self):
        '''test file contains 10 lines with HA'''
        test_file = os.getcwd() + '/crm/tests/test_files/szoi10HA.xls'
        f = open(test_file)
        # create SZOI_File and SZOI_File_Usage instance with the above file
        szoi_file = SZOI_File.objects.create(file=File(f))
        szoi_file_usage = SZOI_File_Usage.objects.create(szoi_file=szoi_file)

        res = stock_update(szoi_file, szoi_file_usage)
        # should create 10 Hearing_Aid_Stock
        self.assertEqual(Hearing_Aid_Stock.objects.all().count(), 10)

        # should return 10 Hearing_Aid_Stock instances
        self.assertEqual(len(res['ha_new']), 10)
        
        f.close()

    def test_stock_update_create_new_10HA(self):
        '''test file contains 10 lines with HA
        there is already one HA, it still be there after stock update'''
        Hearing_Aid_Stock.objects.create(make='oldmake', family='oldfamily', model='oldmodel')
        test_file = os.getcwd() + '/crm/tests/test_files/szoi10HA.xls'
        f = open(test_file)
        # create SZOI_File and SZOI_File_Usage instance with the above file
        szoi_file = SZOI_File.objects.create(file=File(f))
        szoi_file_usage = SZOI_File_Usage.objects.create(szoi_file=szoi_file)

        res = stock_update(szoi_file, szoi_file_usage)
        # should create 10 Hearing_Aid_Stock, should be 11 in total
        self.assertEqual(Hearing_Aid_Stock.objects.all().count(), 11)

        # should return 10 Hearing_Aid_Stock instances
        self.assertEqual(len(res['ha_new']), 10)

        f.close()

    def test_stock_update_with_errors_in_file(self):
        '''second and third lines in a file have only 2 items,
        fourth line has none of the expected text'''
        test_file = os.getcwd() + '/crm/tests/test_files/szoi10haError_shortLine.xls'
        f = open(test_file)
       
        # create SZOI_File and SZOI_File_Usage instance with the above file
        szoi_file = SZOI_File.objects.create(file=File(f))
        szoi_file_usage = SZOI_File_Usage.objects.create(szoi_file=szoi_file)

        res = stock_update(szoi_file, szoi_file_usage)

        # should create 7 Hearing_Aid_Stock
        self.assertEqual(Hearing_Aid_Stock.objects.all().count(), 7)

        # should return 7 Hearing_Aid_Stock instances
        self.assertEqual(len(res['ha_new']), 7)

        errors = SZOI_Errors.objects.all()
        # should create 3 SZOI_Errors instances
        self.assertEqual(errors.count(), 3)

        error1 = errors[0]
        error2 = errors[1]
        error3 = errors[2]
        self.assertEqual(
            error1.line, u"[u'2', u'BERNAFON AG', u'', u'', u'', u'', u'', u'', u'']")
        self.assertEqual(
            error2.line, u"[u'3', u'SONOVA AG', u'', u'', u'', u'', u'', u'', u'']")
        self.assertEqual(error3.error_log,
                         '"Kod środka" not recognized"')
        
        f.close()



    def test_stock_update_with_errors_in_file_ha(self):
        '''HA name format is changed, HA name in line 2 is "test" '''
        test_file = os.getcwd() + '/crm/tests/test_files/szoi10ha_error_name.xls'
        f = open(test_file)
       
        # create SZOI_File and SZOI_File_Usage instance with the above file
        szoi_file = SZOI_File.objects.create(file=File(f))
        szoi_file_usage = SZOI_File_Usage.objects.create(szoi_file=szoi_file)

        res = stock_update(szoi_file, szoi_file_usage)

        # should create 9 Hearing_Aid_Stock
        self.assertEqual(Hearing_Aid_Stock.objects.all().count(), 9)


        # should return 9 Hearing_Aid_Stock instances
        self.assertEqual(len(res['ha_new']), 9)

        errors = SZOI_Errors.objects.all()
        # should create 1 SZOI_Errors instances
        self.assertEqual(errors.count(), 1)
        
        f.close()


    def test_stock_update_ignore_typos(self):
        '''handle typos in "ZERENA5", "Audibel SILVERTRIC" and "JUNA7 NANO"
        there are 2470 lines with items in a file,
        there are 1219 lines with 'P.084.' or 'P.084.' code (HA),
        there are 17 lines with 'P.086.' or 'P.087.' code (Other items),
        there are 1234 lines where code contains '.01'
        '''
        test_file = os.getcwd() + '/crm/tests/test_files/szoifull.xls'
        f = open(test_file)

        # create SZOI_File and SZOI_File_Usage instance with the above file
        szoi_file = SZOI_File.objects.create(file=File(f))
        szoi_file_usage = SZOI_File_Usage.objects.create(szoi_file=szoi_file)

        res = stock_update(szoi_file, szoi_file_usage)
        
        h_all = Hearing_Aid_Stock.objects.all()
        # should create 1131 Hearing_Aid_Stock
        self.assertEqual(h_all.count(), 1131)

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

        # should return 1131 Hearing_Aid_Stock instances
        self.assertEqual(len(res['ha_new']), 1131)

        f.close()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)
