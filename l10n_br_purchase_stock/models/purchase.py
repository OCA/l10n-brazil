# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _prepare_picking(self):
        values = super(PurchaseOrder, self)._prepare_picking()
        values.update({
            'operation_id': self.operation_id.id,
        })
        return values
