# Copyright 2021 - TODAY, Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

import odoo.addons.decimal_precision as dp


class RepairLineMixin(models.AbstractModel):
    _name = 'l10n_br_repair.repair.line.mixin'
    _inherit = ['l10n_br_repair.repair.line.mixin.methods','l10n_br_fiscal.document.line.mixin']
    _description = 'Repair Line and Fee Mixin'

    @api.model
    def _default_fiscal_operation(self):
        return self.env.user.company_id.repair_fiscal_operation_id

    fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain())

    price_gross = fields.Monetary(
        compute='_compute_price_subtotal',
        string='Gross Amount',
        default=0.00,
    )

    price_tax = fields.Monetary(
        compute='_compute_price_subtotal',
        string='Price Tax',
        default=0.00,
    )

    price_total = fields.Monetary(
        compute='_compute_price_subtotal',
        string='Price Total',
        default=0.00,
    )

    discount = fields.Float(
        string='Discount (%)',
    )

    price_subtotal = fields.Float(
        'Subtotal',
        compute='_compute_price_subtotal',
        digits=dp.get_precision('Account'))
