# -*- encoding: utf-8 -*-
import datetime
import xlwt
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models.fields import FieldDoesNotExist
from django.db.models.fields.related import ManyToManyField, OneToOneField
from django.http import HttpResponse
from adminactions.templatetags.actions import get_field_value

try:
    import unicodecsv as csv
except ImportError:
    import csv
from django.utils.encoding import smart_str
from django.utils import dateformat
from adminactions.utils import clone_instance, get_field_by_path, get_copy_of_instance, getattr_or_item  # NOQA

csv_options_default = {'date_format': 'd/m/Y',
                       'datetime_format': 'N j, Y, P',
                       'time_format': 'P',
                       'header': False,
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
    @param m2m: list of m2m fields to merge. If empty will be removed
    @param related: list of related fieldnames to merge. If empty will be removed
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


def export_as_csv(queryset, fields=None, header=None, filename=None, options=None, out=None):
    """
        Exports a queryset as csv from a queryset with the given fields.

    :param queryset: queryset to export
    :param fields: list of fields names to export. None for all fields
    :param header: if True, the exported file will have the first row as column names
    :param filename: name of the filename
    :param options: CSVOptions() instance or none
    :param: out: object that implements File protocol. HttpResponse if None.

    :return: HttpResponse instance
    """
    if out is None:
        if filename is None:
            filename = filename or "%s.csv" % queryset.model._meta.verbose_name_plural.lower().replace(" ", "_")
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment;filename="%s"' % filename.encode('us-ascii', 'replace')
    else:
        response = out

    if options is None:
        config = csv_options_default
    else:
        config = csv_options_default.copy()
        config.update(options)

    if fields is None:
        fields = [f.name for f in queryset.model._meta.fields]

    dialect = config.get('dialect', None)
    if dialect is not None:
        writer = csv.writer(response, dialect=dialect)
    else:
        writer = csv.writer(response,
                            escapechar=str(config['escapechar']),
                            delimiter=str(config['delimiter']),
                            quotechar=str(config['quotechar']),
                            quoting=int(config['quoting']))

    if bool(header):
        if isinstance(header, (list, tuple)):
            writer.writerow(header)
        else:
            writer.writerow([f for f in fields])

    for obj in queryset:
        row = []
        for fieldname in fields:
            value = get_field_value(obj, fieldname)
            if isinstance(value, datetime.datetime):
                value = dateformat.format(value, config['datetime_format'])
            elif isinstance(value, datetime.date):
                value = dateformat.format(value, config['date_format'])
            elif isinstance(value, datetime.time):
                value = dateformat.format(value, config['time_format'])
            row.append(smart_str(value))
        writer.writerow(row)

    return response


xls_options_default = {'date_format': 'd/m/Y',
                       'datetime_format': 'N j, Y, P',
                       'time_format': 'P',
                       'sheet_name': 'Sheet1',
                       'DateField': 'DD MMM-YY',
                       'DateTimeField': 'DD MMD YY hh:mm',
                       'TimeField': 'hh:mm',
                       'IntegerField': '#,##',
                       'PositiveIntegerField': '#,##',
                       'PositiveSmallIntegerField': '#,##',
                       'BigIntegerField': '#,##',
                       'DecimalField': '#,##0.00',
                       'BooleanField': 'boolean',
                       'NullBooleanField': 'boolean',
                       'EmailField': lambda value: 'HYPERLINK("mailto:%s","%s")' % (value, value),
                       'URLField': lambda value: 'HYPERLINK("%s","%s")' % (value, value),
                       'CurrencyColumn': '"$"#,##0.00);[Red]("$"#,##0.00)', }


def export_as_xls(queryset, fields=None, header=None, filename=None, options=None, out=None):
# sheet_name=None,  header_alt=None,
#             formatting=None, out=None):
    """
    Exports a queryset as xls from a queryset with the given fields.

    :param queryset: queryset to export (can also be list of namedtuples)
    :param fields: list of fields names to export. None for all fields
    :param header: if True, the exported file will have the first row as column names
    :param out: object that implements File protocol.
    :param header_alt: if is not None, and header is True, the first row will be as header_alt (same nr columns)
    :param formatting: if is None will use formatting_default
    :return: HttpResponse instance if out not supplied, otherwise out
    """

    def _get_qs_formats(queryset):
        formats = {}
        if hasattr(queryset, 'model'):
            for i, fieldname in enumerate(fields):
                try:
                    f, __, __, __, = queryset.model._meta.get_field_by_name(fieldname)
                    fmt = xls_options_default.get(f.name, xls_options_default.get(f.__class__.__name__, 'general'))
                    formats[i] = fmt
                except FieldDoesNotExist:
                    pass
                    # styles[i] = xlwt.easyxf(num_format_str=xls_options_default.get(col_class, 'general'))
                    # styles[i] = xls_options_default.get(col_class, 'general')

        return formats

    if out is None:
        if filename is None:
            filename = filename or "%s.xls" % queryset.model._meta.verbose_name_plural.lower().replace(" ", "_")
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment;filename="%s"' % filename.encode('us-ascii', 'replace')
    else:
        response = out

    config = xls_options_default.copy()
    if options:
        config.update(options)

    if fields is None:
        fields = [f.name for f in queryset.model._meta.fields]

    book = xlwt.Workbook(encoding="UTF-8")
    sheet_name = config.pop('sheet_name')

    sheet = book.add_sheet(sheet_name)
    style = xlwt.XFStyle()
    row = 0
    heading_xf = xlwt.easyxf('font:height 200; font: bold on; align: wrap on, vert centre, horiz center')
    sheet.write(row, 0, '#', style)
    if header:
        if not isinstance(header, (list, tuple)):
            header = [unicode(f.verbose_name) for f in queryset.model._meta.fields if f.name in fields]

        for col, fieldname in enumerate(header, start=1):
            sheet.write(row, col, fieldname, heading_xf)
            sheet.col(col).width = 5000

    sheet.row(row).height = 500
    formats = _get_qs_formats(queryset)

    for rownum, row in enumerate(queryset):
        sheet.write(rownum + 1, 0, rownum + 1)
        for idx, fieldname in enumerate(fields):
            fmt = formats.get(idx, 'general')
            try:
                value = get_field_value(row, fieldname, usedisplay=False, raw_callable=False)
                if callable(fmt):
                    value = xlwt.Formula(fmt(value))
                    style = xlwt.easyxf(num_format_str='formula')
                else:
                    style = xlwt.easyxf(num_format_str=fmt)
                sheet.write(rownum + 1, idx + 1, value, style)
            except Exception as e:
                #logger.warning("TODO refine this exception: %s" % e)
                sheet.write(rownum + 1, idx + 1, str(e), style)

    book.save(response)
    return response
