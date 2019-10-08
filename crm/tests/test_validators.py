# -*- coding: utf-8 -*-
import os
import pytest
# import shutil
# import tempfile

# from django.conf import settings
from django.test import TestCase
from django.core.files import File
from django.core.exceptions import ValidationError


from crm.validators import xls_only

class TestXLS_Only(TestCase):
    def test_xls_only_with_xls_file(self):
        file_path = os.getcwd() + '/crm/tests/test_files/empty.xls'
        f = File(open(file_path))

        # should pass and not raise errors
        self.assertIsNone(xls_only(f))

    def test_xls_only_with_csv_file(self):
        file_path = os.getcwd() + '/crm/tests/test_files/empty.csv'
        f = File(open(file_path))

        # should raise ValidationError
        self.assertRaises(ValidationError, xls_only, f)

