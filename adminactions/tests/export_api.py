# -*- encoding: utf-8 -*-
import unittest
import xlrd
from adminactions.api import export_as_csv, export_as_xls
import StringIO
from collections import namedtuple


class ExportAsCsv(unittest.TestCase):

    def test_export_as_csv(self):
        fields = ['field1', 'field2']
        header = ['Field 1', 'Field 2']
        Row = namedtuple('Row', fields)
        rows = [Row(1, 4),
                Row(2, 5),
                Row(3, u'ӼӳӬԖԊ')]
        mem = StringIO.StringIO()
        export_as_csv(queryset=rows, fields=fields, header=True, header_alt=header, dialect='excel', out=mem)
        mem.seek(0)
        csv_dump = mem.read()
        self.assertEquals(csv_dump.decode('utf8'), u'Field 1,Field 2\r\n1,4\r\n2,5\r\n3,ӼӳӬԖԊ\r\n')


class ExportAsExcel(unittest.TestCase):

    def test_export_as_xls(self):
        fields = ['field1', 'field2']
        header = ['Field 1', 'Field 2']
        Row = namedtuple('Row', fields)
        rows = [Row(1, 4),
                Row(2, 5),
                Row(3, u'ӼӳӬԖԊ')]
        mem = StringIO.StringIO()
        export_as_xls(queryset=rows, fields=fields, header=True, header_alt=header, out=mem)
        mem.seek(0)
        xls_workbook = xlrd.open_workbook(file_contents=mem.read())
        xls_sheet = xls_workbook.sheet_by_index(0)
        self.assertEqual(xls_sheet.row_values(0)[:], ['Field 1', 'Field 2'])
        self.assertEqual(xls_sheet.row_values(1)[:], ['1', '4'])
        self.assertEqual(xls_sheet.row_values(2)[:], ['2', '5'])
        self.assertEqual(xls_sheet.row_values(3)[:], ['3', u'ӼӳӬԖԊ'])
