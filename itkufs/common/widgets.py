from django import forms
from django.forms.util import flatatt
from django.utils.encoding import smart_text
from django.utils.html import escape
from django.utils.translation import ugettext as _


class GroupedSelect(forms.Select):
    """From http://www.djangosnippets.org/snippets/200/"""

    def render(self, name, value, attrs=None, choices=()):

        if value is None:
            value = ""
        final_attrs = self.build_attrs(attrs, name=name)
        output = ["<select%s>" % flatatt(final_attrs)]
        str_value = smart_text(value)

        for group_label, group in self.choices:
            if group_label:  # should belong to an optgroup
                group_label = smart_text(group_label)
                output.append('<optgroup label="%s">' % escape(group_label))
            for k, v in group:
                option_value = smart_text(k)
                option_label = smart_text(v)
                if option_value == str_value:
                    selected_html = ' selected="selected"'
                else:
                    selected_html = ""
                output.append(
                    '<option value="%s"%s>%s</option>'
                    % (
                        escape(option_value),
                        selected_html,
                        escape(option_label),
                    )
                )
            if group_label:
                output.append("</optgroup>")

        output.append("</select>")
        return "\n".join(output)


class GroupedChoiceField(forms.ChoiceField):
    """field for grouped choices, handles cleaning of funky choice tuple"""

    def __init__(
        self,
        choices=(),
        required=True,
        widget=GroupedSelect,
        label=None,
        initial=None,
        help_text=None,
    ):
        super(forms.ChoiceField, self).__init__(
            required, widget, label, initial, help_text
        )
        self.choices = choices

    def clean(self, value):
        """
        Validates that the input is in self.choices.
        """
        value = super(forms.ChoiceField, self).clean(value)
        if value in (None, ""):
            value = ""
        value = smart_text(value)
        if value == "":
            return value
        valid_values = []
        for group_label, group in self.choices:
            valid_values += [str(k) for k, v in group]
        if value not in valid_values:
            raise forms.ValidationError(
                _(
                    "Select a valid choice. That choice is not one of the "
                    "available choices."
                )
            )
        return value
