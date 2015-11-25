from django.conf.urls import patterns, url, include

from . import views

urlpatterns = [
	url(r'^$', views.index, name='test'),
	url(r'^index/$', views.index, name='index'),
	# url(r'^(?P<response_id>[0-9]+)/result/$', views.result, name='result'),
	url(r'^result/(?P<response_id>.+)/$', views.result, name='result'),
	url(r'^download_all/(?P<responses_id>.+)/$', views.download_all, name='download_all'),
	url(r'^(?P<response_id>[0-9]+)/download/$', views.download, name='download'),
	url(r'^auth/$', views.auth, name='auth'),
	url(r'^(?P<response_id>[0-9]+)/result_all/$', views.result_all, name='result_all'),
	url(r'^get_all/$', views.get_all, name='get_all'),
]