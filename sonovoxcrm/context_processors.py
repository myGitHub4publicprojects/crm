from crm. models import (Reminder_Collection, Reminder_Invoice,
                        Reminder_PCPR, Reminder_NFZ_Confirmed, Reminder_NFZ_New)


def reminders_processor(request):
    all_reminders = sum([len(Reminder_NFZ_New.objects.active()),
                         len(Reminder_NFZ_Confirmed.objects.active()),
                         len(Reminder_PCPR.objects.active()),
                         len(Reminder_Invoice.objects.active()),
                         len(Reminder_Collection.objects.active()),                        
                        ])
    return {'reminders': all_reminders }
