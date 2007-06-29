from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response

from itkufs.accounting.models import *

def accounting_view(request):
    """Test view"""

    return render_to_response('base.html', {'admin': True})
