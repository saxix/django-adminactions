import csv
from django import forms
from django.core.serializers import get_serializer_formats
from django.forms.models import ModelForm
from django.forms.widgets import SelectMultiple
from django.utils import formats
from django.utils.translation import gettext_lazy as _

from .api import delimiters, quotes
from .utils import get_ignored_fields


class GenericActionForm(ModelForm):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    select_across = forms.BooleanField(label='', required=False, initial=0,
                                       widget=forms.HiddenInput({'class': 'select-across'}))
    action = forms.CharField(label='', required=True, initial='', widget=forms.HiddenInput())

    def configured_fields(self):
        return [field for field in self if not field.is_hidden and field.name.startswith('_')]

    def model_fields(self):
        """
        Returns a list of BoundField objects that aren't "private" fields or are not ignored.
        """
        ignored_fields = ('select_accross', 'action', *get_ignored_fields(self._meta.model, "UPDATE_ACTION_IGNORED_FIELDS"))
        return [field for field in self if not field.name.startswith('_') and field.name not in ignored_fields]


class CSVOptions(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    select_across = forms.BooleanField(label='', required=False, initial=0,
                                       widget=forms.HiddenInput({'class': 'select-across'}))
    action = forms.CharField(label='', required=True, initial='', widget=forms.HiddenInput())

    header = forms.BooleanField(label=_('Header'), required=False)
    delimiter = forms.ChoiceField(label=_('Delimiter'), choices=list(zip(delimiters, delimiters)), initial=',')
    quotechar = forms.ChoiceField(label=_('Quotechar'), choices=list(zip(quotes, quotes)), initial="'")
    quoting = forms.ChoiceField(
        label=_('Quoting'),
        choices=((csv.QUOTE_ALL, _('All')),
                 (csv.QUOTE_MINIMAL, _('Minimal')),
                 (csv.QUOTE_NONE, _('None')),
                 (csv.QUOTE_NONNUMERIC, _('Non Numeric'))), initial=csv.QUOTE_ALL)

    escapechar = forms.ChoiceField(label=_('Escapechar'), choices=(('', ''), ('\\', '\\')), required=False)
    datetime_format = forms.CharField(label=_('Datetime format'), initial=formats.get_format('DATETIME_FORMAT'))
    date_format = forms.CharField(label=_('Date format'), initial=formats.get_format('DATE_FORMAT'))
    time_format = forms.CharField(label=_('Time format'), initial=formats.get_format('TIME_FORMAT'))
    columns = forms.MultipleChoiceField(label=_('Columns'), widget=SelectMultiple(attrs={'size': 20}))


class XLSOptions(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    select_across = forms.BooleanField(label='', required=False, initial=0,
                                       widget=forms.HiddenInput({'class': 'select-across'}))
    action = forms.CharField(label='', required=True, initial='', widget=forms.HiddenInput())

    header = forms.BooleanField(label=_('Header'), required=False)
    use_display = forms.BooleanField(label=_('Use display'), required=False)
    columns = forms.MultipleChoiceField(label=_('Columns'), widget=SelectMultiple(attrs={'size': 20}))


class FixtureOptions(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    select_across = forms.BooleanField(label='', required=False, initial=0,
                                       widget=forms.HiddenInput({'class': 'select-across'}))
    action = forms.CharField(label='', required=True, initial='', widget=forms.HiddenInput())

    use_natural_pk = forms.BooleanField(label=_('Use Natural Primary Keys'), required=False)
    use_natural_fk = forms.BooleanField(label=_('Use Natural Foreign Keys'), required=False)
    on_screen = forms.BooleanField(label='Dump on screen', required=False)
    add_foreign_keys = forms.BooleanField(required=False)

    indent = forms.IntegerField(required=True, max_value=10, min_value=0)
    serializer = forms.ChoiceField(choices=list(zip(get_serializer_formats(), get_serializer_formats())))

