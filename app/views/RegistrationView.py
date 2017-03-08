import csv
from itertools import zip_longest

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.formats import date_format
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse

from lib.ResourceView import ResourceView, bind_model
from app.models import Event, Registration, Committee
from app.forms import RegistrationForm, RegistrationsForm
from app.views import EventView


class RegistrationView(LoginRequiredMixin, ResourceView):
	models = [Event, Registration]

	@bind_model
	def index(self, request, event):
		self.check_user(event.committee.chairman)

		regs = event.registration_set.filter(withdrawn_at=None)

		if request.GET['format'] == 'csv':
			response = HttpResponse(content_type='text/csv')
			response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(event.name)

			writer = csv.writer(response)
			writer.writerow(('#', 'Voornaam', 'Achternaam', 'Emailadres', 'Inschrijfdatum', event.note_field))

			for i, reg in enumerate(regs):
				if not reg.is_backup():
					writer.writerow((i, reg.participant.first_name, reg.participant.last_name, reg.participant.email, date_format(reg.created_at, 'SHORT_DATETIME_FORMAT'), reg.note))

			return response

	@bind_model
	def store(self, request, event):
		if request.GET['role'] == 'cm-committee':
			# Bulk registration of whole committee by chairman

			# Get committee that was POSTed and check if user is chairman
			committee = Committee.objects.get(name=request.POST['committee'])
			self.check_user(committee.chairman)

			# Register all members for event, creating a new Registration instance if one does not exist yet
			for member in committee.members.all():
				registration, created = Registration.objects.get_or_create(event=event, participant=member)
				registration.withdrawn_at = None
				registration.save()

			messages.success(request, "Commissie {} geregistreerd!".format(committee.name))
			return redirect('event-detail', event.pk)
		elif request.GET['role'] == 'cm-admin':
			# Bulk registration of users as chairman administrating the event
			self.check_user(event.committee.chairman)

			# Create list of tuples from three lists of inputs
			rows = list(zip_longest(
				request.POST.getlist('username'),
				request.POST.getlist('note'),
				request.POST.getlist('date')
			))

			# Build list of forms
			forms = [RegistrationsForm(event, data={
				'username': username,
				'note': note,
				'date': date
			}) for username, note, date in rows]

			count = 0
			for form in forms:
				if form.is_valid():
					registration, created = Registration.objects.get_or_create(
						event=event,
						participant=form.cleaned_data['username']
					)

					registration.note = form.cleaned_data.get('note', '')
					registration.created_at = form.cleaned_data.get('date', timezone.now())
					registration.withdrawn_at = None

					registration.save()
					count += 1
				else:
					messages.error(request, form.errors)

			if count > 0:
				messages.success(request, "{} inschrijvingen toegevoegd!".format(count))
			return redirect('event-edit', event.pk)
		elif request.GET['role'] == 'user':
			form = RegistrationForm(event, data=request.POST)

			# For a new registration, the registered field is required
			form.fields['registered'].required = True

			if form.is_valid():
				registration = Registration(
					event=event,
					participant=request.user,
					note=form.cleaned_data.get('note', '')
				)

				registration.save()

				messages.success(request, "Inschrijving geregistreerd!")
				return redirect('event-detail', event.pk)
			else:
				# Render previous page with validation errors
				event_view = EventView(self.route, self.request)
				return event_view.show(self.request, event.pk, form=form)

	@bind_model
	def edit(self, request, event, registration, form=None):
		self.check_user(event.committee.chairman)

		if form is None:
			form = RegistrationForm(event, registration)

		return render(request, 'registration_edit.html', {
			'event': event,
			'registration': registration,
			'form': form
		})

	@bind_model
	def update(self, request, event, registration):
		form = RegistrationForm(event, data=request.POST)

		def process_form():
			registration.note = form.cleaned_data.get('note', '')

			if form.cleaned_data['registered']:
				registration.withdrawn_at = None
			else:
				registration.withdrawn_at = timezone.now()

			registration.save()

		if request.GET['role'] == 'cm-admin':
			# POSTing the form as an chairman administrating the event
			self.check_user(event.committee.chairman)

			if form.is_valid():
				process_form()
				messages.success(request, "Inschrijving bijgewerkt!")
				return redirect('event-edit', event.pk)
			else:
				# Render previous page with validation errors
				registration_view = RegistrationView(self.route, self.request)
				return registration_view.edit(self.request, event.pk, form=form)
		elif request.GET['role'] == 'user':
			# POSTing the form as an user updating their own registration
			self.check_user(registration.participant)

			# Make sure deadline hasn't passed
			if event.is_expired():
				raise PermissionDenied

			if form.is_valid():
				process_form()
				messages.success(request, "Inschrijving bijgewerkt!")
				return redirect('event-detail', event.pk)
			else:
				# Render previous page with validation errors
				event_view = EventView(self.route, self.request)
				return event_view.show(self.request, event.pk, form=form)

	@bind_model
	def create(self, request, event):
		form = RegistrationsForm(event=event)

		# Get list of usernames for suggestions
		usernames = User.objects.values_list('username', flat=True)

		return render(request, 'registration_create.html', {
			'event': event,
			'form': form,
			'usernames': usernames
		})
