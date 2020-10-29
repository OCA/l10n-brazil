# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api
from odoo.addons.spec_driven_model.models import spec_models


class FiscalPaymentLine(spec_models.StackedModel):
    _name = 'l10n_br_fiscal.payment.line'
    _inherit = [_name, 'nfe.40.dup']
    _stacked = 'nfe.40.dup'
    _spec_module = 'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe'
    _stack_skip = 'nfe40_dup_cobr_id'

    nfe40_nDup = fields.Char(
        related='communication',
    )
    nfe40_dVenc = fields.Date(
        related='date_maturity',
    )
    nfe40_vDup = fields.Monetary(
        related='amount',
    )

    company_id = fields.Many2one(
        default=lambda self: self.env.user.company_id,
    )
    currency_id = fields.Many2one(
        default=lambda self: self.env.user.company_id.currency_id,
    )
