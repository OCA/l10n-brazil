# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (<http://www.kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import xlwt
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
import logging
_logger = logging.getLogger(__name__)


class StockHistoryXlsParser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(StockHistoryXlsParser, self).__init__(
            cr, uid, name, context=context)
        self.context = context


class StockHistoryXls(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(StockHistoryXls, self).__init__(
            name, table, rml, parser, header, store)

        # Cell Styles
        _xs = self.xls_styles
        # header
        rh_cell_format = _xs['bold'] + _xs['fill'] + \
            _xs['borders_all'] + _xs['right']
        self.rh_cell_style = xlwt.easyxf(rh_cell_format)
        self.rh_cell_style_date = xlwt.easyxf(
            rh_cell_format, num_format_str=report_xls.date_format)
        # lines
        self.mis_rh_cell_style = xlwt.easyxf(
            _xs['borders_all'] + _xs['bold'] + _xs['fill'])

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        report_name = 'Relatório de Valorização de Estoque'
        ws = wb.add_sheet(report_name[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        # Title
        c_specs = [
            ('report_name', 1, 0, 'text', report_name),
        ]
        row_data = self.xls_row_template(c_specs, ['report_name'])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=xlwt.easyxf(_xs['xls_title']))
        row_pos += 1

        active_ids = self.context.get('active_ids')
        wizard_obj = self.pool.get('wizard.valuation.history').browse(
            self.cr, self.uid, active_ids)

        wizard_obj.compute(self.cr, self.uid, objects[0].id, date=wizard_obj.date)
        from pprint import pprint
        pprint(data)
        pass


StockHistoryXls('report.wizard.valuation.history.xls',
                'wizard.valuation.history.xls', parser=StockHistoryXlsParser)
