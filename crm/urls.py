from django.conf.urls import url
from . import views

app_name = 'crm'
urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^advanced_search/$', views.advancedsearch, name='advanced_search'),
	url(r'^create/$', views.create, name='create'),
	url(r'^select_noach_file/$', views.select_noach_file, name='select_noach_file'),
	url(r'^store/$', views.store, name='store'),
	url(r'^reminders/$', views.reminders, name='reminders'),
	url(r'^duplicate_check/$', views.duplicate_check, name='duplicate_check'),
    url(r'^(?P<reminder_id>[0-9]+)/reminder_nfz_new/$',
        views.reminder_nfz_new, name='reminder_nfz_new'),
    url(r'^(?P<reminder_id>[0-9]+)/reminder_nfz_confirmed/$',
        views.reminder_nfz_confirmed, name='reminder_nfz_confirmed'),
    url(r'^(?P<reminder_id>[0-9]+)/reminder_pcpr/$',
        views.reminder_pcpr, name='reminder_pcpr'),
    url(r'^(?P<reminder_id>[0-9]+)/reminder_invoice/$',
        views.reminder_invoice, name='reminder_invoice'),
    url(r'^(?P<reminder_id>[0-9]+)/reminder_collection/$',
        views.reminder_collection, name='reminder_collection'),
	url(r'^import_from_noach/$', views.import_from_noach, name='import_from_noach'),     # this is probably not needed but html file needs to be adjusted
	url(r'^(?P<patient_id>[0-9]+)/edit/$', views.edit, name='edit'),
	url(r'^(?P<patient_id>[0-9]+)/updating/$', views.updating, name='updating'),
	url(r'^(?P<patient_id>[0-9]+)/deleteconfirm/$', views.deleteconfirm, name='deleteconfirm'),
	url(r'^(?P<patient_id>[0-9]+)/delete/$', views.delete_patient, name='delete'),
    url(r'^(?P<patient_id>[0-9]+)/invoice_create/$',
        views.invoice_create, name='invoice_create'),
	url(r'^(?P<invoice_id>[0-9]+)/invoice_detail/$',
	    views.invoice_detail, name='invoice_detail'),
    url(r'^(?P<invoice_id>[0-9]+)/invoice_update/$',
        views.invoice_update, name='invoice_update'),
    # url invoice delete
    
    url(r'^(?P<patient_id>[0-9]+)/pcpr_create/$',
        views.pcpr_create, name='pcpr_create'),
	url(r'^(?P<pcpr_id>[0-9]+)/pcpr_detail/$',
	    views.pcpr_detail, name='pcpr_detail'),
    url(r'^(?P<pcpr_id>[0-9]+)/pcpr_update/$',
        views.pcpr_update, name='pcpr_update'),
]
