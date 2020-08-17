# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class DocumentLineMixin(models.AbstractModel):
    _name = 'l10n_br_account.document.line.mixin'
    _description = 'Account Document Line Mixin'

    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Fiscal Position',
    )

    @api.onchange('product_id')
    def _onchange_product_id_account(self):
        if self.fiscal_operation_id:
            if self.fiscal_operation_id.fiscal_position_id:
                self.fiscal_position_id = (
                    self.fiscal_operation_id.fiscal_position_id)
