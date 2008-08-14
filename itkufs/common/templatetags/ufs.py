from decimal import Decimal, DecimalException

from django.template import Library, Variable, TemplateSyntaxError, Node, VariableDoesNotExist
from django.db.models import Q

register = Library()

@register.tag(name="filter_entries")
def do_hide(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, transaction, entry_list = token.split_contents()
    except ValueError:
        raise TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]

    if transaction[0] == transaction[-1] and transaction[0] in ('"', "'"):
        raise TemplateSyntaxError, "%r tag only takes variables" % tag_name
    if entry_list[0] == entry_list[-1] and entry_list[0] in ('"', "'"):
        raise TemplateSyntaxError, "%r tag only takes variables" % tag_name

    return HideNode(transaction, entry_list)

class HideNode(Node):
    def __init__(self, transaction, entry_list):
        self.transaction = Variable(transaction)
        self.is_admin = Variable('is_admin')
        self.account = Variable('account')
        self.entry_list = entry_list

    def render(self, context):
        transaction = self.transaction.resolve(context)
        is_admin = self.is_admin.resolve(context)
        entry_list = transaction.entry_set.select_related()

        if is_admin:
            # Return quickly if we can
            context[self.entry_list] = entry_list
            return ''

        try:
            account = self.account.resolve(context)
        except VariableDoesNotExist:
            account = None

        # This is not inside the except on purpose, please don't change.
        if not account:
            # Figure out which account we are allowed to show
            account = Variable('user').resolve(context).account_set.get(group=Variable('group').resolve(context))
            context['account'] = account
            show_all = True
        else:
            show_all = False

        if transaction.entry_count_sql == 2:
            for e in entry_list:
                if e.account == account:
                    context[self.entry_list] = entry_list
                    return ''
            context[self.entry_list] = entry_list.none()
            return ''

        # Add extra sub-query that asks if user is on credit side of
        # transaction.
        entry_list = entry_list.extra(
            select={
                'user_credit': """SELECT credit > debit FROM accounting_transactionentry
                                  WHERE transaction_id = %d AND account_id = %d"""
                % (transaction.id, account.id),
            },
        )

        # FIXME? if your account is the only credit/debit account in
        # transaction show all debit/credit ammounts so that you know where
        # your money went to.

        # Loop through entries not adding those that are on the samme side
        # as the current user. Blank out values of the entry on the other
        # side
        tmp = []
        for e in entry_list:
            if e.account == account:
                tmp.append(e)
            elif (show_all or e.user_credit) and e.debit:
                e.debit = '-'
                tmp.append(e)
            elif (show_all or not e.user_credit) and e.credit:
                e.credit = '-'
                tmp.append(e)

        entry_list = tmp

        # Set what ever value self.entry_list is to our computed value
        context[self.entry_list] = entry_list
        return ''
