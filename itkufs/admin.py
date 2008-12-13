from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.admin import FlatPageAdmin

site = AdminSite()

class CustomUserAdmin(UserAdmin):
    # Remove group editing
    fieldsets = UserAdmin.fieldsets[:-1]

class CustomFlatPageAdmin(FlatPageAdmin):
    list_filter = []

site.register(User, CustomUserAdmin)
site.register(FlatPage, CustomFlatPageAdmin)
