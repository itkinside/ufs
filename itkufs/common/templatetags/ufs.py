from django.template import Library, Variable, TemplateSyntaxError, Node
from decimal import Decimal, DecimalException

register = Library()

@register.tag(name="hide")
def do_hide(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, entry, value = token.split_contents()
    except ValueError:
        raise TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]
    if value[0] == value[-1] and value[0] in ('"', "'"):
        raise TemplateSyntaxError, "%r tag only takes variables" % tag_name

    return HideNode(entry, value)

class HideNode(Node):
    def __init__(self, entry, value):
        self.value = Variable(value)
        self.entry = Variable(entry)

    def render(self, context):
        entry = self.entry.resolve(context)
        value = Decimal(self.value.resolve(context))

        if value == 0:
            return u''

        if context.get('is_admin',False) or context.get('user_account',None) == entry.account:
            return u'%0.2f' % value
        else:
            return u'-'

