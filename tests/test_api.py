from __future__ import annotations

import csv
import io
import unittest
from collections import namedtuple

import django
import xlrd
from django.contrib.auth.models import Permission
from django.http import HttpResponse
from django.test import TestCase

from adminactions.api import export_as_csv, export_as_xls


class TestExportQuerySetAsCsv(TestCase):
    def test_default_params(self) -> None:
        with self.assertNumQueries(1):
            qs = Permission.objects.select_related().filter(codename="add_user")
            ret = export_as_csv(queryset=qs)
        assert isinstance(ret, HttpResponse)
        if django.VERSION[0] == 2:
            assert ret.content.decode("utf8") == f'"{qs[0].pk}";"Can add user";"user";"add_user"\r\n'
        elif django.VERSION[0] == 3:
            assert ret.content.decode("utf8") == f'"{qs[0].pk}";"Can add user";"auth | user";"add_user"\r\n'

    def test_header_is_true(self) -> None:
        mem = io.StringIO()
        with self.assertNumQueries(1):
            qs = Permission.objects.select_related().filter(codename="add_user")
            export_as_csv(queryset=qs, header=True, out=mem)
        mem.seek(0)
        csv_reader = csv.reader(mem)
        assert next(csv_reader) == ['id;"name";"content_type";"codename"']

    def test_queryset_values(self) -> None:
        fields = ["codename", "content_type__app_label"]
        header = ["Name", "Application"]
        mem = io.StringIO()
        with self.assertNumQueries(1):
            qs = Permission.objects.filter(codename="add_user").values("codename", "content_type__app_label")
            export_as_csv(queryset=qs, fields=fields, header=header, out=mem)
        mem.seek(0)
        csv_dump = mem.read()
        assert csv_dump == '"Name";"Application"\r\n"add_user";"auth"\r\n'

    def test_callable_method(self) -> None:
        fields = ["codename", "natural_key"]
        mem = io.StringIO()
        with self.assertNumQueries(2):
            qs = Permission.objects.filter(codename="add_user")
            export_as_csv(queryset=qs, fields=fields, out=mem)
        mem.seek(0)
        csv_dump = mem.read()
        assert csv_dump == "\"add_user\";\"('add_user', 'auth', 'user')\"\r\n"

    def test_deep_attr(self) -> None:
        fields = ["codename", "content_type.app_label"]
        mem = io.StringIO()
        with self.assertNumQueries(1):
            qs = Permission.objects.select_related().filter(codename="add_user")
            export_as_csv(queryset=qs, fields=fields, out=mem)
        mem.seek(0)
        csv_dump = mem.read()
        assert csv_dump == '"add_user";"auth"\r\n'


class TestExportAsCsv(unittest.TestCase):
    def test_export_as_csv(self) -> None:
        fields = ["field1", "field2"]
        header = ["Field 1", "Field 2"]
        Row = namedtuple("Row", fields)
        rows = [Row(1, 4), Row(2, 5), Row(3, "ӼӳӬԖԊ")]
        mem = io.StringIO()
        export_as_csv(queryset=rows, fields=fields, header=header, out=mem)
        mem.seek(0)
        csv_dump = mem.read()
        assert csv_dump == '"Field 1";"Field 2"\r\n"1";"4"\r\n"2";"5"\r\n"3";"ӼӳӬԖԊ"\r\n'

    def test_dialect(self) -> None:
        fields = ["field1", "field2"]
        header = ["Field 1", "Field 2"]
        Row = namedtuple("Row", fields)
        rows = [Row(1, 4), Row(2, 5), Row(3, "ӼӳӬԖԊ")]
        mem = io.StringIO()
        export_as_csv(
            queryset=rows,
            fields=fields,
            header=header,
            out=mem,
            options={"dialect": "excel"},
        )
        mem.seek(0)
        csv_dump = mem.read()
        assert csv_dump == "Field 1,Field 2\r\n1,4\r\n2,5\r\n3,ӼӳӬԖԊ\r\n"


class TestExportAsExcel(TestCase):
    def test_default_params(self) -> None:
        with self.assertNumQueries(1):
            qs = Permission.objects.select_related().filter(codename="add_user")
            ret = export_as_xls(queryset=qs)
        assert isinstance(ret, HttpResponse)

    def test_header_is_true(self) -> None:
        mem = io.BytesIO()
        with self.assertNumQueries(1):
            qs = Permission.objects.select_related().filter(codename="add_user")
            export_as_xls(queryset=qs, header=True, out=mem)
        mem.seek(0)
        xls_workbook = xlrd.open_workbook(file_contents=mem.read())
        xls_sheet = xls_workbook.sheet_by_index(0)
        assert xls_sheet.row_values(0)[:] == ["#", "ID", "name", "content type", "codename"]

    def test_export_as_xls(self) -> None:
        fields = ["field1", "field2"]
        header = ["Field 1", "Field 2"]
        Row = namedtuple("Row", fields)
        rows = [Row(111, 222), Row(333, 444), Row(555, "ӼӳӬԖԊ")]
        mem = io.BytesIO()
        export_as_xls(queryset=rows, fields=fields, header=header, out=mem)
        mem.seek(0)

        xls_workbook = xlrd.open_workbook(file_contents=mem.read())
        xls_sheet = xls_workbook.sheet_by_index(0)
        assert xls_sheet.row_values(0)[:] == ["#", "Field 1", "Field 2"]
        assert xls_sheet.row_values(1)[:] == [1.0, 111.0, 222.0]
        assert xls_sheet.row_values(2)[:] == [2.0, 333.0, 444.0]
        assert xls_sheet.row_values(3)[:] == [3.0, 555.0, "ӼӳӬԖԊ"]


class TestExportQuerySetAsExcel(TestCase):
    def test_queryset_values(self) -> None:
        fields = ["codename", "content_type__app_label"]
        header = ["Name", "Application"]
        qs = Permission.objects.filter(codename="add_user").values("codename", "content_type__app_label")
        mem = io.BytesIO()
        export_as_xls(queryset=qs, fields=fields, header=header, out=mem)
        mem.seek(0)
        w = xlrd.open_workbook(file_contents=mem.read())
        sheet = w.sheet_by_index(0)
        assert sheet.cell_value(1, 1) == "add_user"
        assert sheet.cell_value(1, 2) == "auth"

    def test_callable_method(self) -> None:
        fields = ["codename", "natural_key"]
        qs = Permission.objects.filter(codename="add_user")
        mem = io.BytesIO()
        export_as_xls(queryset=qs, fields=fields, out=mem)
        mem.seek(0)
        content = mem.read()
        w = xlrd.open_workbook(file_contents=content)
        sheet = w.sheet_by_index(0)
        assert sheet.cell_value(1, 1) == "add_user"
        assert sheet.cell_value(1, 2) == "add_userauthuser"
