from django import forms
from django.utils.translation import ugettext_lazy as _


class MassMailForm(forms.Form):
	recipients = forms.ChoiceField(choices=[
		('active', _("Deelnemers")),
		('all', _("Deelnemers en reservelijst"))
	], label=_("Ontvangers"))
	subject = forms.CharField(max_length=100, label=_("Onderwerp"))
	body = forms.CharField(widget=forms.Textarea(attrs={'id': 'summernote'}), initial=_("<p>Beste {{ name }},</p>"))
