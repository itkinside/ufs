from django.contrib import databrowse

from itkufs.accounting.models import *

databrowse.site.register(Group)
databrowse.site.register(Account)
databrowse.site.register(RoleAccount)
databrowse.site.register(Settlement)
databrowse.site.register(Transaction)
databrowse.site.register(TransactionLog)
databrowse.site.register(TransactionEntry)
