# -*- coding: utf-8 -*-
import csv
import os
import pytest
import shutil, tempfile

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
        # create test file in main dir
        testfile = open('output.csv', 'w')
        testfile.close()

        # create object
        s = SZOI_File.objects.create(file=File(open('output.csv')))

        # remove test file from main dir
        os.remove('output.csv')

        # self.assertEqual(testfile.name, 'output.csv')
        self.assertEqual(s.filename(), 'output.csv')

    def test_with_real_data(self):
        '''test file contains products'''
        
        # create file
        csv_file = open('output.csv', mode='w')

        writer = csv.writer(
            csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        writer.writerow(['1', 'SONOVA AG', 'BOLERO B 30 P', 'NIE', '1682', 'PHONAK BOLERO B',
                         'P.084.00', 'APARAT SŁUCHOWY NA PRZEWODNICTWO POWIETRZNE PRZY JEDNOSTRONNYM UBYTKU SŁUCHU, ALBO DWA APARATY SŁUCHOWE NA PRZEWODNICTWO POWIETRZNE PRZY OBUSTRONNYM UBYTKU SŁUCHU - PACJENCI POWYŻEJ 26 RŻ.',
                         '3150.00'])
        writer.writerow(['2', 'BERNAFON AG', 'ZERENA 9 B 105', 'NIE', '1726', 'ZERENA 9 BTE', 'P.084.00',
                         'APARAT SŁUCHOWY NA PRZEWODNICTWO POWIETRZNE PRZY JEDNOSTRONNYM UBYTKU SŁUCHU, ALBO DWA APARATY SŁUCHOWE NA PRZEWODNICTWO POWIETRZNE PRZY OBUSTRONNYM UBYTKU SŁUCHU - PACJENCI POWYŻEJ 26 RŻ.',
                          '8100.00'])
        
        csv_file.close()
       
        # create object
        s = SZOI_File.objects.create(file=File(open('output.csv')))
        
        # remove test file from main dir
        os.remove('output.csv')

        # self.assertEqual(testfile.name, 'output.csv')
        self.assertEqual(s.filename(), 'output.csv')

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)
