# -*- encoding: utf-8 -*-

from openerp import models, fields, api
# from .models import l10n_br_fci


class ProductFciFromProductTemplateLines(models.TransientModel):
    _name = "product_fci.from.product.template.lines"
    _description = "Produtos FCI"

    products_ids = fields.Many2many('product.template','product_fci_rel', 'product_ids','product_id')

    @api.multi
    def populate_l10n_br_fci(self):

        print self

        product_line_obj_vals= {
                'default_code': self.products_ids.default_code,
                'name': self.products_ids.name,
                'ean13': self.products_ids.ean13,
                'list_price':self.products_ids.list_price,
                'uom_id': self.products_ids.uom_id,
                'ncm_id': self.products_ids.ncm_id,
                'fci':self.products_ids.fci
            }
        # l10n_br_fci.

        self.env['l10n_br.fci.line'].create(product_line_obj_vals)


        return {'type': 'ir.actions.act_window_close'}
