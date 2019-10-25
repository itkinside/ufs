from django import forms
from django.utils.translation import ugettext as _


class GroupedSelect(forms.Select):
    """From http://www.djangosnippets.org/snippets/200/"""

    def render(self, name, value, attrs=None, choices=()):
        from django.utils.html import escape
        from django.forms.util import flatatt, smart_unicode

        if value is None:
            value = ""
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u"<select%s>" % flatatt(final_attrs)]
        str_value = smart_unicode(value)

        for group_label, group in self.choices:
            if group_label:  # should belong to an optgroup
                group_label = smart_unicode(group_label)
                output.append(u'<optgroup label="%s">' % escape(group_label))
            for k, v in group:
                option_value = smart_unicode(k)
                option_label = smart_unicode(v)
                if option_value == str_value:
                    selected_html = u' selected="selected"'
                else:
                    selected_html = ""
                output.append(
                    u'<option value="%s"%s>%s</option>'
                    % (
                        escape(option_value),
                        selected_html,
                        escape(option_label),
                    )
                )
            if group_label:
                output.append(u"</optgroup>")

        output.append(u"</select>")
        return u"\n".join(output)


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
            value = u""
        value = forms.util.smart_unicode(value)
        if value == u"":
            return value
        valid_values = []
        for group_label, group in self.choices:
            valid_values += [str(k) for k, v in group]
        if value not in valid_values:
            raise forms.ValidationError(
                _(
                    u"Select a valid choice. That choice is not one of the "
                    u"available choices."
                )
            )
        return value
