from __future__ import annotations

import collections
import csv
import datetime
import itertools
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import xlwt  # type: ignore[import-untyped]
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist
from django.db.models import FileField, Model
from django.db.models.fields.related import ManyToManyField, OneToOneField
from django.db.transaction import atomic
from django.http import HttpResponse, StreamingHttpResponse
from django.utils import dateformat
from django.utils.encoding import force_str, smart_str
from django.utils.timezone import get_default_timezone

from adminactions import utils

from .utils import clone_instance, get_field_by_path, get_field_value, get_ignored_fields

if TYPE_CHECKING:
    from collections.abc import Generator

    from django.contrib.admin.options import ModelAdmin
    from django.core.files.base import File
    from django.db.models.query import QuerySet

    from .forms import CSVOptions

csv_options_default: dict[str, str | int] = {
    "date_format": "d/m/Y",
    "datetime_format": "N j, Y, P",
    "time_format": "P",
    "header": False,
    "quotechar": '"',
    "quoting": csv.QUOTE_ALL,
    "delimiter": ";",
    "escapechar": "\\",
}

delimiters = ",;|:"
quotes = "'\"`"
escapechars = " \\"
ALL_FIELDS = -999


def merge(  # noqa: C901, PLR0912, PLR0915
    master: Model,
    other: Model,
    fields: Iterable[str] | None = None,
    commit: bool = False,
    m2m: Iterable[str] | int | None = None,
    related: Iterable[str] | int | None = None,
) -> Model:
    """
        Merge 'other' into master.

        `fields` is a list of fieldnames that must be readed from ``other`` to put into master.
        If ``fields`` is None ``master`` will not get any of the ``other`` values.
        Finally ``other`` will be deleted and master will be preserved

    @param master:  Model instance
    @param other: Model instance
    @param fields: list of fieldnames to  merge
    @param m2m: list of m2m fields to merge. If empty will be removed
    @param related: list of related fieldnames to merge. If empty will be removed
    @return:
    """

    fields = fields or []
    related_names: Iterable[str]

    all_m2m: dict[str, list[Any]] = {}
    all_related: dict[str, list[Any]] = {}

    if related == ALL_FIELDS:
        related_names = [rel.get_accessor_name() for rel in utils.get_all_related_objects(master)]
    elif isinstance(related, Iterable):
        related_names = related
    else:
        related_names = []

    if m2m == ALL_FIELDS:
        m2m = set()
        for field in master._meta.get_fields():
            if getattr(field, "many_to_many", None):
                if isinstance(field, ManyToManyField):
                    if not field.remote_field.through._meta.auto_created:
                        continue
                    m2m.add(field.name)
                else:
                    # reverse relation
                    m2m.add(field.get_accessor_name())
    if m2m and not commit:
        raise ValueError("Cannot save related with `commit=False`")
    with atomic():
        result = clone_instance(master)
        for fieldname in fields:
            f = get_field_by_path(master, fieldname)
            if isinstance(f, FileField) or (f and not f.primary_key):
                setattr(result, fieldname, getattr(other, fieldname))

        if m2m:
            for accessor in set(m2m):
                all_m2m[accessor] = []
                source_m2m = getattr(other, accessor)
                for r in source_m2m.all():
                    all_m2m[accessor].append(r)
        if related_names:
            for name in set(related_names):
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
                        rel_fieldname = next(iter(accessor.core_filters.keys()))
                        for r in accessor.all():
                            all_related[name].append((rel_fieldname, r))

        if commit:
            for __, elements in list(all_related.items()):
                for rel_fieldname, element in elements:
                    setattr(element, rel_fieldname, master)
                    element.save()
            other.delete()
            ignored_fields = get_ignored_fields(result._meta.model, "MERGE_ACTION_IGNORED_FIELDS")
            for ig_field in ignored_fields:
                setattr(result, ig_field, result._meta.get_field(ig_field).get_default())
            result.save()
            for fieldname, elements in list(all_m2m.items()):
                dest_m2m = getattr(result, fieldname)
                for element in elements:
                    dest_m2m.add(element)
    return result


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value: Any) -> Any:  # noqa: PLR6301
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def export_as_csv(  # noqa: C901,
    queryset: QuerySet,
    fields: list[str] | None = None,
    header: bool = False,
    filename: str | None = None,
    options: CSVOptions | None = None,
    out: File | None = None,
    modeladmin: ModelAdmin = None,
) -> HttpResponse:
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
    streaming_enabled = getattr(settings, "ADMINACTIONS_STREAM_CSV", False)
    if out is None:
        response_class = StreamingHttpResponse if streaming_enabled else HttpResponse

        if filename is None:
            filename = "{}.csv".format(queryset.model._meta.verbose_name_plural.lower().replace(" ", "_"))

        response = response_class(content_type="text/csv")
        response["Content-Disposition"] = (f'attachment;filename="{filename}"').encode("us-ascii", "replace")
    else:
        response = out

    if options is None:
        config = csv_options_default
    else:
        config = csv_options_default.copy()
        config.update(options)

    if fields is None:
        fields = [f.name for f in queryset.model._meta.fields + queryset.model._meta.many_to_many]
    buffer_object = Echo() if streaming_enabled else response

    dialect = config.get("dialect", None)
    if dialect is not None:
        writer = csv.writer(buffer_object, dialect=dialect)
    else:
        writer = csv.writer(
            buffer_object,
            escapechar=config["escapechar"],
            delimiter=str(config["delimiter"]),
            quotechar=str(config["quotechar"]),
            quoting=int(config["quoting"]),
        )

    settingstime_zone = get_default_timezone()

    def yield_header() -> Generator[str, None, None]:
        if bool(header):
            if isinstance(header, (list | tuple)):
                yield writer.writerow(header)
            else:
                yield writer.writerow(list(fields))
        yield ""

    def yield_rows() -> Generator[str, None, None]:
        for obj in queryset:
            row = []
            for fieldname in fields:
                value = get_field_value(obj, fieldname, modeladmin=modeladmin)
                if isinstance(value, datetime.datetime):
                    try:
                        value = dateformat.format(
                            value.astimezone(settingstime_zone),
                            config["datetime_format"],
                        )
                    except ValueError:
                        # astimezone() cannot be applied to a naive datetime
                        value = dateformat.format(value, config["datetime_format"])
                elif isinstance(value, datetime.date):
                    value = dateformat.format(value, config["date_format"])
                elif isinstance(value, datetime.time):
                    value = dateformat.format(value, config["time_format"])
                row.append(smart_str(value))
            yield writer.writerow(row)

    if streaming_enabled:
        content_attr = "content" if (StreamingHttpResponse is HttpResponse) else "streaming_content"
        setattr(response, content_attr, itertools.chain(yield_header(), yield_rows()))
    else:
        collections.deque(itertools.chain(yield_header(), yield_rows()), maxlen=0)

    return response


xls_options_default = {
    "date_format": "d/m/Y",
    "datetime_format": "N j, Y, P",
    "time_format": "P",
    "sheet_name": "Sheet1",
    "DateField": "DD MMM-YY",
    "DateTimeField": "DD MMD YY hh:mm",
    "TimeField": "hh:mm",
    "IntegerField": "#,##",
    "PositiveIntegerField": "#,##",
    "PositiveSmallIntegerField": "#,##",
    "BigIntegerField": "#,##",
    "DecimalField": "#,##0.00",
    "BooleanField": "boolean",
    "NullBooleanField": "boolean",
    "EmailField": lambda value: f'HYPERLINK("mailto:{value}","{value}")',
    "URLField": lambda value: f'HYPERLINK("{value}","{value}")',
    "CurrencyColumn": '"$"#,##0.00);[Red]("$"#,##0.00)',
}


def export_as_xls2(  # noqa: C901, PLR0912, PLR0914, PLR0915
    queryset: QuerySet[Model],
    fields: list[str] | None = None,
    header: bool = False,
    filename: str | None = None,
    options: dict[str, int | str] | None = None,
    out: File | None = None,
    modeladmin: ModelAdmin[Model] | None = None,
) -> HttpResponse:
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

    def _get_qs_formats(selected_fields: list[str], queryset: QuerySet[Model]) -> dict[int, str]:
        formats: dict[int, str] = {}
        if hasattr(queryset, "model"):
            for i, _fieldname in enumerate(selected_fields):
                try:
                    (
                        f,
                        __,
                        __,
                        __,
                    ) = utils.get_field_by_name(queryset.model, _fieldname)
                    fmt_ = xls_options_default.get(f.name, xls_options_default.get(f.__class__.__name__, "general"))
                    formats[i] = fmt_
                except FieldDoesNotExist:
                    pass

        return formats

    if out is None:
        if filename is None:
            filename = "{}.xls".format(queryset.model._meta.verbose_name_plural.lower().replace(" ", "_"))

        response = HttpResponse(content_type="application/vnd.ms-excel")
        response["Content-Disposition"] = (f'attachment;filename="{filename}"').encode("us-ascii", "replace")
    else:
        response = out

    config = xls_options_default.copy()
    if options:
        config.update(options)

    if fields is None:
        fields = [f.name for f in queryset.model._meta.fields + queryset.model._meta.many_to_many]

    book = xlwt.Workbook(encoding="utf-8", style_compression=2)
    sheet_name = config.pop("sheet_name")
    use_display = bool(config.get("use_display", False))

    sheet = book.add_sheet(sheet_name)
    style = xlwt.XFStyle()
    row = 0
    heading_xf = xlwt.easyxf("font:height 200; font: bold on; align: wrap on, vert centre, horiz center")
    sheet.write(row, 0, "#", style)
    if header:
        if isinstance(header, (list | tuple)):
            header_line = header
        else:
            header_line = [
                force_str(f.verbose_name)
                for f in queryset.model._meta.fields + queryset.model._meta.many_to_many
                if f.name in fields
            ]

        for col, fieldname in enumerate(header_line, start=1):
            sheet.write(row, col, fieldname, heading_xf)
            sheet.col(col).width = 5000

    sheet.row(row).height = 500
    formats = _get_qs_formats(fields, queryset)

    styles_ = {}
    for rownum, instance in enumerate(queryset):
        sheet.write(rownum + 1, 0, rownum + 1)
        for col_idx, fieldname in enumerate(fields):
            fmt = formats.get(col_idx, "general")
            try:
                value = get_field_value(
                    instance,
                    fieldname,
                    usedisplay=use_display,
                    raw_callable=False,
                    modeladmin=modeladmin,
                )
                if callable(fmt):
                    value = xlwt.Formula(fmt(value))
                if hash(fmt) not in styles_:
                    if callable(fmt):
                        styles_[hash(fmt)] = xlwt.easyxf(num_format_str="formula")
                    elif isinstance(value, datetime.datetime):
                        styles_[hash(fmt)] = xlwt.easyxf(num_format_str=config["datetime_format"])
                    elif isinstance(value, datetime.date):
                        styles_[hash(fmt)] = xlwt.easyxf(num_format_str=config["date_format"])
                    elif isinstance(value, datetime.datetime):
                        styles_[hash(fmt)] = xlwt.easyxf(num_format_str=config["time_format"])
                    else:
                        styles_[hash(fmt)] = xlwt.easyxf(num_format_str=fmt)

                if isinstance(value, (list | tuple)):
                    value = "".join(value)

                sheet.write(rownum + 1, col_idx + 1, value, styles_[hash(fmt)])
            except Exception as e:  # noqa: BLE001
                sheet.write(rownum + 1, col_idx + 1, smart_str(e), styles_[hash(fmt)])

    book.save(response)
    return response


xlsxwriter_options = {
    "date_format": "d/m/Y",
    "datetime_format": "N j, Y, P",
    "time_format": "P",
    "sheet_name": "Sheet1",
    "DateField": "DD MMM-YY",
    "DateTimeField": "DD MMD YY hh:mm",
    "TimeField": "hh:mm",
    "IntegerField": "#,##",
    "PositiveIntegerField": "#,##",
    "PositiveSmallIntegerField": "#,##",
    "BigIntegerField": "#,##",
    "DecimalField": "#,##0.00",
    "BooleanField": "boolean",
    "NullBooleanField": "boolean",
    "CurrencyColumn": '"$"#,##0.00);[Red]("$"#,##0.00)',
}

export_as_xls = export_as_xls2
