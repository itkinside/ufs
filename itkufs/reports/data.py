from django.contrib import databrowse

from itkufs.reports.models import *

databrowse.site.register(List)
databrowse.site.register(ListColumn)

