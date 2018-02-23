from crm. models import Reminder


def reminders_processor(request):
    return {'reminders': len(Reminder.objects.active()) }
