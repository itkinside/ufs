from pwd import getpwnam

from django.conf import settings
from django.contrib.auth.models import User


class KerberosBackend:
    def authenticate(self, request=None, remote_user=None):
        if not remote_user:
            if "HTTP_REMOTE_USER" in request.META:
                remote_user = request.META["HTTP_REMOTE_USER"]

        if remote_user:
            username = self.clean_username(remote_user)
            return self.get_or_create_user(username)
        else:
            return None

    def clean_username(self, username):
        return username.split("@")[0]

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
            user = User(username=username, password="In Kerberos")
            user.email = "%s@%s" % (username, settings.MAIL_DOMAIN)
            user.save()
        return user
