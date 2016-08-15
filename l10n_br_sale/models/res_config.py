# -*- coding: utf-8 -*-
# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import SUPERUSER_ID
from openerp import models, fields


class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    def _get_default_copy_note(self):
        ir_values = self.env['ir.values']
        comp_id = self.env.user.company_id.id
        return ir_values.get_default('sale.order', 'copy_note',
                                     company_id=comp_id)

    copy_note = fields.Boolean(u'Copiar Observações nos Documentos Fiscais',
                               default=_get_default_copy_note)

    def set_sale_defaults(self, cr, uid, ids, context=None):
        result = super(SaleConfiguration, self).set_sale_defaults(
            cr, uid, ids, context)
        wizard = self.browse(cr, uid, ids, context)[0]
        ir_values = self.pool.get('ir.values')
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        ir_values.set_default(cr, SUPERUSER_ID, 'sale.order', 'copy_note',
                              wizard.copy_note, company_id=user.company_id.id)
        return result
