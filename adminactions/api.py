# -*- encoding: utf-8 -*-
import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models.fields.related import ManyToManyField, OneToOneField
from django.http import HttpResponse
from adminactions.templatetags.actions import get_field_value
try:
    import unicodecsv as csv
except ImportError:
    import csv
from django.utils.encoding import smart_str
from django.utils import dateformat
from adminactions.utils import clone_instance, get_field_by_path, get_copy_of_instance  # NOQA

csv_options_default = {'date_format': 'd/m/Y',
                       'datetime_format': 'N j, Y, P',
                       'time_format': 'P',
                       'quotechar': '"',
                       'quoting': csv.QUOTE_ALL,
                       'delimiter': ';',
                       'escapechar': '\\', }

delimiters = ",;|:"
quotes = "'\"`"
escapechars = " \\"
ALL_FIELDS = -999


def merge(master, other, fields=None, commit=False, m2m=None, related=None):
    """
        Merge 'other' into master.

        `fields` is a list of fieldnames that must be readed from ``other`` to put into master.
        If ``fields`` is None ``master`` will get all the ``other`` values except primary_key.
        Finally ``other`` will be deleted and master will be preserved

    @param master:  Model instance
    @param other: Model instance
    @param fields: list of fieldnames to  merge
    @return:
    """
    fields = fields or [f.name for f in master._meta.fields]
    all_m2m = {}
    all_related = {}

    if related == ALL_FIELDS:
        related = [rel.get_accessor_name()
                   for rel in master._meta.get_all_related_objects(False, False, False)]

    if m2m == ALL_FIELDS:
        m2m = [field.name for field in master._meta.many_to_many]

    if m2m and not commit:
        raise ValueError('Cannot save related with `commit=False`')
    with transaction.commit_manually():
        try:
            result = clone_instance(master)

            for fieldname in fields:
                f = get_field_by_path(master, fieldname)
                if not f.primary_key:
                    setattr(result, fieldname, getattr(other, fieldname))

            if m2m:
                for fieldname in set(m2m):
                    all_m2m[fieldname] = []
                    field_object = get_field_by_path(master, fieldname)
                    if not isinstance(field_object, ManyToManyField):
                        raise ValueError('{0} is not a ManyToManyField field'.format(fieldname))
                    source_m2m = getattr(other, field_object.name)
                    for r in source_m2m.all():
                        all_m2m[fieldname].append(r)
            if related:
                for name in set(related):
                    related_object = get_field_by_path(master, name)
                    all_related[name] = []
                    if related_object and isinstance(related_object.field, OneToOneField):
                        try:
                            accessor = getattr(other, name)
                            all_related[name] = [(related_object.field.name, accessor)]
                        except ObjectDoesNotExist:
                            #nothing to merge
                            pass
                    else:
                        accessor = getattr(other, name)
                        rel_fieldname = accessor.core_filters.keys()[0].split('__')[0]
                        for r in accessor.all():
                            all_related[name].append((rel_fieldname, r))

            if commit:
                for name, elements in all_related.items():
                    # dest = getattr(result, name)
                    for rel_fieldname, element in elements:
                        setattr(element, rel_fieldname, master)
                        element.save()

                other.delete()
                result.save()
                for fieldname, elements in all_m2m.items():
                    dest_m2m = getattr(result, fieldname)
                    for element in elements:
                        dest_m2m.add(element)

        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()
    return result


def export_as_csv(queryset, fields=None, header=False, filename=None, options=None):
    """
        Exports a queryset as csv from a queryset with the given fields.

    :param queryset: queryset to export
    :param fields: list of fields names to export. None for all fields
    :param header: if True, the exported file will have the first row as column names
    :param filename: name of the filename
    :param options: CSVOptions() instance or none
    :return: HttpResponse instance
    """
    filename = filename or "%s.csv" % queryset.model._meta.verbose_name_plural.lower().replace(" ", "_")
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment;filename="%s"' % filename.encode('us-ascii', 'replace')
    if options is None:
        options = csv_options_default

    writer = csv.writer(response,
                        escapechar=str(options['escapechar']),
                        delimiter=str(options['delimiter']),
                        quotechar=str(options['quotechar']),
                        quoting=int(options['quoting']))
    if header:
        writer.writerow([f for f in fields])
    for obj in queryset:
        row = []
        for fieldname in fields:
            value = get_field_value(obj, fieldname)
            if isinstance(value, datetime.datetime):
                value = dateformat.format(value, options['datetime_format'])
            elif isinstance(value, datetime.date):
                value = dateformat.format(value, options['date_format'])
            elif isinstance(value, datetime.time):
                value = dateformat.format(value, options['time_format'])
            row.append(smart_str(value))
        writer.writerow(row)
    return response
