# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (<http://www.kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from openerp import models, fields, api
from openerp import tools


class WizardValuationHistory(models.TransientModel):

    _inherit = 'wizard.valuation.history'

    @api.multi
    def compute(self, date):
        ctx = dict(self._context)
        ctx['history_date'] = date

        result = self._model.read_group(
            self._cr, self._uid, domain=[],
            fields=[
                'fiscal_classification_id',
                'product_id',
                'location_id',
                'move_id',
                'company_id',
                'date',
                'source',
                'quantity',
                # 'inventory_value',
                'price_unit_on_quant'
            ],
            groupby=[
                'product_id',
                'location_id',
            ],
            context=ctx)
        return result


class StockHistory(models.Model):
    _inherit = 'stock.history'

    fiscal_classification_id = fields.Many2one(
        comodel_name='account.product.fiscal.classification',
        string='NCM',
        related='product_id.fiscal_classification_id'
    )

#
# class StockHistory(models.Model):
#     _inherit = 'stock.history'
#     # @api.v7
#     # def read_group(self, cr, uid, domain, fields, groupby, offset=0,
#     #                limit=None, context=None, orderby=False, lazy=True):
#     #     res = super(StockHistoryReport, self).read_group(
#     #         cr, uid, domain, fields, groupby, offset=offset, limit=limit,
#     #         context=context, orderby=orderby, lazy=lazy)
#     #     if context is None:
#     #         context = {}
#     #     date = context.get('history_date', datetime.now())
#     #     if 'inventory_value' in fields:
#     #         group_lines = {}
#     #         for line in res:
#     #             domain = line.get('__domain', domain)
#     #             group_lines.setdefault(str(domain), self.search(
#     #                 cr, uid, domain, context=context))
#     #         line_ids = set()
#     #         for ids in group_lines.values():
#     #             for product_id in ids:
#     #                 line_ids.add(product_id)
#     #         line_ids = list(line_ids)
#     #         lines_rec = {}
#     #         if line_ids:
#     #             cr.execute(
#     #                 'SELECT id, product_id, price_unit_on_quant, company_id,'
#     #                 ' quantity, fiscal_classification_id '
#     #                 'FROM stock_history_report'
#     #                 ' WHERE id in %s', (tuple(line_ids),))
#     #             lines_rec = cr.dictfetchall()
#     #         lines_dict = dict((line['id'], line) for line in lines_rec)
#     #         product_ids = list(set(
#     #             line_rec['product_id'] for line_rec in lines_rec))
#     #         products_rec = self.pool['product.product'].read(
#     #             cr, uid, product_ids, ['cost_method', 'product_tmpl_id',
#     #                                    'fiscal_classification_id'],
#     #             context=context)
#     #         products_dict = dict((product['id'], product)
#     #                              for product in products_rec)
#     #         cost_method_product_tmpl_ids = list(
#     #             set(product['product_tmpl_id'][0]
#     #                 for product in products_rec
#     #                 if product['cost_method'] != 'real'))
#     #         histories = []
#     #         if cost_method_product_tmpl_ids:
#     #             cr.execute(
#     #                 'SELECT DISTINCT ON '
#     #                 '(ph.product_template_id, ph.company_id) '
#     #                 'ph.product_template_id, ph.company_id, ph.cost, '
#     #                 'pt.fiscal_classification_id '
#     #                 'FROM product_price_history ph '
#     #                 'INNER JOIN product_template pt ON '
#     #                 'pt.id = ph.product_template_id '
#     #                 'WHERE ph.product_template_id in %s '
#     #                 'AND ph.datetime <= %s ORDER BY ph.product_template_id,'
#     #                 ' ph.company_id, ph.datetime DESC', (
#     #                     tuple(cost_method_product_tmpl_ids), date))
#     #             histories = cr.dictfetchall()
#     #         histories_dict = {}
#     #         for history in histories:
#     #             histories_dict[(history['product_template_id'],
#     #                             history['company_id'])] = history['cost']
#     #         for line in res:
#     #             inv_value = 0.0
#     #             lines = group_lines.get(str(line.get('__domain', domain)))
#     #             for line_id in lines:
#     #                 line_rec = lines_dict[line_id]
#     #                 product = products_dict[line_rec['product_id']]
#     #                 if product['cost_method'] == 'real':
#     #                     price = line_rec['price_unit_on_quant']
#     #                 else:
#     #                     price = histories_dict.get(
#     #                         (product['product_tmpl_id'][0],
#     #                          line_rec['company_id']), 0.0)
#     #                 inv_value += price * line_rec['quantity']
#     #             line['inventory_value'] = inv_value
#     #
#     #     return res
#
#     # @api.depends('product_id.cost_method', 'price_unit_on_quant', 'quantity')
#     # @api.multi
#     # def _get_inventory_value(self):
#     #     if self._context is None:
#     #         context = {}
#     #     date = self._context.get('history_date')
#     #     product_tmpl_obj = self.env["product.template"]
#     #     for line in self:
#     #         if line.product_id.cost_method == 'real':
#     #             line.inventory_value = line.quantity * line.price_unit_on_quant
#     #         else:
#     #             line.inventory_value = (
#     #                 line.quantity * product_tmpl_obj.get_history_price(
#     #                     line.company_id.id, date=date)
#     #             )
#
#     # move_id = fields.Many2one(
#     #     comodel_name='stock.move',
#     #     string='Stock Move',
#     #     required=True)
#     # location_id = fields.Many2one(
#     #     comodel_name='stock.location',
#     #     string='Location',
#     #     required=True)
#     # company_id = fields.Many2one(
#     #     comodel_name='res.company',
#     #     string='Company')
#     # product_id = fields.Many2one(
#     #     comodel_name='product.product',
#     #     string='Product',
#     #     required=True)
#     # product_categ_id = fields.Many2one(
#     #     comodel_name='product.category',
#     #     string='Product Category',
#     #     required=True)
#     # quantity = fields.Float('Product Quantity')
#     # date = fields.Datetime('Operation Date')
#     # price_unit_on_quant = fields.Float('Value')
#     # inventory_value = fields.Float(
#     #     compute='_get_inventory_value',
#     #     string="Inventory Value",
#     #     readonly=True)
#     # source = fields.Char('Source')
#
#     fiscal_classification_id = fields.Many2one(
#         comodel_name='account.product.fiscal.classification',
#         string='NCM',
#         related='product_id.fiscal_classification_id'
#     )
#
#     # def init(self, cr):
#     #     tools.drop_view_if_exists(cr, 'stock_history_report')
#     #     cr.execute("""
#     #         CREATE OR REPLACE VIEW stock_history_report AS (
#     #           SELECT MIN(id) as id,
#     #             move_id,
#     #             location_id,
#     #             company_id,
#     #             product_id,
#     #             product_categ_id,
#     #             fiscal_classification_id,
#     #             SUM(quantity) as quantity,
#     #             date,
#     #             SUM(price_unit_on_quant * quantity) / SUM(quantity) as price_unit_on_quant,
#     #             source
#     #             FROM
#     #             ((SELECT
#     #                 stock_move.id AS id,
#     #                 stock_move.id AS move_id,
#     #                 dest_location.id AS location_id,
#     #                 dest_location.company_id AS company_id,
#     #                 stock_move.product_id AS product_id,
#     #                 product_template.categ_id AS product_categ_id,
#     #                 product_template.fiscal_classification_id as fiscal_classification_id,
#     #                 quant.qty AS quantity,
#     #                 stock_move.date AS date,
#     #                 quant.cost as price_unit_on_quant,
#     #                 stock_move.origin AS source
#     #             FROM
#     #                 stock_move
#     #             JOIN
#     #                 stock_quant_move_rel on stock_quant_move_rel.move_id = stock_move.id
#     #             JOIN
#     #                 stock_quant as quant on stock_quant_move_rel.quant_id = quant.id
#     #             JOIN
#     #                stock_location dest_location ON stock_move.location_dest_id = dest_location.id
#     #             JOIN
#     #                 stock_location source_location ON stock_move.location_id = source_location.id
#     #             JOIN
#     #                 product_product ON product_product.id = stock_move.product_id
#     #             JOIN
#     #                 product_template ON product_template.id = product_product.product_tmpl_id
#     #             WHERE quant.qty>0 AND stock_move.state = 'done' AND dest_location.usage in ('internal', 'transit')
#     #               AND (
#     #                 (source_location.company_id is null and dest_location.company_id is not null) or
#     #                 (source_location.company_id is not null and dest_location.company_id is null) or
#     #                 source_location.company_id != dest_location.company_id or
#     #                 source_location.usage not in ('internal', 'transit'))
#     #             ) UNION ALL
#     #             (SELECT
#     #                 (-1) * stock_move.id AS id,
#     #                 stock_move.id AS move_id,
#     #                 source_location.id AS location_id,
#     #                 source_location.company_id AS company_id,
#     #                 stock_move.product_id AS product_id,
#     #                 product_template.categ_id AS product_categ_id,
#     #                 product_template.fiscal_classification_id as fiscal_classification_id,
#     #                 - quant.qty AS quantity,
#     #                 stock_move.date AS date,
#     #                 quant.cost as price_unit_on_quant,
#     #                 stock_move.origin AS source
#     #             FROM
#     #                 stock_move
#     #             JOIN
#     #                 stock_quant_move_rel on stock_quant_move_rel.move_id = stock_move.id
#     #             JOIN
#     #                 stock_quant as quant on stock_quant_move_rel.quant_id = quant.id
#     #             JOIN
#     #                 stock_location source_location ON stock_move.location_id = source_location.id
#     #             JOIN
#     #                 stock_location dest_location ON stock_move.location_dest_id = dest_location.id
#     #             JOIN
#     #                 product_product ON product_product.id = stock_move.product_id
#     #             JOIN
#     #                 product_template ON product_template.id = product_product.product_tmpl_id
#     #             WHERE quant.qty>0 AND stock_move.state = 'done' AND source_location.usage in ('internal', 'transit')
#     #              AND (
#     #                 (dest_location.company_id is null and source_location.company_id is not null) or
#     #                 (dest_location.company_id is not null and source_location.company_id is null) or
#     #                 dest_location.company_id != source_location.company_id or
#     #                 dest_location.usage not in ('internal', 'transit'))
#     #             ))
#     #             AS foo
#     #             GROUP BY move_id, location_id, company_id, product_id, product_categ_id, fiscal_classification_id, date, source
#     #         )""")
#

