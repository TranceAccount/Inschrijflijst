import ldap


class LDAPService:
	"""
	Service for communicating with LDAP database. Is a context manager for a LDAP connection.

	The .decode()s used in class methods are needed because the attribute values returned by PyLDAP are in bytes
	(not str) for some archaic reason.
	"""
	# Last part of all DNs
	dc_suffix = 'DC=alembic,DC=utwente,DC=nl'

	def __init__(self, uri, bind_dn, bind_pw):
		"""
		Initialise LDAP connection and bind using provided credentials.
		"""
		self.connection = ldap.initialize(uri, bytes_mode=False)
		self.connection.bind_s(bind_dn, bind_pw)

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.connection.unbind()

	def get_committees(self):
		"""
		Get all committees.
		Returns a list of dicts (CN, members, chairman) where members is a list of usernames.
		"""
		filter = '(objectclass=group)'
		dn = 'OU=Commissies,OU=Groepen,{}'.format(self.dc_suffix)
		attrs = ['cn', 'member', 'salsaCommiteeChairman']

		result = self.connection.search_s(dn, ldap.SCOPE_ONELEVEL, filter, attrs)

		# Build and return list of dicts from LDAP query result
		return [self.build_committee_dict(attrs) for dn, attrs in result]

	def get_in_committees(self, username):
		"""
		Return committees the user is in.
		"""
		filter = '(&(objectclass=group)(member={}))'.format(self.get_dn_from_username(username))
		dn = 'OU=Commissies,OU=Groepen,{}'.format(self.dc_suffix)
		attrs = ['cn', 'member', 'salsaCommiteeChairman']

		result = self.connection.search_s(dn, ldap.SCOPE_ONELEVEL, filter, attrs)

		# Build and return list of dicts from LDAP query result
		return [self.build_committee_dict(attrs) for dn, attrs in result]

	def get_username_from_dn(self, dn):
		"""
		Return username from a distinguished name.
		"""
		# Get sAMAccountName from DN
		filter = '(objectclass=*)'
		attrs = ['sAMAccountName']
		result = self.connection.search_s(dn, ldap.SCOPE_BASE, filter, attrs)

		# Above result is a list of tuples of the form (dn, attrs) where attrs is a dict containing sAMAccountName
		# which is a list of a (byte) string, which we're interested in. Yeah.
		return result[0][1]['sAMAccountName'][0].decode("utf-8")

	def get_dn_from_username(self, username):
		"""
		Return distinguished name from username.
		"""
		filter = '(&(objectclass=person)(sAMAccountName={}))'.format(username)
		dn = 'OU=Gebruikers,{}'.format(self.dc_suffix)
		result = self.connection.search_s(dn, ldap.SCOPE_SUBTREE, filter, [])

		return result[0][0]

	def build_committee_dict(self, attrs):
		"""
		Build a dict containing cn, members and chairman for a commitee from a dict of attributes returned from LDAP.
		"""
		# Lookup username for chairman. Some committees don't have this attribute.
		if 'salsaCommiteeChairman' in attrs:
			chairman = self.get_username_from_dn(attrs['salsaCommiteeChairman'][0].decode('utf-8'))
		else:
			chairman = None

		# For every member, lookup the username. Some committees don't have this attribute.
		if 'member' in attrs:
			members = [self.get_username_from_dn(m.decode('utf-8')) for m in attrs['member']]
		else:
			members = []

		return {
			'cn': attrs['cn'][0].decode("utf-8"),
			'members': members,
			'chairman': chairman
		}