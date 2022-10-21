# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nBrCNABReturnLog(models.Model):
    """
    The class is used to register the LOG of CNAB return file.
    """

    _name = "l10n_br_cnab.return.log"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "CNAB Return Log"

    name = fields.Char()
    filename = fields.Char(string="Nome do Arquivo")
    number_events = fields.Integer(string="Número de Eventos")
    number_lots = fields.Integer(string="Número de Lotes")
    cnab_date_import = fields.Datetime(string="CNAB Date Import")
    bank_account_id = fields.Many2one(
        string="Conta cedente", comodel_name="res.partner.bank"
    )
    # TODO - validar o campo a partir do primeiro arquivo incluido
    #  para evitar de 'pular' a sequencia ?
    #  O BRCobranca ignora a linha do header
    sequential_file = fields.Char(string="Sequencial do Arquivo")
    cnab_date_file = fields.Date(string="CNAB Date File")

    event_ids = fields.One2many(
        string="Eventos",
        comodel_name="l10n_br_cnab.return.event",
        inverse_name="cnab_return_log_id",
    )
    amount_total_title = fields.Float(string="Valor Total Títulos")
    amount_total_received = fields.Float(string="Valor Total Recebido")
    amount_total_tariff_charge = fields.Float(string="Valor Total de Tarifas")
    amount_total_rebate = fields.Float(string="Valor Total de Abatimentos")
    amount_total_discount = fields.Float(string="Valor Total de Descontos")
    amount_total_interest_fee = fields.Float(string="Valor Total de Juros Mora/Multa")
    # Field used to make invisible/visible fields refer to Lot
    is_cnab_lot = fields.Boolean(string="Is CNAB Lot?")
    # The LOG can have or not Journal Entry
    move_ids = fields.Many2many(
        comodel_name="account.move",
        relation="l10n_br_cnab_return_log_move_rel",
        column1="l10n_br_cnab_return_log_id",
        column2="move_id",
        string="Journal Entries",
    )
