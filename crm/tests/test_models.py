# -*- coding: utf-8 -*-
import os
from pdb import line_prefix
import pytest
import shutil, tempfile
from django.core.exceptions import ValidationError
from django.core.files.temp import NamedTemporaryFile
from django.core import files

from django.conf import settings
from django.test import TestCase
from mixer.backend.django import mixer
from django.core.files import File
from crm.models import SZOI_File



class Test_SZOI_File(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        settings.MEDIA_ROOT = self.test_dir

    def test_with_empty_file(self):
        '''the test file is empty'''
        named_temp_file = NamedTemporaryFile(delete=True)

        test_file = open(os.getcwd() + '/crm/tests/test_files/empty.xls', 'rb')
        # Write the in-memory file to the temporary file

        for line in test_file:
            named_temp_file.write(line)

        temp_file = files.File(named_temp_file, name='empty.xls')

        s = SZOI_File.objects.create(file=temp_file)

        # validate
        s.full_clean()

        # filename should be 'empty.xls'
        self.assertEqual(s.filename(), 'empty.xls')
        

    def test_with_csv_file(self):
        '''should not accept files other than .xls'''
        named_temp_file = NamedTemporaryFile(delete=True)

        test_file = open(os.getcwd() + '/crm/tests/test_files/empty.csv', 'rb')
        # Write the in-memory file to the temporary file

        for line in test_file:
            named_temp_file.write(line)

        temp_file = files.File(named_temp_file, name='empty.csv')

        s = SZOI_File.objects.create(file=temp_file)

        self.assertRaises(ValidationError, s.full_clean)


    def test_with_real_data(self):
        '''test file contains products'''
        named_temp_file = NamedTemporaryFile(delete=True)

        test_file = open(os.getcwd() + '/crm/tests/test_files/szoi10HA.xls', 'rb')
        # Write the in-memory file to the temporary file

        for line in test_file:
            named_temp_file.write(line)

        temp_file = files.File(named_temp_file, name='szoi10HA.xls')

        s = SZOI_File.objects.create(file=temp_file)
        

        # filename should be 'szoi10HA.xls'
        self.assertEqual(s.filename(), 'szoi10HA.xls')

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)
