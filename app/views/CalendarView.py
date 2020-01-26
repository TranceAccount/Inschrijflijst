from django.shortcuts import render
from django.contrib import messages
from django.utils.translation import ugettext as _

from app.services import GoogleCalendarService
from lib.BetterView import BetterView


class CalendarView(BetterView):
	handler_method_names = {
		'show': {'get': 'show'},
	}

	def show(self, request):
		try:
			cal_service = GoogleCalendarService(request.base_url)
			return render(request, 'calendar.html', {'calendar': cal_service.calendar})
		except RuntimeError:
			messages.error(request, _("Geen kalender ingesteld."))
			return render(request, 'calendar.html')
