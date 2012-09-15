#from functools import update_wrapper
#from django import template
#from django.conf import settings
#from django.conf.urls.defaults import url, patterns
#import tempfile
#from django.contrib import messages
#from django.core.exceptions import ObjectDoesNotExist, ValidationError
#from django.core.files.uploadedfile import TemporaryUploadedFile
#from django.core.urlresolvers import reverse
#from django.db.models.fields.related import ForeignKey
#from django.db.models.loading import get_model
#from django.db.utils import IntegrityError
#from django.http import HttpResponseRedirect
#from django.shortcuts import render_to_response, redirect
#import os
#from iadmin.plugins import IAdminPlugin
#from iadmin.plugins.csv.utils import update_model, open_csv
#from .utils import  ImportForm, csv_processor_factory
#
#
#class CSVImporter(IAdminPlugin):
#    template_step1 = None
#    template_step2 = None
#    template_step3 = None
#
#    def _get_base_context(self, request, app=None, model=None):
#        return template.RequestContext(request, {'app_label': (app or '').lower(),
#                                                 'model_name': (model or '').lower(),
#                                                 'root_path': self.admin_site.root_path or '',
#                                                 'lbl_next': 'Next >>',
#                                                 'lbl_back': '<< Back',
#                                                 'back': request.META['HTTP_REFERER'],
#                                                 },
#                                       current_app=self.name)
#
#    def __get_mapping(self, form):
#        mapping = {}
#        for i, f in enumerate(form._fields):
#            field_name = form.cleaned_data['fld_%s' % i]
#            column = form.cleaned_data['col_%s' % i]
#            rex = form.cleaned_data['rex_%s' % i]
#            lk = form.cleaned_data['lkf_%s' % i]
#            key = form.cleaned_data['key_%s' % i]
#
#            if column >= 0:
#                Field, _, _, _ = form._model._meta.get_field_by_name(field_name)
#                mapping[field_name] = [column, rex, bool(key), lk, Field]
#        return mapping
#
#    def _step_1(self, request, app=None, model=None, temp_file_name=None):
#        context = self._get_base_context(request, app, model)
#        if request.method == 'POST':
#            form = ImportForm(app, model, request.POST, request.FILES)
#            if form.is_valid():
#                f = request.FILES['csv']
#                fd = open(temp_file_name, 'wb')
#                for chunk in f.chunks():
#                    fd.write(chunk)
#                fd.close()
#                if settings.DEBUG:
#                    messages.info(request, temp_file_name)
#                app_name, model_name = form.cleaned_data['model'].split(':')
#                goto_url = reverse('%s:model_import_csv' % self.name,
#                                   kwargs={'app': app_name, 'model': model_name, 'page': 2})
#                return HttpResponseRedirect(goto_url)
#        else:
#            form = ImportForm(app, model, initial={'page': 1})
#
#        context.update({'page': 1, 'form': form, })
#
#        return render_to_response(self.template_step1 or [
#            "iadmin/%s/%s/import_csv_1.html" % (app, model),
#            "iadmin/%s/import_csv_1.html" % app,
#            "iadmin/import_csv_1.html"
#        ], context)
#
#
#    def _process_row(self, row, mapping):
#        record = {}
#        key = {}
#        for field_name, (col, rex, is_key, lk, Field) in mapping.items():
#            try:
#                raw_val = rex.search(row[col]).group(1)
#                field_value = None
#                if isinstance(Field, ForeignKey):
#                    try:
#                        field_value = Field.rel.to.objects.get(**{lk: raw_val})
#                    except Field.rel.to.DoesNotExist:
#                        pass
#                else:
#                    field_value = Field.to_python(raw_val)
#                record[field_name] = field_value
#                if is_key:
#                    key[field_name] = record[field_name]
#            except AttributeError, e:
#                raise AttributeError('Error processing "%s": Invalid regex' % field_name)
#            except Exception, e:
#                raise e.__class__('Error processing "%s"' % field_name, e)
#        return record, key
#
#    def _step_2(self, request, app_name=None, model_name=None, temp_file_name=None):
#        records = []
#        context = self._get_base_context(request, app_name, model_name)
#        try:
#            Form = csv_processor_factory(app_name, model_name, temp_file_name)
#            if request.method == 'POST':
#                form = Form(request.POST, request.FILES)
#                if form.is_valid():
#                    mapping = self.__get_mapping(form)
#                    Model = get_model(app_name, model_name)
#                    with open_csv(temp_file_name) as csv:
#                        if form.cleaned_data['header']:
#                            csv.next()
#                        for i, row in enumerate(csv):
#                            if i > 20 and not form.cleaned_data['preview_all']:
#                                break
#                            try:
#                                sample = Model()
#                                record, key = self._process_row(row, mapping)
#                                exists = key and Model.objects.filter(**key).exists() or False
#                                if key and exists:
#                                    sample = Model.objects.get(**key)
#                                else:
#                                    sample = Model()
#                                sample = update_model(request, sample, record, mapping)
#                                records.append([sample, None, row])
#                            except (ValidationError, AttributeError), e:
#                                records.append([sample, str(e), row])
#                            except (ValueError, ObjectDoesNotExist, ValidationError), e:
#                                #messages.error(request, '%s' % e)
#                                records.append([sample, str(e)])
#                        return self._step_3(request, app_name, model_name, temp_file_name, {'records': records,
#                                                                                            'form': form})
#
#            else:
#                form = Form()
#
#            context.update({'page': 2,
#                            'form': form,
#                            'back': reverse('%s:model_import_csv' % self.name,
#                                            kwargs={'app': app_name, 'model': model_name, 'page': 1}),
#                            'fields': form._fields,
#                            'sample': form._head(),
#                            })
#            return render_to_response(self.template_step2 or [
#                                                    "iadmin/%s/%s/import_csv_2.html" % (app_name, model_name.lower()),
#                                                    "iadmin/%s/import_csv_2.html" % app_name,
#                                                    "iadmin/import_csv_2.html"
#                                                ], context)
#
#        except IOError, e:
#            messages.error(request, str(e))
#            return redirect('%s:model_import_csv' % self.name, app=app_name, model=model_name, page=1)
#
#    def _step_3(self, request, app_name=None, model_name=None, temp_file_name=None, extra_context=None ):
#        context = self._get_base_context(request, app_name, model_name)
#        Model = get_model(app_name, model_name)
#        extra_context = extra_context or {}
#        if 'apply' in request.POST:
#            Form = csv_processor_factory(app_name, model_name, temp_file_name)
#            form = Form(request.POST, request.FILES)
#            if form.is_valid():
#                mapping = self.__get_mapping(form)
#                Model = get_model(app_name, model_name)
#                with open_csv(temp_file_name) as csv:
#                    if form.cleaned_data['header']:
#                        csv.next()
#                    for i, row in enumerate(csv):
#                        record, key = self._process_row(row, mapping)
#                        try:
#                            if key:
#                                if form.cleaned_data['create_missing']:
#                                    sample, _ = Model.objects.get_or_create(**key)
#                                else:
#                                    sample = Model.objects.get(**key)
#                            else:
#                                sample = Model()
#                            sample = update_model(request, sample, record, mapping)
#                            sample.save()
#                        except (IntegrityError, ObjectDoesNotExist), e:
#                            messages.error(request, '%s: %s' % (str(e), row) )
#                return redirect('%s:%s_%s_changelist' % (self.name, app_name, model_name.lower()))
#        else:
#            pass
#        context.update({'page': 3,
#                        'fields': Model._meta.fields,
#                        'back': reverse('%s:model_import_csv' % self.name,
#                                        kwargs={'app': app_name, 'model': model_name, 'page': 2}),
#                        'lbl_next': 'Apply',
#                        })
#        context.update(extra_context)
#        return render_to_response(self.template_step3 or [
#                                                "iadmin/%s/%s/import_csv_3.html" % (app_name, model_name.lower()),
#                                                "iadmin/%s/import_csv_3.html" % app_name,
#                                                "iadmin/import_csv_3.html"
#                                            ], context)
#
#
#    def import_csv(self, request, page=1, app=None, model=None):
#        temp_file_name = os.path.join(tempfile.gettempdir(), 'iadmin_import_%s_%s.temp~' % (
#            request.user.username, hash(request.user.password)))
#        if int(page) == 1:
#            return self._step_1(request, app, model, temp_file_name=temp_file_name)
#        elif int(page) == 2:
#            if not 'HTTP_REFERER' in request.META:
#                return redirect('%s:model_import_csv' % self.name, app=app, model=model, page=1)
#                # todo: check referer
#            return self._step_2(request, app, model, temp_file_name=temp_file_name)
#        elif int(page) == 3:
#            return self._step_3(request, app, model, temp_file_name=temp_file_name)
#        raise Exception(page)
#
#    def get_urls(self):
#        def wrap(view, cacheable=False):
#            def wrapper(*args, **kwargs):
#                return self.admin_site.admin_view(view, cacheable)(*args, **kwargs)
#
#            return update_wrapper(wrapper, view)
#
#        return patterns('',
#                        url(r'^import/1$',
#                            wrap(self.import_csv),
#                            name='import_csv'),
#
#                        url(r'^(?P<app>\w+)/(?P<model>\w+)/import/(?P<page>\d)',
#                            wrap(self.import_csv),
#                            name='model_import_csv'),
#
#                        url(r'^(?P<app>\w+)/import/(?P<page>\d)',
#                            wrap(self.import_csv),
#                            name='app_import_csv'),
#                        )
