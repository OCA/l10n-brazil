# -*- coding: utf-8 -*-
# @ 2016 Kmee - www.kmee.com.br - Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, _
from openerp.osv import osv, fields


class WizardValuationHistory(models.TransientModel):
    _inherit = 'wizard.valuation.history'

    '''TODO - We need to use the old API because the Context is not being
     pass to the method read_group( ORM ), the reason seems because this
      method still not migrated to new API.'''
    @api.model
    def compute(self, cr, uid, ids, date, context=None):

        context['history_date'] = date

        fields = [
            'fiscal_classification_id',
            'product_id',
            'location_id',
            'move_id',
            'company_id',
            'date',
            'source',
            'quantity',
            'inventory_value',
            'price_unit_on_quant'
        ]
        group_by = [
            'product_id',
            'location_id',
            'fiscal_classification_id'
        ]

        result = self.pool.get('stock.history').read_group(
            cr, uid, domain=[['date', '<=', date]], fields=fields,
            groupby=group_by, context=context)

        return result

    @api.multi
    def open_report_xls(self):

        data = self.read()[0]
        ctx = self.env.context.copy()
        ctx['history_date'] = data['date']
        ctx['search_default_group_by_product'] = True
        ctx['search_default_group_by_location'] = True

        return {
            'domain': "[('date', '<=', '" + data['date'] + "')]",
            'name': _('Stock Value At Date'),
            'type': 'ir.actions.report.xml',
            'report_name': 'wizard.valuation.history',
            'datas': data,
            'context': ctx,
            'nodestroy': True
        }


class StockHistory(osv.osv):

    _inherit = 'stock.history'

    _columns = {
        'fiscal_classification_id': fields.related(
            'product_id', 'fiscal_classification_id', type='many2one',
            relation='account.product.fiscal.classification', string='NCM'
        )
    }

    def read_group(self, cr, uid, domain, fields, groupby, offset=0,
                   limit=None, context=None, orderby=False, lazy=True):
        res = super(StockHistory, self).read_group(
            cr, uid, domain, fields, groupby, offset=offset, limit=limit,
            context=context, orderby=orderby, lazy=lazy)

        if 'fiscal_classification_id' in fields:
            product_obj = self.pool.get('product.product')
            for line in res:
                product = product_obj.browse(cr, uid, line['product_id'][0])
                fiscal_class = product.fiscal_classification_id.code
                line.update({'fiscal_classification_id': fiscal_class})
        return res
