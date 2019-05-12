from django.contrib import admin

from .models import (Patient, NewInfo, PCPR_Estimate, Invoice,
                    Hearing_Aid, Hearing_Aid_Stock, Other_Item, Other_Item_Stock,
                    NFZ_Confirmed, NFZ_New, Reminder_Collection, Reminder_Invoice,
                    Reminder_PCPR, Reminder_NFZ_Confirmed, Reminder_NFZ_New)


admin.site.register(Patient)
admin.site.register(NewInfo)
admin.site.register(PCPR_Estimate)
admin.site.register(Invoice)
admin.site.register(Hearing_Aid)
admin.site.register(Hearing_Aid_Stock)
admin.site.register(Other_Item)
admin.site.register(Other_Item_Stock)
admin.site.register(NFZ_Confirmed)
admin.site.register(NFZ_New)
admin.site.register(Reminder_Collection)
admin.site.register(Reminder_Invoice)
admin.site.register(Reminder_PCPR)
admin.site.register(Reminder_NFZ_Confirmed)
admin.site.register(Reminder_NFZ_New)