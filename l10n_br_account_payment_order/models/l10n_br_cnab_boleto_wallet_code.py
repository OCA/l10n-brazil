# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class L10nBrCNABBoletoWalletCode(models.Model):
    _name = "l10n_br_cnab.boleto.wallet.code"
    _inherit = ["l10n_br_cnab.data.abstract", "mail.thread"]
    _description = "CNAB Boleto Wallet Code"

    bank_ids = fields.Many2many(
        string="Banks",
        comodel_name="res.bank",
        relation="l10n_br_cnab_boleto_wallet_code_bank_rel",
        column1="bank_id",
        column2="l10n_br_cnab_boleto_wallet_code_id",
        tracking=True,
    )

    payment_method_ids = fields.Many2many(
        comodel_name="account.payment.method",
        string="Payment Methods",
        relation="l10n_br_cnab_boleto_wallet_code_payment_method_rel",
        column1="payment_method_id",
        column2="l10n_br_cnab_boleto_wallet_code_id",
        tracking=True,
    )

    comment = fields.Text()

    # TODO: Forma encontrada para pode fazer o Group By, na v15
    #  parece já ser possivel usar campos many2many.
    #  Também deve ser considerado em apagar o campo many2many e deixar
    #  apenas o many2one já que, por enquanto, não há bancos diferentes
    #  usando o mesmo conjunto de codigos apenas diferentes cnab( 240/400 )
    bank_id = fields.Many2one(
        comodel_name="res.bank", compute="_compute_bank_id", store=True
    )  # it is possible to search only among stored fields

    payment_method_id = fields.Many2one(
        comodel_name="account.payment.method",
        compute="_compute_payment_method_id",
        store=True,
    )  # it is possible to search only among stored fields

    @api.depends("bank_ids")
    def _compute_bank_id(self):
        for record in self:
            record.bank_id = record.bank_ids and record.bank_ids[0] or False

    @api.depends("payment_method_ids")
    def _compute_payment_method_id(self):
        for record in self:
            record.payment_method_id = (
                record.payment_method_ids and record.payment_method_ids[0] or False
            )
