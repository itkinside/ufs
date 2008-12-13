from django.contrib import admin
from itkufs.reports.models import List, ListColumn

from itkufs.admin import site

class ListColumnInline(admin.TabularInline):
    model = ListColumn
    extra = 3

class ListAdmin(admin.ModelAdmin):
    inlines = [
        ListColumnInline,
    ]
    list_filter = ('group',)
    list_display = ('group', 'name')
    list_display_links = ('name',)
    ordering = ('group', 'name')
    prepopulated_fields = {
        'slug': ('name',),
    }

site.register(List, ListAdmin)
