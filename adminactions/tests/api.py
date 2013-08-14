# -*- encoding: utf-8 -*-
import unittest
import xlrd
from adminactions.api import export_as_csv, export_as_xls
import StringIO
from collections import namedtuple

#ӼӳӬԖԊ
class TestExportAsCsv(unittest.TestCase):
    def test_export_as_csv(self):
        fields = ['field1', 'field2']
        header = ['Field 1', 'Field 2']
        Row = namedtuple('Row', fields)
        rows = [Row(1, 4),
                Row(2, 5),
                Row(3, u'ӼӳӬԖԊ')]
        mem = StringIO.StringIO()
        export_as_csv(queryset=rows, fields=fields, header=header, out=mem)
        mem.seek(0)
        csv_dump = mem.read()
        self.assertEquals(csv_dump.decode('utf8'), u'"Field 1";"Field 2"\r\n"1";"4"\r\n"2";"5"\r\n"3";"ӼӳӬԖԊ"\r\n')


class TestExportAsExcel(unittest.TestCase):
    def test_export_as_xls(self):
        fields = ['field1', 'field2']
        header = ['Field 1', 'Field 2']
        Row = namedtuple('Row', fields)
        rows = [Row(111, 222),
                Row(333, 444),
                Row(555, u'ӼӳӬԖԊ')]
        mem = StringIO.StringIO()
        export_as_xls(queryset=rows, fields=fields, header=header, out=mem)
        mem.seek(0)
        xls_workbook = xlrd.open_workbook(file_contents=mem.read())
        xls_sheet = xls_workbook.sheet_by_index(0)
        self.assertEqual(xls_sheet.row_values(0)[:], ['#', 'Field 1', 'Field 2'])
        self.assertEqual(xls_sheet.row_values(1)[:], [1.0, 111.0, 222.0])
        self.assertEqual(xls_sheet.row_values(2)[:], [2.0, 333.0, 444.0])
        self.assertEqual(xls_sheet.row_values(3)[:], [3.0, 555.0, u'ӼӳӬԖԊ'])
