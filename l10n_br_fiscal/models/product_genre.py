# Copyright (C) 2019 Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class ProductGenre(models.Model):
    _name = 'l10n_br_fiscal.product.genre'
    _inherit = 'l10n_br_fiscal.data.abstract'
    _description = 'Fiscal Product Genre'

    product_tmpl_ids = fields.One2many(
        comodel_name='product.template',
        inverse_name='fiscal_genre_id',
        string='Products')

    product_tmpl_qty = fields.Integer(
        string='Products Related',
        compute='_compute_product_tmpl_info')

    @api.multi
    @api.depends('product_tmpl_ids')
    def _compute_product_tmpl_info(self):
        for record in self:
            product_tmpls = record.env['product.template'].search([
                ('fiscal_genre_id', '=', record.id),
                '|',
                ('active', '=', False),
                ('active', '=', True)
            ])

            record.product_tmpl_qty = len(product_tmpls)

    def action_view_product(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Products',
            'res_model': 'product.template',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('fiscal_genre_id', '=', self.id)]
        }
