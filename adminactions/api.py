# -*- encoding: utf-8 -*-
import datetime
from django.db import transaction
from django.http import HttpResponse
from adminactions.templatetags.actions import get_field_value
import unicodecsv as csv
from django.utils.encoding import smart_str
from django.utils import dateformat
from adminactions.utils import clone_instance, get_field_by_path

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

def merge(master, other, fields=None, commit=False):
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
    with transaction.commit_manually():
        try:
            target = clone_instance(other)
            result = clone_instance(master)
            for fieldname in fields:
                f = get_field_by_path(master, fieldname)
                if not f.primary_key:
                    setattr(result, fieldname, getattr(target, fieldname))
        except:
            transaction.rollback()
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
