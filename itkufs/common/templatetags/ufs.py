from django.template import Library, Variable, TemplateSyntaxError, Node, \
            VariableDoesNotExist
from django.template.defaultfilters import stringfilter
from django.db.models import Q

from itkufs.common.utils import callsign_sorted as ufs_sorted
from itkufs.accounting.models import Account

register = Library()

@register.tag
def ufs_sort(parser, token):
    try:
        tag_name, variable = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
    if (variable[0] == variable[-1] and variable[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's argument should not be in quotes" % tag_name
    return SortedNode(variable)

class SortedNode(Node):
    def __init__(self, variable):
        self.variable = variable

    def render(self, context):
        objects = Variable(self.variable).resolve(context)
        objects = ufs_sorted(list(objects))

        context[self.variable] = objects

        return ''

@register.filter
def creditformat(value):
    if value is None:
        return '-'
    elif value == 0:
        return ''
    else:
        return '%.2f' % value

# FIXME this code should really be removed, however transaction list needs
# to be rewritten to list entries and handle pagination before this can
# happen.
@register.tag(name="filter_entries")
def do_hide(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, transaction, entry_list = token.split_contents()
    except ValueError:
        raise TemplateSyntaxError, "%r tag requires exactly two arguments" \
                    % token.contents.split()[0]

    if transaction[0] == transaction[-1] and transaction[0] in ('"', "'"):
        raise TemplateSyntaxError, "%r tag only takes variables" % tag_name
    if entry_list[0] == entry_list[-1] and entry_list[0] in ('"', "'"):
        raise TemplateSyntaxError, "%r tag only takes variables" % tag_name

    return HideNode(transaction, entry_list)

class HideNode(Node):
    def __init__(self, transaction, entry_list):
        self.transaction = Variable(transaction)
        self.account = Variable('account')
        self.entry_list = entry_list

    def render(self, context):
        transaction = self.transaction.resolve(context)
        entry_list = transaction.entry_set.select_related('account__owner')

        context[self.entry_list] = entry_list
        return ''
