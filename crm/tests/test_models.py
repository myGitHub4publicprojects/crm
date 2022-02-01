# -*- coding: utf-8 -*-
import shutil, tempfile
from django.core.exceptions import ValidationError

from django.conf import settings
from django.test import TestCase

from crm.tests.utils import create_szoi_file

class Test_SZOI_File(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        settings.MEDIA_ROOT = self.test_dir

    def test_with_empty_file(self):
        '''the test file is empty'''
        s = create_szoi_file('/crm/tests/test_files/empty.xls')

        # validate
        s.full_clean()

        # filename should be 'empty.xls'
        self.assertEqual(s.filename(), 'empty.xls')
        

    def test_with_csv_file(self):
        '''should not accept files other than .xls'''
        s = create_szoi_file('/crm/tests/test_files/empty.csv')

        self.assertRaises(ValidationError, s.full_clean)


    def test_with_real_data(self):
        '''test file contains products'''
        s = create_szoi_file('/crm/tests/test_files/szoi10HA.xls')

        # filename should be 'szoi10HA.xls'
        self.assertEqual(s.filename(), 'szoi10HA.xls')

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)