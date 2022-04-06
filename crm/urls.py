from django.urls import re_path
from . import views


app_name = 'crm'
urlpatterns = [
    re_path(r'^$',
            views.Index.as_view(), name='index'),
	re_path(r'^advanced_search/$', views.advancedsearch, name='advanced_search'),
	re_path(r'^create/$', views.create, name='create'),
	re_path(r'^store/$', views.store, name='store'),
	re_path(r'^reminders/$', views.reminders, name='reminders'),
	re_path(r'^duplicate_check/$', views.duplicate_check, name='duplicate_check'),
    re_path(r'^(?P<reminder_id>[0-9]+)/reminder_nfz_confirmed/$',
        views.reminder_nfz_confirmed, name='reminder_nfz_confirmed'),
    re_path(r'^(?P<reminder_id>[0-9]+)/reminder_pcpr/$',
        views.reminder_pcpr, name='reminder_pcpr'),
    re_path(r'^(?P<reminder_id>[0-9]+)/reminder_invoice/$',
        views.reminder_invoice, name='reminder_invoice'),
    re_path(r'^(?P<reminder_id>[0-9]+)/reminder_collection/$',
        views.reminder_collection, name='reminder_collection'),
	re_path(r'^(?P<patient_id>[0-9]+)/edit/$', views.edit, name='edit'),
	re_path(r'^(?P<patient_id>[0-9]+)/updating/$', views.updating, name='updating'),
	re_path(r'^(?P<patient_id>[0-9]+)/deleteconfirm/$', views.deleteconfirm, name='deleteconfirm'),
	re_path(r'^(?P<patient_id>[0-9]+)/delete/$', views.delete_patient, name='delete'),

    
    re_path(r'^szoi_create/$',
            views.SZOICreate.as_view(), name='szoi_create'),
    re_path(r'^(?P<pk>[0-9]+)/szoi_detail/$',
        views.SZOIDetail.as_view(), name='szoi_detail'),
    re_path(r'^szoi_list/$', views.SZOIList.as_view(), name='szoi_list'),

    re_path(r'^szoi_usage_create/$',
            views.SZOI_UsageCreate.as_view(), name='szoi_usage_create'),
    re_path(r'^(?P<pk>[0-9]+)/szoi_usage_detail/$',
        views.SZOI_UsageDetail.as_view(), name='szoi_usage_detail'),
]
