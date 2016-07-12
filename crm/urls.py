from django.conf.urls import url
from . import views

app_name = 'crm'
urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^create/$', views.create, name='create'),
	url(r'^store/$', views.store, name='store'),
	url(r'^(?P<patient_id>[0-9]+)/$', views.detail, name='detail'),
	url(r'^(?P<patient_id>[0-9]+)/edit/$', views.edit, name='edit'),
	url(r'^(?P<patient_id>[0-9]+)/updating/$', views.updating, name='updating')
]