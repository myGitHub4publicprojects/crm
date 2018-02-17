from django.contrib import admin

from .models import Patient, NewInfo

admin.site.register(Patient)
admin.site.register(NewInfo)
