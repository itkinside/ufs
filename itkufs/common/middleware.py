from django.http import Http404
from django.utils.translation import ugettext as _

from itkufs.accounting.models import Group, Account
from itkufs.reports.models import List

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

            if 'list' in view_kwargs:
                # Replace list slug with list object
                try:
                    view_kwargs['list'] = \
                        view_kwargs['group'].list_set.get(
                            slug=view_kwargs['list'])
                except List.DoesNotExist:
                    raise Http404

            # Add group admin flag
            if view_kwargs['group'].admins.filter(id=request.user.id).count():
                view_kwargs['is_admin'] = True
                # Check for pending transactions TODO add quick link
                if view_kwargs['group'].not_received_transaction_set.count():
                    request.user.message_set.create(
                        message=_('You have pending transactions in "%s".') \
                        % view_kwargs['group'].name)
            else:
                view_kwargs['is_admin'] = False
