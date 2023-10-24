import csv

from django import forms
from django.core.serializers import get_serializer_formats
from django.forms.models import ModelForm
from django.forms.widgets import SelectMultiple
from django.utils import formats
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from .api import delimiters, quotes
from .utils import get_ignored_fields


class GenericActionForm(ModelForm):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    select_across = forms.BooleanField(
        label="",
        required=False,
        initial=0,
        widget=forms.HiddenInput({"class": "select-across"}),
    )
    action = forms.CharField(label="", required=True, initial="", widget=forms.HiddenInput())

    def configured_fields(self):
        return [field for field in self if not field.is_hidden and field.name.startswith("_")]

    @cached_property
    def model_field_names(self):
        ignored_fields = {
            "select_accross",
            "action",
            *get_ignored_fields(self._meta.model, "UPDATE_ACTION_IGNORED_FIELDS"),
        }
        return [f.name for f in self._meta.model._meta.get_fields() if f.name not in ignored_fields]

    def model_fields(self):
        # field_names = [f.name for f in self._meta.model._meta.get_fields() if f.name not in self.model_field_names]
        return [field for field in self if field.name in self.model_field_names]


class CSVConfigForm(forms.Form):
    header = forms.BooleanField(label=_("Header"), required=False)
    delimiter = forms.ChoiceField(
        label=_("Delimiter"), choices=list(zip(delimiters, delimiters)), initial=","
    )
    quotechar = forms.ChoiceField(label=_("Quotechar"), choices=list(zip(quotes, quotes)), initial="'")
    quoting = forms.TypedChoiceField(
        coerce=int,
        label=_("Quoting"),
        choices=(
            (csv.QUOTE_ALL, _("All")),
            (csv.QUOTE_MINIMAL, _("Minimal")),
            (csv.QUOTE_NONE, _("None")),
            (csv.QUOTE_NONNUMERIC, _("Non Numeric")),
        ),
        initial=csv.QUOTE_ALL,
    )

    escapechar = forms.ChoiceField(label=_("Escapechar"), choices=(("", ""), ("\\", "\\")), required=False)

    def clean_escapechar(self):
        return self.cleaned_data["escapechar"] or None

    def csv_fields(self):
        return [
            field
            for field in self
            if field.name
            in [
                "header",
                "delimiter",
                "quotechar",
                "quoting",
                "escapechar",
            ]
        ]


class CSVOptions(CSVConfigForm):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    select_across = forms.BooleanField(
        label="",
        required=False,
        initial=0,
        widget=forms.HiddenInput({"class": "select-across"}),
    )
    action = forms.CharField(label="", required=True, initial="", widget=forms.HiddenInput())

    datetime_format = forms.CharField(
        label=_("Datetime format"), initial=formats.get_format("DATETIME_FORMAT")
    )
    date_format = forms.CharField(label=_("Date format"), initial=formats.get_format("DATE_FORMAT"))
    time_format = forms.CharField(label=_("Time format"), initial=formats.get_format("TIME_FORMAT"))
    columns = forms.MultipleChoiceField(label=_("Columns"), widget=SelectMultiple(attrs={"size": 20}))


class XLSOptions(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    select_across = forms.BooleanField(
        label="",
        required=False,
        initial=0,
        widget=forms.HiddenInput({"class": "select-across"}),
    )
    action = forms.CharField(label="", required=True, initial="", widget=forms.HiddenInput())

    header = forms.BooleanField(label=_("Header"), required=False)
    use_display = forms.BooleanField(label=_("Use display"), required=False)
    columns = forms.MultipleChoiceField(label=_("Columns"), widget=SelectMultiple(attrs={"size": 20}))


class FixtureOptions(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    select_across = forms.BooleanField(
        label="",
        required=False,
        initial=0,
        widget=forms.HiddenInput({"class": "select-across"}),
    )
    action = forms.CharField(label="", required=True, initial="", widget=forms.HiddenInput())

    use_natural_pk = forms.BooleanField(label=_("Use Natural Primary Keys"), required=False)
    use_natural_fk = forms.BooleanField(label=_("Use Natural Foreign Keys"), required=False)
    on_screen = forms.BooleanField(label="Dump on screen", required=False)
    add_foreign_keys = forms.BooleanField(required=False)

    indent = forms.IntegerField(required=True, max_value=10, min_value=0)
    serializer = forms.ChoiceField(choices=list(zip(get_serializer_formats(), get_serializer_formats())))
