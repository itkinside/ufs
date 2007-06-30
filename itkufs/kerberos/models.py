from django.contrib.auth.models import User
from django.conf import settings

class SettingsBackend:
    def authenticate(self, username=None, password=None):
        if self.META.has_key('REMOTE_USER'):
            username = request.META.get('REMOTE_USER').split('@')[0]

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                email = '%s@%s' % (username, settings.MAIL_DOMAIN)
                user = User(username=username, password=None, email=email)
                user.save()
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
