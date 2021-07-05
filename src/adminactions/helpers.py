from django import forms
from django.contrib import messages
from django.core import serializers
from django.core.exceptions import ValidationError
from django.template.response import TemplateResponse


class ImportFixtureForm(forms.Form):
    fixture_file = forms.FileField(required=False)
    fixture_content = forms.CharField(widget=forms.Textarea, required=False)

    use_natural_foreign_keys = forms.BooleanField(required=False)
    use_natural_primary_keys = forms.BooleanField(required=False)

    def clean(self):
        if not (self.cleaned_data['fixture_file'] or self.cleaned_data['fixture_content']):
            raise ValidationError('You must provide file or content')


def import_fixture(modeladmin, request):
    context = modeladmin.get_common_context(request)
    if request.method == 'POST':
        form = ImportFixtureForm(data=request.POST)
        if form.is_valid():
            use_natural_fk = form.cleaned_data['use_natural_foreign_keys']
            use_natural_pk = form.cleaned_data['use_natural_primary_keys']
            ser_fmt = 'json'
            try:
                if form.cleaned_data['fixture_content']:
                    fixture_data = form.cleaned_data['fixture_content']
                else:
                    fixture_data = request.FILES['fixture_file'].read()

                ser_fmt = 'json'
                objects = serializers.deserialize(ser_fmt, fixture_data,
                                                  use_natural_foreign_keys=use_natural_fk,
                                                  use_natural_primary_keys=use_natural_pk)
                imported = 0
                for obj in objects:
                    obj.save()
                    imported += 1

                modeladmin.message_user(request, imported, messages.SUCCESS)
            except Exception as e:
                modeladmin.message_user(request, f'{e.__class__.__name__}: {e}', messages.ERROR)

    else:
        form = ImportFixtureForm()
    context['form'] = form
    context['action'] = 'Import fixture'
    return TemplateResponse(request, "adminactions/helpers/import_fixture.html", context)



