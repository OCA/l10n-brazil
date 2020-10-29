# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons.spec_driven_model.models import spec_models


class FiscalPayment(spec_models.StackedModel):
    _name = "l10n_br_fiscal.payment"
    _inherit = [_name, 'nfe.40.detpag']
    _stacked = 'nfe.40.dup'
    _spec_module = 'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe'
    _stack_skip = 'nfe40_detPag_pag_id'

    nfe40_indPag = fields.Selection(
        compute='_compute_nfe40_indPag',
    )
    nfe40_tPag = fields.Selection(
        related='payment_mode',
    )
    nfe40_vPag = fields.Monetary(
        related='amount',
    )

    nfe40_tpIntegra = fields.Selection(
        related='integracao_cartao',
    )
    nfe40_CNPJ = fields.Char(
        related='partner_card_cnpj_cpf',
    )
    nfe40_tBand = fields.Selection(
        related='bandeira_cartao',
    )
    nfe40_cAut = fields.Char(
        related='autorizacao',
    )

    company_id = fields.Many2one(
        default=lambda self: self.env.user.company_id,
    )
    currency_id = fields.Many2one(
        default=lambda self: self.env.user.company_id.currency_id,
    )

    @api.depends('payment_term_id')
    def _compute_nfe40_indPag(self):
        for record in self:
            if record.payment_term_id == self.env.ref(
                    'l10n_br_fiscal.term_a_vista'):
                record.nfe40_indPag = '0'
            else:
                record.nfe40_indPag = '1'
