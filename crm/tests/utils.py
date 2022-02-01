# -*- coding: utf-8 -*-
import os
from django.core.files.temp import NamedTemporaryFile
from django.core import files
from crm.models import SZOI_File


def create_szoi_file(path_to_file):
    '''to prevent SuspiciousFileOperation error content of a file is written to the
    NamdedTemporaryFile object, accepts stirng (path to a file), returns SZOI_File object'''
    named_temp_file = NamedTemporaryFile(delete=True)

    test_file = open(os.getcwd() + path_to_file, 'rb')

    for line in test_file:
        named_temp_file.write(line)

    oryginal_file_name = path_to_file.split('/')[-1]
    temp_file = files.File(named_temp_file, name=oryginal_file_name)
    s = SZOI_File.objects.create(file=temp_file)
    return s