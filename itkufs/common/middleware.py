from django.http import Http404
from django.utils.translation import ugettext as _

from itkufs.accounting.models import Group, Account, Settlement, Transaction
from itkufs.reports.models import List
from itkufs.billing.models import Bill

class UfsMiddleware:
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Replaces group and account kwargs for the view with objects, and
        adds is_admin flag"""

        if 'group' in view_kwargs:
            # Replace group slug with group object
            try:
                view_kwargs['group'] = Group.objects.get(
                    slug=view_kwargs['group'])
            except Group.DoesNotExist:
                raise Http404

            if 'account' in view_kwargs:
                # Replace account slug with account object
                try:
                    view_kwargs['account'] = \
                        view_kwargs['group'].account_set.get(
                            slug=view_kwargs['account'])
                except Account.DoesNotExist:
                    raise Http404
                # Add account owner flag
                if view_kwargs['account'].owner == request.user:
                    view_kwargs['is_owner'] = True

            if 'settlement' in view_kwargs:
                # Replace settlement ID with settlement object
                try:
                    view_kwargs['settlement'] = \
                        view_kwargs['group'].settlement_set.get(
                            id=view_kwargs['settlement'])
                except Settlement.DoesNotExist:
                    raise Http404

            if 'transaction' in view_kwargs:
                # Replace transaction ID with transaction object
                try:
                    view_kwargs['transaction'] = \
                        view_kwargs['group'].transaction_set_with_rejected.get(
                            id=view_kwargs['transaction'])
                except Transaction.DoesNotExist:
                    raise Http404

            if 'list' in view_kwargs:
                # Replace list slug with list object
                try:
                    view_kwargs['list'] = \
                        view_kwargs['group'].list_set.get(
                            slug=view_kwargs['list'])
                except List.DoesNotExist:
                    raise Http404

            if 'bill' in view_kwargs:
                # Replace list slug with list object
                try:
                    view_kwargs['bill'] = Bill.objects.get(
                        id=view_kwargs['bill'],
                        group=view_kwargs['group'])
                except Bill.DoesNotExist:
                    raise Http404

            # Add group admin flag
            if view_kwargs['group'].admins.filter(id=request.user.id).count():
                view_kwargs['is_admin'] = True
            else:
                view_kwargs['is_admin'] = False
