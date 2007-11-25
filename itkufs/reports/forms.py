from django.newforms import BaseForm
from django.newforms.forms import BoundField
#from django.utils.safestring import mark_safe

class ColumnBaseForm(BaseForm):
    """Returns this form rendered as HTML <tr>s -- excluding the <table></table>."""
    def as_table_row(self):
        output = []
        for name, field in self.fields.items():
            bf = BoundField(self, field, name)

            if bf.errors:
                error = u'class="error"'
            else:
                error = u''

            output.append("<td%s>%s</td>" %(error, bf))

        return u'\n'.join(output)
