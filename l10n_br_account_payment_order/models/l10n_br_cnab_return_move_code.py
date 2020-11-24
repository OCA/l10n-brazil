# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class L10nBrCNABReturnMoveCode(models.Model):
    _name = 'l10n_br_cnab.return.move.code'
    _inherit = 'l10n_br_cnab.data.abstract'
    _description = 'CNAB Return Move Code'

    bank_ids = fields.Many2many(
        string='Bank',
        comodel_name='res.bank',
        relation='l10n_br_cnab_return_move_code_bank_rel',
        column1='bank_id',
        column2='l10n_br_cnab_return_move_code_id',
        track_visibility='always',
    )

    payment_method_ids = fields.Many2many(
        comodel_name='account.payment.method',
        string='Payment Method',
        relation='l10n_br_cnab_return_move_code_payment_method_rel',
        column1='payment_method_id',
        column2='l10n_br_cnab_mov_instruction_code_id',
        track_visibility='always',
    )
