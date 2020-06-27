# Copyright (C) 2009 Gabriel C. Stabel
# Copyright (C) 2009 Renato Lima (Akretion)
# Copyright (C) 2012 Raphaël Valyi (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError

BANK_ACCOUNT_TYPE = [
    ('01', _('Conta corrente individual')),
    ('02', _('Conta poupança individual')),
    ('03', _('Conta depósito judicial/Depósito em consignação individual')),
    ('11', _('Conta corrente conjunta')),
    ('12', _('Conta poupança conjunta')),
    ('13', _('Conta depósito judicial/Depósito em consignação conjunta')),
]


class ResPartnerBank(models.Model):
    """ Adiciona campos necessários para o cadastramentos de contas
    bancárias no Brasil."""
    _inherit = 'res.partner.bank'

    bank_account_type = fields.Selection(
        selection=BANK_ACCOUNT_TYPE,
        string='Bank Account Type',
        default='01',
    )

    acc_number = fields.Char(
        string='Account Number',
        size=64,
        required=False,
    )

    acc_number_dig = fields.Char(
        string='Account Digit',
        size=8,
    )

    bra_number = fields.Char(
        string='Bank Branch',
        size=8,
    )

    bra_number_dig = fields.Char(
        string='Bank Branch Digit',
        size=8,
    )

    bra_bank_bic = fields.Char(
        string='BIC/Swift Final Code.',
        size=3,
        help="Last part of BIC/Swift Code.",
    )

    @api.multi
    @api.constrains('bra_number')
    def _check_bra_number(self):
        for b in self:
            if b.bank_id.code_bc:
                if len(b.bra_number) > 4:
                    raise UserError(
                        _("Bank branch code must be four caracteres.")
                    )
