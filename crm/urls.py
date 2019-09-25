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
	url(r'^(?P<patient_id>[0-9]+)/edit/$', views.edit, name='edit'),
	url(r'^(?P<patient_id>[0-9]+)/updating/$', views.updating, name='updating'),
	url(r'^(?P<patient_id>[0-9]+)/deleteconfirm/$', views.deleteconfirm, name='deleteconfirm'),
	url(r'^(?P<patient_id>[0-9]+)/delete/$', views.delete_patient, name='delete'),
    url(r'^(?P<patient_id>[0-9]+)/invoice_create/$',
        views.invoice_create, name='invoice_create'),
	url(r'^(?P<invoice_id>[0-9]+)/invoice_detail/$',
	    views.invoice_detail, name='invoice_detail'),
    url(r'^(?P<pk>[0-9]+)/invoice_update/$',
        views.InvoiceUpdate.as_view(), name='invoice_update'),
    url(r'^invoice_list/$', views.InvoiceList.as_view(), name='invoice_list'),

    url(r'^(?P<invoice_id>[0-9]+)/corrective_invoice_create/$',
            views.corrective_invoice_create, name='corrective_invoice_create'),
   	url(r'^(?P<cinvoice_id>[0-9]+)/corrective_invoice_detail/$',
        views.corrective_invoice_detail, name='corrective_invoice_detail'),
    url(r'^(?P<cinvoice_id>[0-9]+)/corrective_invoice_update/$',
        views.corrective_invoice_update, name='corrective_invoice_update'),
    url(r'^(?P<pk>[0-9]+)/delete_corrective_invoice/$',
        views.CorrectiveInvoiceDelete.as_view(), name='delete_corrective_invoice'),

    url(r'^(?P<patient_id>[0-9]+)/pcpr_create/$',
        views.pcpr_create, name='pcpr_create'),
	url(r'^(?P<pcpr_id>[0-9]+)/pcpr_detail/$',
	    views.pcpr_detail, name='pcpr_detail'),
    url(r'^(?P<pcpr_id>[0-9]+)/pcpr_update/$',
        views.pcpr_update, name='pcpr_update'),

    url(r'^towary/$', login_required(TemplateView.as_view(
        template_name="crm/towary.html")), name='towary'),
    url(r'^ha_list/$', views.HAStockList.as_view(), name='ha_list'),
    url(r'^add_ha/$', views.HAStockCreate.as_view(), name='add_ha'),
    url(r'^(?P<pk>[0-9]+)/edit_ha/$', views.HAStockUpdate.as_view(), name='edit_ha'),
    url(r'^(?P<pk>[0-9]+)/delete_ha/$',
        views.HAStockDelete.as_view(), name='delete_ha'),
    url(r'^other_list/$', views.OtherStockList.as_view(), name='other_list'),
    url(r'^add_other/$', views.OtherStockCreate.as_view(), name='add_other'),
    url(r'^(?P<pk>[0-9]+)/edit_other/$',
        views.OtherStockUpdate.as_view(), name='edit_other'),
    url(r'^(?P<pk>[0-9]+)/delete_other/$',
        views.OtherStockDelete.as_view(), name='delete_other'),
    
    url(r'^szoi_create/$',
            views.SZOICreate.as_view(), name='szoi_create'),
    url(r'^(?P<pk>[0-9]+)/szoi_detail/$',
        views.SZOIDetail.as_view(), name='szoi_detail'),
    url(r'^szoi_list/$', views.SZOIList.as_view(), name='szoi_list'),

    url(r'^szoi_usage_create/$',
            views.SZOI_UsageCreate.as_view(), name='szoi_usage_create'),
    url(r'^(?P<pk>[0-9]+)/szoi_usage_detail/$',
        views.SZOI_UsageDetail.as_view(), name='szoi_usage_detail'),
    # url(r'^szoi_usage_list/$', views.SZOI_UsageList.as_view(), name='szoi_usage_list'),
]
