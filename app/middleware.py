from django.utils import timezone


def last_seen_middleware(get_response):
	"""
	Keep track of last seen date.
	"""
	def middleware(request):
		response = get_response(request)

		if request.user.is_authenticated:
			request.user.last_seen_at = timezone.now()
			request.user.save()

		return response

	return middleware


def base_url_middleware(get_response):
	"""
	Add base url to request
	"""
	def middleware(request):
		request.base_url = request.build_absolute_uri('/').strip("/")

		return get_response(request)

	return middleware
