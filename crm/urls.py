from django.conf.urls import url
from . import views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required


app_name = 'crm'
urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^advanced_search/$', views.advancedsearch, name='advanced_search'),
	url(r'^create/$', views.create, name='create'),
	url(r'^store/$', views.store, name='store'),
	url(r'^reminders/$', views.reminders, name='reminders'),
	url(r'^duplicate_check/$', views.duplicate_check, name='duplicate_check'),
    url(r'^(?P<reminder_id>[0-9]+)/reminder_nfz_confirmed/$',
        views.reminder_nfz_confirmed, name='reminder_nfz_confirmed'),
    url(r'^(?P<reminder_id>[0-9]+)/reminder_pcpr/$',
        views.reminder_pcpr, name='reminder_pcpr'),
    url(r'^(?P<reminder_id>[0-9]+)/reminder_invoice/$',
        views.reminder_invoice, name='reminder_invoice'),
    url(r'^(?P<reminder_id>[0-9]+)/reminder_collection/$',
        views.reminder_collection, name='reminder_collection'),
	url(r'^(?P<patient_id>[0-9]+)/edit/$', views.edit, name='edit'),
	url(r'^(?P<patient_id>[0-9]+)/updating/$', views.updating, name='updating'),
	url(r'^(?P<patient_id>[0-9]+)/deleteconfirm/$', views.deleteconfirm, name='deleteconfirm'),
	url(r'^(?P<patient_id>[0-9]+)/delete/$', views.delete_patient, name='delete'),

    
    url(r'^szoi_create/$',
            views.SZOICreate.as_view(), name='szoi_create'),
    url(r'^(?P<pk>[0-9]+)/szoi_detail/$',
        views.SZOIDetail.as_view(), name='szoi_detail'),
    url(r'^szoi_list/$', views.SZOIList.as_view(), name='szoi_list'),

    url(r'^szoi_usage_create/$',
            views.SZOI_UsageCreate.as_view(), name='szoi_usage_create'),
    url(r'^(?P<pk>[0-9]+)/szoi_usage_detail/$',
        views.SZOI_UsageDetail.as_view(), name='szoi_usage_detail'),
]
