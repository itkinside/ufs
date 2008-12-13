from django.contrib import admin
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from itkufs.admin import site
from itkufs.accounting.models import Group, Account, RoleAccount, \
        Settlement, Transaction, TransactionLog, TransactionEntry

class BaseModelAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False

class GroupAdmin(BaseModelAdmin):
    filter_horizontal = ('admins',)
    prepopulated_fields = {
        'slug': ('name',),
    }

class BasicGroupAdmin(GroupAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'admins'),
        }),
    )

class AccountAdmin(BaseModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'group', 'owner'),
        }),
        (_('Advanced options'), {
            'classes': ('collapse',),
            'fields' : ('type', 'active', 'ignore_block_limit'),
        }),
    )
    list_display = ('group', 'name', 'type', 'owner', 'balance',
        'active', 'ignore_block_limit')
    list_display_links = ('name',)
    list_filter = ('active', 'type', 'group')
    list_per_page = 20
    prepopulated_fields = {
        'slug': ('name',),
    }
    search_fields = ('name',)

    def has_delete_permission(self, request, obj=None):
        return False

class RoleAccountAdmin(BaseModelAdmin):
    list_display = ('group', 'role', 'account')
    list_display_links = ('group', 'role', 'account')
    list_filter = ('group', 'role')
    list_per_page = 20
    search_fields = ('account',)

class TransactionLogInline(admin.TabularInline):
    model = TransactionLog
    extra = 1
    max_num = 4

class TransactionEntryInline(admin.TabularInline):
    model = TransactionEntry
    extra = 3

class TransactionAdmin(BaseModelAdmin):
    inlines = [
        TransactionLogInline,
        TransactionEntryInline,
    ]

if getattr(settings, 'BACKOFFICE', False):
    site.register(Group, GroupAdmin)
    site.register(Account, AccountAdmin)
    site.register(RoleAccount, RoleAccountAdmin)
    site.register(Settlement)
    site.register(Transaction, TransactionAdmin)
else:
    site.register(Group, BasicGroupAdmin)
