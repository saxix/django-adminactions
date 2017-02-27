# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import six
import unittest
from collections import namedtuple

import xlrd
from django.contrib.auth.models import Permission
from django.http import HttpResponse
from django.test import TestCase

from adminactions.api import export_as_csv, export_as_xls

if six.PY3:
    import csv
elif six.PY2:
    import unicodecsv as csv


class TestExportQuerySetAsCsv(TestCase):
    def test_default_params(self):
        with self.assertNumQueries(1):
            qs = Permission.objects.select_related().filter(codename='add_user')
            ret = export_as_csv(queryset=qs)
        self.assertIsInstance(ret, HttpResponse)
        self.assertEqual(ret.content.decode('utf8'), u'"%s";"Can add user";"user";"add_user"\r\n' % qs[0].pk)

    def test_header_is_true(self):
        mem = six.StringIO()
        with self.assertNumQueries(1):
            qs = Permission.objects.select_related().filter(codename='add_user')
            export_as_csv(queryset=qs, header=True, out=mem)
        mem.seek(0)
        csv_reader = csv.reader(mem)
        self.assertEqual(next(csv_reader), [u'id;"name";"content_type";"codename"'])

    def test_queryset_values(self):
        fields = ['codename', 'content_type__app_label']
        header = ['Name', 'Application']
        mem = six.StringIO()
        with self.assertNumQueries(1):
            qs = Permission.objects.filter(codename='add_user').values('codename', 'content_type__app_label')
            export_as_csv(queryset=qs, fields=fields, header=header, out=mem)
        mem.seek(0)
        csv_dump = mem.read()
        if six.PY2:
            self.assertEqual(csv_dump.decode('utf8'), u'"Name";"Application"\r\n"add_user";"auth"\r\n')
        else:
            self.assertEqual(csv_dump, '"Name";"Application"\r\n"add_user";"auth"\r\n')

    def test_callable_method(self):
        fields = ['codename', 'natural_key']
        mem = six.StringIO()
        with self.assertNumQueries(2):
            qs = Permission.objects.filter(codename='add_user')
            export_as_csv(queryset=qs, fields=fields, out=mem)
        mem.seek(0)
        csv_dump = mem.read()
        if six.PY2:
            self.assertEqual(csv_dump.decode('utf8'), u'"add_user";"(u\'add_user\', u\'auth\', u\'user\')"\r\n')
        else:
            self.assertEqual(csv_dump, '"add_user";"(\'add_user\', \'auth\', \'user\')"\r\n')

    def test_deep_attr(self):
        fields = ['codename', 'content_type.app_label']
        mem = six.StringIO()
        with self.assertNumQueries(1):
            qs = Permission.objects.select_related().filter(codename='add_user')
            export_as_csv(queryset=qs, fields=fields, out=mem)
        mem.seek(0)
        csv_dump = mem.read()
        if six.PY2:
            self.assertEqual(csv_dump.decode('utf8'), u'"add_user";"auth"\r\n')
        else:
            self.assertEqual(csv_dump, '"add_user";"auth"\r\n')


class TestExportAsCsv(unittest.TestCase):
    def test_export_as_csv(self):
        fields = ['field1', 'field2']
        header = ['Field 1', 'Field 2']
        Row = namedtuple('Row', fields)
        rows = [Row(1, 4),
                Row(2, 5),
                Row(3, u'ӼӳӬԖԊ')]
        mem = six.StringIO()
        export_as_csv(queryset=rows, fields=fields, header=header, out=mem)
        mem.seek(0)
        csv_dump = mem.read()
        if six.PY2:
            self.assertEqual(csv_dump.decode('utf8'), u'"Field 1";"Field 2"\r\n"1";"4"\r\n"2";"5"\r\n"3";"ӼӳӬԖԊ"\r\n')
        else:
            self.assertEqual(csv_dump, '"Field 1";"Field 2"\r\n"1";"4"\r\n"2";"5"\r\n"3";"ӼӳӬԖԊ"\r\n')

    def test_dialect(self):
        fields = ['field1', 'field2']
        header = ['Field 1', 'Field 2']
        Row = namedtuple('Row', fields)
        rows = [Row(1, 4),
                Row(2, 5),
                Row(3, 'ӼӳӬԖԊ')]
        mem = six.StringIO()
        export_as_csv(queryset=rows, fields=fields, header=header,
                      out=mem, options={'dialect': 'excel'})
        mem.seek(0)
        csv_dump = mem.read()
        if six.PY2:
            self.assertEqual(csv_dump.decode('utf8'), u'Field 1,Field 2\r\n1,4\r\n2,5\r\n3,ӼӳӬԖԊ\r\n')
        else:
            self.assertEqual(csv_dump, 'Field 1,Field 2\r\n1,4\r\n2,5\r\n3,ӼӳӬԖԊ\r\n')


class TestExportAsExcel(TestCase):
    def test_default_params(self):
        with self.assertNumQueries(1):
            qs = Permission.objects.select_related().filter(codename='add_user')
            ret = export_as_xls(queryset=qs)
        self.assertIsInstance(ret, HttpResponse)

    def test_header_is_true(self):
        mem = six.BytesIO()
        with self.assertNumQueries(1):
            qs = Permission.objects.select_related().filter(codename='add_user')
            export_as_xls(queryset=qs, header=True, out=mem)
        mem.seek(0)
        xls_workbook = xlrd.open_workbook(file_contents=mem.read())
        xls_sheet = xls_workbook.sheet_by_index(0)
        if six.PY2:
            self.assertEqual(xls_sheet.row_values(0)[:], [u'#', u'ID', u'name', u'content type', u'codename'])
        else:
            self.assertEqual(xls_sheet.row_values(0)[:], ['#', 'ID', 'name', 'content type', 'codename'])

    def test_export_as_xls(self):
        fields = ['field1', 'field2']
        header = ['Field 1', 'Field 2']
        Row = namedtuple('Row', fields)
        rows = [Row(111, 222),
                Row(333, 444),
                Row(555, 'ӼӳӬԖԊ')]
        mem = six.BytesIO()
        export_as_xls(queryset=rows, fields=fields, header=header, out=mem)
        mem.seek(0)

        xls_workbook = xlrd.open_workbook(file_contents=mem.read())
        xls_sheet = xls_workbook.sheet_by_index(0)
        if six.PY2:
            self.assertEqual(xls_sheet.row_values(0)[:], [u'#', u'Field 1', u'Field 2'])
        else:
            self.assertEqual(xls_sheet.row_values(0)[:], ['#', 'Field 1', 'Field 2'])
        self.assertEqual(xls_sheet.row_values(1)[:], [1.0, 111.0, 222.0])
        self.assertEqual(xls_sheet.row_values(2)[:], [2.0, 333.0, 444.0])
        self.assertEqual(xls_sheet.row_values(3)[:], [3.0, 555.0, u'ӼӳӬԖԊ'])


class TestExportQuerySetAsExcel(TestCase):
    def test_queryset_values(self):
        fields = ['codename', 'content_type__app_label']
        header = ['Name', 'Application']
        qs = Permission.objects.filter(codename='add_user').values('codename', 'content_type__app_label')
        mem = six.BytesIO()
        export_as_xls(queryset=qs, fields=fields, header=header, out=mem)
        mem.seek(0)
        w = xlrd.open_workbook(file_contents=mem.read())
        sheet = w.sheet_by_index(0)
        self.assertEqual(sheet.cell_value(1, 1), u'add_user')
        self.assertEqual(sheet.cell_value(1, 2), u'auth')

    def test_callable_method(self):
        fields = ['codename', 'natural_key']
        qs = Permission.objects.filter(codename='add_user')
        mem = six.BytesIO()
        export_as_xls(queryset=qs, fields=fields, out=mem)
        mem.seek(0)
        content = mem.read()
        w = xlrd.open_workbook(file_contents=content)
        sheet = w.sheet_by_index(0)
        self.assertEqual(sheet.cell_value(1, 1), u'add_user')
        self.assertEqual(sheet.cell_value(1, 2), u'add_userauthuser')
