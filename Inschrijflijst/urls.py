"""Inschrijflijst URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from app.views import EventView

urlpatterns = [
	url(r'^admin/', admin.site.urls, name='admin'),

	url(r'^login/$', auth_views.login, name='login'),
	url(r'^logout/$', auth_views.logout, name='logout'),

	url(r'^events/$', EventView.as_view('index'), name='event-list'),
	url(r'^events/create$', EventView.as_view('create'), name='event-create'),
	url(r'^events/(?P<pk>\d+)$', EventView.as_view('show'), name='event-detail'),
	url(r'^events/(?P<pk>\d+)/edit$', EventView.as_view('edit'), name='event-edit')
]