from django.conf import settings
from django.contrib.auth.models import User

class KerberosBackend:
    def authenticate(self, request=None):
        if request and 'REMOTE_USER' in request.META:
            username = request.META['REMOTE_USER'].split('@')[0]
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                email = '%s@%s' % (username, settings.MAIL_DOMAIN)
                user = User(username=username, password='In Kerberos')
                user.email = email
                user.save()
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
