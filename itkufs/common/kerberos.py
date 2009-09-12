from pwd import getpwnam

from django.conf import settings
from django.contrib.auth.models import User

class KerberosBackend:
    def authenticate(self, request=None):
        if request and 'REMOTE_USER' in request.META:
            username = request.META['REMOTE_USER'].split('@')[0]
            return self.get_or_create_user(username)
        else:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def get_or_create_user(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                getpwnam(username)
            except KeyError:
                return None
            user = User(username=username, password='In Kerberos')
            user.email = '%s@%s' % (username, settings.MAIL_DOMAIN)
            user.save()
        return user
