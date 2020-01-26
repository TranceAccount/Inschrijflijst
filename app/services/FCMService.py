import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging


class FCMService:
	"""
	Service for communicating with Firebase Cloud Messaging
	"""
	FCM_CLIENT_SECRET_FILE = 'storage/FCM_client_id.json'
	DEFAULT_TOPIC = 'all'

	def __init__(self, base_url):
		"""
        Get credentials
        """
		self.base_url = base_url
		try:
			cred = credentials.Certificate(self.FCM_CLIENT_SECRET_FILE)
			self.app = firebase_admin.initialize_app(cred)
		except FileNotFoundError:
			raise RuntimeError('Client secrets invalid')

	def notify(self, app_event):
		"""
		Send notification to app users
		"""
		message = messaging.Message(
			data={
				'title': app_event.name,
				'body': app_event.description,
				'eventURL': self.base_url + app_event.get_absolute_url(),
			},
			topic=self.DEFAULT_TOPIC
		)

		messaging.send(message)
