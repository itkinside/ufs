from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from itkufs.accounting.models import Group, Account, RoleAccount, \
        Settlement, Transaction, TransactionLog, TransactionEntry

class GroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('admins',)
    prepopulated_fields = {
        'slug': ('name',),
    }

class AccountAdmin(admin.ModelAdmin):
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

class RoleAccountAdmin(admin.ModelAdmin):
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

class TransactionAdmin(admin.ModelAdmin):
    inlines = [
        TransactionLogInline,
        TransactionEntryInline,
    ]

admin.site.register(Group, GroupAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(RoleAccount, RoleAccountAdmin)
admin.site.register(Settlement)
admin.site.register(Transaction, TransactionAdmin)
