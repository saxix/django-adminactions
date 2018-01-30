import collections
import csv
import datetime
import itertools
from io import BytesIO

import xlwt
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import FileField
from django.db.models.fields import FieldDoesNotExist
from django.db.models.fields.related import ManyToManyField, OneToOneField
from django.db.transaction import atomic
from django.http import HttpResponse, StreamingHttpResponse
from django.utils import dateformat
from django.utils.encoding import force_text, smart_str, smart_text
from django.utils.timezone import get_default_timezone

from . import compat
from .templatetags.actions import get_field_value
from .utils import clone_instance, get_field_by_path

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


def merge(master, other, fields=None, commit=False, m2m=None, related=None):  # noqa
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
                   for rel in compat.get_all_related_objects(master)]
    # for rel in master._meta.get_all_related_objects(False, False, False)]

    if m2m == ALL_FIELDS:
        m2m = set()
        for field in master._meta.get_fields():
            if getattr(field, 'many_to_many', None):
                if isinstance(field, ManyToManyField):
                    if not field.remote_field.through._meta.auto_created:
                        continue
                    m2m.add(field.name)
                else:
                    # reverse relation
                    m2m.add(field.get_accessor_name())
    if m2m and not commit:
        raise ValueError('Cannot save related with `commit=False`')
    with atomic():
        result = clone_instance(master)

        for fieldname in fields:
            f = get_field_by_path(master, fieldname)
            if isinstance(f, FileField) or f and not f.primary_key:
                setattr(result, fieldname, getattr(other, fieldname))

        if m2m:
            for accessor in set(m2m):
                all_m2m[accessor] = []
                source_m2m = getattr(other, accessor)
                for r in source_m2m.all():
                    all_m2m[accessor].append(r)
        if related:
            for name in set(related):
                related_object = get_field_by_path(master, name)
                all_related[name] = []
                if related_object and isinstance(related_object.field, OneToOneField):
                    try:
                        accessor = getattr(other, name)
                        all_related[name] = [(related_object.field.name, accessor)]
                    except ObjectDoesNotExist:
                        pass
                else:
                    accessor = getattr(other, name, None)
                    if accessor:
                        rel_fieldname = list(accessor.core_filters.keys())[0].split('__')[0]
                        for r in accessor.all():
                            all_related[name].append((rel_fieldname, r))

        if commit:
            for name, elements in list(all_related.items()):
                for rel_fieldname, element in elements:
                    setattr(element, rel_fieldname, master)
                    element.save()
            other.delete()
            result.save()
            for fieldname, elements in list(all_m2m.items()):
                dest_m2m = getattr(result, fieldname)
                for element in elements:
                    dest_m2m.add(element)
    return result


class Echo(object):
    """An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def export_as_csv(queryset, fields=None, header=None,  # noqa
                  filename=None, options=None, out=None):
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
    streaming_enabled = (
        getattr(settings, 'ADMINACTIONS_STREAM_CSV', False)
    )
    if out is None:
        if streaming_enabled:
            response_class = StreamingHttpResponse
        else:
            response_class = HttpResponse

        if filename is None:
            filename = filename or "%s.csv" % queryset.model._meta.verbose_name_plural.lower().replace(" ", "_")
        response = response_class(content_type='text/csv')
        response['Content-Disposition'] = ('attachment;filename="%s"' % filename).encode('us-ascii', 'replace')
    else:
        response = out

    if options is None:
        config = csv_options_default
    else:
        config = csv_options_default.copy()
        config.update(options)

    if fields is None:
        fields = [f.name for f in queryset.model._meta.fields +
                  queryset.model._meta.many_to_many]

    if streaming_enabled:
        buffer_object = Echo()
    else:
        buffer_object = response

    dialect = config.get('dialect', None)
    if dialect is not None:
        writer = csv.writer(buffer_object, dialect=dialect)
    else:
        writer = csv.writer(buffer_object,
                            escapechar=str(config['escapechar']),
                            delimiter=str(config['delimiter']),
                            quotechar=str(config['quotechar']),
                            quoting=int(config['quoting']))

    settingstime_zone = get_default_timezone()

    def yield_header():
        if bool(header):
            if isinstance(header, (list, tuple)):
                yield writer.writerow(header)
            else:
                yield writer.writerow([f for f in fields])
        yield ''

    def yield_rows():
        for obj in queryset:
            row = []
            for fieldname in fields:
                value = get_field_value(obj, fieldname)
                if isinstance(value, datetime.datetime):
                    try:
                        value = dateformat.format(value.astimezone(settingstime_zone), config['datetime_format'])
                    except ValueError:
                        # astimezone() cannot be applied to a naive datetime
                        value = dateformat.format(value, config['datetime_format'])
                elif isinstance(value, datetime.date):
                    value = dateformat.format(value, config['date_format'])
                elif isinstance(value, datetime.time):
                    value = dateformat.format(value, config['time_format'])
                row.append(smart_str(value))
            yield writer.writerow(row)

    if streaming_enabled:
        content_attr = 'content' if (
            StreamingHttpResponse is HttpResponse) else 'streaming_content'
        setattr(response, content_attr,
                itertools.chain(yield_header(), yield_rows()))
    else:
        collections.deque(itertools.chain(
            yield_header(), yield_rows()), maxlen=0)

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


def export_as_xls2(queryset, fields=None, header=None,  # noqa
                   filename=None, options=None, out=None):
    # sheet_name=None,  header_alt=None,
    # formatting=None, out=None):
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
                    f, __, __, __, = compat.get_field_by_name(queryset.model, fieldname)
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
        response['Content-Disposition'] = ('attachment;filename="%s"' % filename).encode('us-ascii', 'replace')
    else:
        response = out

    config = xls_options_default.copy()
    if options:
        config.update(options)

    if fields is None:
        fields = [f.name for f in queryset.model._meta.fields +
                  queryset.model._meta.many_to_many]

    book = xlwt.Workbook(encoding="utf-8", style_compression=2)
    sheet_name = config.pop('sheet_name')
    use_display = config.get('use_display', False)

    sheet = book.add_sheet(sheet_name)
    style = xlwt.XFStyle()
    row = 0
    heading_xf = xlwt.easyxf('font:height 200; font: bold on; align: wrap on, vert centre, horiz center')
    sheet.write(row, 0, u'#', style)
    if header:
        if not isinstance(header, (list, tuple)):
            header = [force_text(f.verbose_name) for f in
                      queryset.model._meta.fields + queryset.model._meta.many_to_many if f.name in fields]

        for col, fieldname in enumerate(header, start=1):
            sheet.write(row, col, fieldname, heading_xf)
            sheet.col(col).width = 5000

    sheet.row(row).height = 500
    formats = _get_qs_formats(queryset)

    _styles = {}

    for rownum, row in enumerate(queryset):
        sheet.write(rownum + 1, 0, rownum + 1)
        for col_idx, fieldname in enumerate(fields):
            fmt = formats.get(col_idx, 'general')
            try:
                value = get_field_value(row,
                                        fieldname,
                                        usedisplay=use_display,
                                        raw_callable=False)
                if callable(fmt):
                    value = xlwt.Formula(fmt(value))
                if hash(fmt) not in _styles:
                    if callable(fmt):
                        _styles[hash(fmt)] = xlwt.easyxf(num_format_str='formula')
                    elif isinstance(value, datetime.datetime):
                        _styles[hash(fmt)] = xlwt.easyxf(num_format_str=config['datetime_format'])
                    elif isinstance(value, datetime.date):
                        _styles[hash(fmt)] = xlwt.easyxf(num_format_str=config['date_format'])
                    elif isinstance(value, datetime.datetime):
                        _styles[hash(fmt)] = xlwt.easyxf(num_format_str=config['time_format'])
                    else:
                        _styles[hash(fmt)] = xlwt.easyxf(num_format_str=fmt)

                if isinstance(value, (list, tuple)):
                    value = "".join(value)

                sheet.write(rownum + 1, col_idx + 1, value, _styles[hash(fmt)])
            except Exception as e:
                sheet.write(rownum + 1, col_idx + 1, smart_str(e), _styles[hash(fmt)])

    book.save(response)
    return response


xlsxwriter_options = {'date_format': 'd/m/Y',
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
                      # 'EmailField': lambda value: 'HYPERLINK("mailto:%s","%s")' % (value, value),
                      # 'URLField': lambda value: 'HYPERLINK("%s","%s")' % (value, value),
                      'CurrencyColumn': '"$"#,##0.00);[Red]("$"#,##0.00)', }


def export_as_xls3(queryset, fields=None, header=None,  # noqa
                   filename=None, options=None, out=None):  # pragma: no cover
    # sheet_name=None,  header_alt=None,
    # formatting=None, out=None):
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
    import xlsxwriter

    def _get_qs_formats(queryset):
        formats = {'_general_': book.add_format()}
        if hasattr(queryset, 'model'):
            for i, fieldname in enumerate(fields):
                try:
                    f, __, __, __, = queryset.model._meta.get_field_by_name(fieldname)
                    pattern = xlsxwriter_options.get(f.name, xlsxwriter_options.get(f.__class__.__name__, 'general'))
                    fmt = book.add_format({'num_format': pattern})
                    formats[fieldname] = fmt
                except FieldDoesNotExist:
                    pass
                    # styles[i] = xlwt.easyxf(num_format_str=xls_options_default.get(col_class, 'general'))
                    # styles[i] = xls_options_default.get(col_class, 'general')

        return formats

    http_response = out is None
    if out is None:
        # if filename is None:
        # filename = filename or "%s.xls" % queryset.model._meta.verbose_name_plural.lower().replace(" ", "_")
        # response = HttpResponse(content_type='application/vnd.ms-excel')
        # response['Content-Disposition'] = 'attachment;filename="%s"' % filename.encode('us-ascii', 'replace')
        out = BytesIO()
        #
        # out = StringIO()

    config = xlsxwriter_options.copy()
    if options:
        config.update(options)

    if fields is None:
        fields = [f.name for f in queryset.model._meta.fields +
                  queryset.model._meta.many_to_many]

    book = xlsxwriter.Workbook(out, {'in_memory': True})
    sheet_name = config.pop('sheet_name')
    use_display = config.get('use_display', False)
    sheet = book.add_worksheet(sheet_name)
    book.close()
    formats = _get_qs_formats(queryset)

    row = 0
    sheet.write(row, 0, force_text('#'), formats['_general_'])
    if header:
        if not isinstance(header, (list, tuple)):
            header = [force_text(f.verbose_name) for f in
                      queryset.model._meta.fields + queryset.model._meta.many_to_many if f.name in fields]

        for col, fieldname in enumerate(header, start=1):
            sheet.write(row, col, force_text(fieldname), formats['_general_'])

    settingstime_zone = get_default_timezone()

    for rownum, row in enumerate(queryset):
        sheet.write(rownum + 1, 0, rownum + 1)
        for idx, fieldname in enumerate(fields):
            fmt = formats.get(fieldname, formats['_general_'])
            try:
                value = get_field_value(row,
                                        fieldname,
                                        usedisplay=use_display,
                                        raw_callable=False)
                if callable(fmt):
                    value = fmt(value)
                if isinstance(value, (list, tuple)):
                    value = smart_text(u"".join(value))

                if isinstance(value, datetime.datetime):
                    try:
                        value = dateformat.format(value.astimezone(settingstime_zone), config['datetime_format'])
                    except ValueError:
                        value = dateformat.format(value, config['datetime_format'])

                # if isinstance(value, six.binary_type):
                value = str(value)

                sheet.write(rownum + 1, idx + 1, smart_text(value), fmt)
            except Exception as e:
                raise
                sheet.write(rownum + 1, idx + 1, smart_text(e), fmt)

    book.close()
    out.seek(0)
    if http_response:
        if filename is None:
            filename = filename or "%s.xls" % queryset.model._meta.verbose_name_plural.lower().replace(" ", "_")
        response = HttpResponse(out.read(),
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        # content_type='application/vnd.ms-excel')
        # response['Content-Disposition'] = six.b('attachment;filename="%s"') % six.b(filename.encode('us-ascii', 'replace'))
        response['Content-Disposition'] = 'attachment;filename="%s"' % filename
        return response
    return out


export_as_xls = export_as_xls2
