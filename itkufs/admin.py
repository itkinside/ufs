from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.contrib.flatpages.models import FlatPage

site = AdminSite()

site.register(User)
site.register(FlatPage)
