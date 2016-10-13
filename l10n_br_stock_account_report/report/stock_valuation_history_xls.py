# -*- coding: utf-8 -*-
# @ 2016 Kmee - www.kmee.com.br - Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import _render
from openerp.exceptions import Warning as UserError
from openerp.tools.translate import _

try:
    import xlwt
except ImportError:
    raise UserError(_(u'Erro!'), _(u"Biblioteca xlwt não instalada!"))

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
        self.rh_cell_style_center = xlwt.easyxf(rh_cell_format + _xs['center'])
        self.rh_cell_style_right = xlwt.easyxf(rh_cell_format + _xs['right'])
        self.rh_cell_style_date = xlwt.easyxf(
            rh_cell_format, num_format_str=report_xls.date_format)
        # lines
        line_cell_format = _xs['borders_all']
        self.line_cell_style_decimal = xlwt.easyxf(
            line_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)
        self.line_cell_style = xlwt.easyxf(line_cell_format)

        self.col_specs_template = {
            'fiscal_classification_id': {
                'header': [1, 10, 'text', _render("('NCM')")],
                'lines': [1, 0, 'text',
                          _render("line.get('fiscal_classification_id', '')")],
                'totals': [1, 0, 'text', None]},
            'product_id': {
                'header': [1, 50, 'text', _render("('Produto')")],
                'lines': [1, 0, 'text',
                          _render("line.get('product_id', False) and "
                                  "line.get('product_id')[1] or ''")],
                'totals': [1, 0, 'text', None]},
            'price_unit_on_quant': {
                'header': [1, 25, 'text',
                           _render("('Preço de custo no periodo')")],
                'lines': [1, 0, 'number',
                          _render("line.get('price_unit_on_quant')"),
                          None, self.line_cell_style_decimal],
                'totals': [1, 0, 'text', None]},
            'quantity': {
                'header': [1, 15, 'text', _render("('Quantidade')")],
                'lines': [1, 0, 'number', _render("line.get('quantity', 0)")],
                'totals': [1, 0, 'text', None]},
            'inventory_value': {
                'header': [1, 15, 'text', _render("('Valor Total')")],
                'lines': [1, 0, 'number',
                          _render("line.get('inventory_value', 0)"),
                          None, self.line_cell_style_decimal],
                'totals': [1, 0, 'text', None]},
        }

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

        # Column headers
        c_specs = map(lambda x: self.render(
            x, self.col_specs_template, 'header'),
            [
                'product_id',
                'fiscal_classification_id',
                # 'product_id_count',
                'quantity',
                'price_unit_on_quant',
                'inventory_value'
            ])
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=self.rh_cell_style_center,
            set_column_size=True)
        ws.set_horz_split_pos(row_pos)

        # Lines
        active_ids = self.context.get('active_ids')
        wizard_obj = self.pool.get('wizard.valuation.history').browse(
            self.cr, self.uid, active_ids)
        data = wizard_obj.compute(
            self.cr, self.uid, objects[0].id, date=wizard_obj.date,
            context=self.context)
        for line in data:
            c_specs = map(
                lambda x: self.render(
                    x, self.col_specs_template, 'lines'), [
                    'product_id',
                    'fiscal_classification_id',
                    'quantity',
                    'price_unit_on_quant',
                    'inventory_value'
                ])
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, row_style=self.line_cell_style)
        pass


StockHistoryXls('report.wizard.valuation.history',
                'wizard.valuation.history', parser=StockHistoryXlsParser)
