from django.db import models
from django.conf import settings
from django.utils.decorators import classonlymethod
from django.contrib.auth import get_user_model

from .Registration import Registration
from app.mails import RegistrationNotificationMail


class Committee(models.Model):
	name = models.CharField(max_length=25)
	chairman = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='chaired_committees')
	email = models.EmailField()
	members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='in_committees')
	super_members = models.BooleanField(default=False)

	def __str__(self):
		return self.name

	def enroll(self, mailer, event, request):
		"""
		Register all committee members for event, creating a new Registration instance if one does not exist yet
		"""
		with mailer:
			for member in self.members.all():
				registration, created = Registration.objects.get_or_create(event=event, participant=member)
				registration.withdrawn_at = None
				registration.save()

				# Send mail to member
				mailer.send(RegistrationNotificationMail(event, member, request))

	@classonlymethod
	def update_committees(cls, committees):
		"""
		Update all committees in a list of dicts representing those committees.
		"""
		for c_dict in committees:
			# Create committee if it doesn't exist
			c_object, created = cls.objects.get_or_create(name=c_dict['cn'])

			# Update members
			c_object.members.set(
				[get_user_model().objects.get(username=m) for m in c_dict['members'] if get_user_model().objects.filter(username=m).exists()])

			# Update chairman and email address
			c_object.chairman = get_user_model().objects.filter(username=c_dict['chairman']).first()
			c_object.email = c_dict['email']
			c_object.save()
