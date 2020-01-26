from django.shortcuts import render, redirect, reverse
from django.conf import settings
from django.contrib import messages
from django.utils.translation import ugettext as _

from lib.BetterView import BetterView, StaffRequiredMixin
from app.services import LDAPService, GoogleCalendarService, FlowService
from app.models import Committee


class AdminView(StaffRequiredMixin, BetterView):
	handler_method_names = {
		'show': {'get': 'show'},
		'sync-ldap': {'post': 'sync_ldap'},
		'calendar': {'post': 'calendar'},
		'calendar-flow': {'get': 'calendar_flow'}
	}

	def __init__(self, route, request):
		super().__init__(route, request)
		# Instantiate FlowService
		try:
			self.flow = FlowService(request.base_url + reverse('admin-calendar-flow'))
		except RuntimeError:
			self.flow = None
			messages.error(request, _("Google Kalender-verbinding niet mogelijk omdat Google OAuth niet ingesteld is."))

	def show(self, request):
		if self.flow:
			# Get authorization URL for link
			authorize_url = self.flow.get_authorize_url()

			# Try to instantiate GoogleCalendarService and get list of calendars
			try:
				cal_service = GoogleCalendarService(request.base_url)
				cals = cal_service.get_calendars()
				active_cal = cal_service.calendar
			except RuntimeError:
				cals = None
				active_cal = None

			return render(request, 'admin.html', {
				'authorize_url': authorize_url,
				'cals': cals,
				'active_cal': active_cal
			})
		else:
			return render(request, 'admin.html')

	def calendar(self, request):
		# Set 'active' calendar
		cal_service = GoogleCalendarService(request.base_url)
		cal_service.calendar = request.POST['calender_id']

		messages.success(request, _("Kalender ingesteld!"))
		return redirect('admin')

	def calendar_flow(self, request):
		# Callback from Google

		# Finish Flow
		self.flow.exchange(request.GET['code'])

		# Empty active calendar setting
		cal_service = GoogleCalendarService(request.base_url)
		cal_service.calendar = None

		messages.success(request, _("Google-account gekoppeld!"))
		return redirect('admin')

	def sync_ldap(self, request):
		# Get committees from AD
		with LDAPService(settings.AUTH_LDAP_SERVER_URI, settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD) as ldap_service:
			committees = ldap_service.get_committees()

		# Update all committees from list of dicts
		Committee.update_committees(committees)

		messages.success(request, _("Commissies geupdatet!"))
		return redirect('admin')
