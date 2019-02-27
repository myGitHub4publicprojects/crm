from django.contrib import admin

from .models import (Patient, NewInfo, Invoice, Hearing_Aid, PCPR_Estimate,
                     Other_Item, HA_Invoice, Reminder)

admin.site.register(Patient)
admin.site.register(NewInfo)
admin.site.register(Invoice)
admin.site.register(Hearing_Aid)
admin.site.register(PCPR_Estimate)
admin.site.register(Other_Item)
admin.site.register(HA_Invoice)
admin.site.register(Reminder)
