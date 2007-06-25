from django.contrib.auth.models import User

class SettingsBackend:
    def authenticate(self, username=None, password=None):
        if self.META.has_key('REMOTE_USER'):
            username = request.META.get('REMOTE_USER').split('@')[0]

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = User(username=username, password=None)
                user.is_staff = False
                user.is_superuser = False
                user.save()
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
