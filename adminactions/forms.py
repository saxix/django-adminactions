from django import forms
from django.forms.models import ModelForm


class GenericActionForm(ModelForm):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)

    def configured_fields(self):

        return [field for field in self if not field.is_hidden and field.name.startswith('_')]

    def model_fields(self):
        """
        Returns a list of BoundField objects that aren't "private" fields.
        """
        return [field for field in self if not (field.name.startswith('_') or field.name in ['select_across', 'action'])]
