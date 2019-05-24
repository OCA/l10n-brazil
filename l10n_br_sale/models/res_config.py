# -*- coding: utf-8 -*-
# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    def _get_default_copy_note(self):
        ir_values = self.env['ir.values']
        comp_id = self.env.user.company_id.id
        return ir_values.get_default('sale.order', 'copy_note',
                                     company_id=comp_id)

    copy_note = fields.Boolean(u'Copiar Observações nos Documentos Fiscais',
                               default=_get_default_copy_note)

    @api.multi
    def set_sale_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'sale.order', 'copy_note', self.copy_note,
            company_id=self.env.user.company_id.id)
