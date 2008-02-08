from django.newforms.models import ModelForm
from django.newforms.forms import BoundField, Form
from django.utils.safestring import mark_safe

def as_table_row(self):
    """Returns this form rendered as HTML <td>s -- excluding the
       <table></table> and <tr></tr>."""
    output = []
    for name, field in self.fields.items():
        bf = BoundField(self, field, name)

        if bf.errors:
            error = u' class="error"'
        else:
            error = u''

        output.append("<td%s>%s</td>" %(error, bf))

    return mark_safe(u'\n'.join(output))


class CustomModelForm(ModelForm):
    pass
CustomModelForm.as_table_row = as_table_row

class CustomForm(Form):
    pass
CustomForm.as_table_row = as_table_row
