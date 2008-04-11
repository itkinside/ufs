from django.template import Library, Variable, TemplateSyntaxError, Node
from decimal import Decimal, DecimalException

register = Library()

@register.tag(name="hide")
def do_hide(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, account, value = token.split_contents()
    except ValueError:
        raise TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]
    if value[0] == value[-1] and value[0] in ('"', "'"):
        raise TemplateSyntaxError, "%r tag only takes variables" % tag_name

    return HideNode(account, value)

class HideNode(Node):
    def __init__(self, account, value):
        self.value = Variable(value)
        self.account = Variable(account)

    def render(self, context):
        # FIXME this needs to be documentet and explainded alot better
        account = self.account.resolve(context)
        value = self.value.resolve(context)

        try:
            value = Decimal(value)
            decimal = True
        except DecimalException:
            decimal = False

        if context.get('is_admin', False):
            show = True
        elif context.get('user_account', None) == account:
            show = True
        elif not decimal and not context['group'].admin_only:
            show = True
        elif not decimal and not account.is_user_account():
            show = True
        else:
            show = False

        if decimal:
            if value == 0:
                return ''
            elif show:
                return "%0.2f" % value
        elif show:
            return value

        return '-'

