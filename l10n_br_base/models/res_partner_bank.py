# Copyright (C) 2009 Gabriel C. Stabel
# Copyright (C) 2009 Renato Lima (Akretion)
# Copyright (C) 2012 Raphaël Valyi (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class ResPartnerBank(models.Model):
    """ Adiciona campos necessários para o cadastramentos de contas
    bancárias no Brasil."""
    _inherit = 'res.partner.bank'

    acc_number = fields.Char(
        string='Account Number',
        size=64,
        required=False)

    acc_number_dig = fields.Char(
        string='Account Digit',
        size=8)

    bra_number = fields.Char(
        string='Bank Branch',
        size=8)

    bra_number_dig = fields.Char(
        string='Bank Branch Digit',
        size=8)

    bra_bank_bic = fields.Char(
        string='BIC/Swift Final Code.',
        size=3,
        help='Last part of BIC/Swift Code.')
