# -*- encoding: utf-8 -*-

from openerp import models, fields, api
from ..models import l10n_br_fci


class ProductFciFromProductTemplateLines(models.TransientModel):
    _name = "product_fci.from.product.template.lines"
    _description = "Produtos FCI"

    products_ids = fields.Many2many('product.template', 'product_id', 'line_id',
                                    'product_line_rel')

    @api.multi
    def populate_l10n_br_fci(self):

        #assert para verificar se essa execução é executada uma de cada vez.
        for wizard in self:
            active_id = wizard._context.get('active_id')
            for product in self.products_ids:
                vals = {}
                vals = {
                    'product_id' : product.id,
                    'product_uom': product.uom_id.id,
                    'l10n_br_fci_id': active_id,
                }
                fci_line_obj = self.env['l10n_br.fci.line']
                fci_line_obj.create(vals)
        return True
