# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class CNABReturnLog(models.Model):
    """
        The class is used to register the LOG of CNAB return file.
    """
    _name = 'cnab.return.log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'CNAB Return Log'

    name = fields.Char(string='Name')
    filename = fields.Char(string='Nome do Arquivo')
    number_events = fields.Integer(string='Número de Eventos')
    number_lots = fields.Integer(string='Número de Lotes')
    cnab_date_import = fields.Datetime(string='CNAB Date Import')
    bank_account_id = fields.Many2one(
        string='Conta cedente', comodel_name='res.partner.bank'
    )
    # TODO - validar o campo a partir do primeiro arquivo incluido
    #  para evitar de 'pular' a sequencia ?
    #  O BRCobranca ignora a linha do header
    sequential_file = fields.Char(string='Sequencial do Arquivo')
    cnab_date_file = fields.Date(string='CNAB Date File')

    event_ids = fields.One2many(
        string='Eventos', comodel_name='cnab.return.event',
        inverse_name='cnab_return_log_id'
    )
    amount_total_title = fields.Float(string='Valor Total Títulos')
    amount_total_received = fields.Float(string='Valor Total Recebido')
    # Field used to make invisible/visible fields refer to Lot
    is_cnab_lot = fields.Boolean(string='Is CNAB Lot?')
    # The LOG can have or not Journal Entry
    move_id = fields.Many2one(
        string='Journal Entry', comodel_name='account.move'
    )
