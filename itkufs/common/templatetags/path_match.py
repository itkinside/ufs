"""
Use this to set an li element to active.
examples:
<li{% path_match '^(<% url news year,month,day %>|<% url news_index %>)$' %}><a href=...
<li{% path_match '^/contact/$' %}< a href...
"""

from django import template
import re

register = template.Library()

MATCH_STRING = ' class="active"'

class PathMatchNode(template.Node):
    def __init__(self, template_string):
        self.template_string = template_string
    def render(self, context):
        regexp = template.Template(template_string=self.template_string).render(context)
        try:
            match = re.match(regexp, context['request'].path)
        except:
            match = False
        if match:
            return MATCH_STRING
        else:
            return ""

@register.tag('path_match')
def do_path_match(parser, token):
    try:
        tag_name, arg = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single regexp as argument" % token.contents.split()[0]
    if not (arg[0] == arg[-1] and arg[0] in ( '"', "'" )):
        raise template.TemplateSyntaxError, "%r tag requires a single regexp as argument" % tag_name
    norm = re.compile(r'\<% ([^%\>]*) %\>')
    template_string = norm.sub(ur'{% \1 %}', arg)[1:-1]
    return PathMatchNode(template_string)

