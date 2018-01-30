# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django import forms
from django.forms.models import ModelForm
from django.forms.widgets import SelectMultiple
from django.utils import formats
from django.utils.translation import ugettext_lazy as _

from .api import csv, delimiters, quotes


class GenericActionForm(ModelForm):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    select_across = forms.BooleanField(label='', required=False, initial=0,
                                       widget=forms.HiddenInput({'class': 'select-across'}))
    action = forms.CharField(label='', required=True, initial='', widget=forms.HiddenInput())

    def configured_fields(self):
        return [field for field in self if not field.is_hidden and field.name.startswith('_')]

    def model_fields(self):
        """
        Returns a list of BoundField objects that aren't "private" fields.
        """
        return [field for field in self if
                not (field.name.startswith('_') or field.name in ['select_across', 'action'])]


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
    # delimiter = forms.ChoiceField(choices=zip(delimiters, delimiters), initial=',')
    # quotechar = forms.ChoiceField(choices=zip(quotes, quotes), initial="'")
    # quoting = forms.ChoiceField(
    #     choices=((csv.QUOTE_ALL, 'All'),
    #              (csv.QUOTE_MINIMAL, 'Minimal'),
    #              (csv.QUOTE_NONE, 'None'),
    #              (csv.QUOTE_NONNUMERIC, 'Non Numeric')), initial=csv.QUOTE_ALL)
    #
    # escapechar = forms.ChoiceField(choices=(('', ''), ('\\', '\\')), required=False)
    # datetime_format = forms.CharField(initial=formats.get_format('DATETIME_FORMAT'))
    # date_format = forms.CharField(initial=formats.get_format('DATE_FORMAT'))
    # time_format = forms.CharField(initial=formats.get_format('TIME_FORMAT'))
    columns = forms.MultipleChoiceField(label=_('Columns'), widget=SelectMultiple(attrs={'size': 20}))
