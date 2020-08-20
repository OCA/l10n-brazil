# © 2012 KMEE INFORMATICA LTDA
#   @author  Luiz Felipe do Divino Costa <luiz.divino@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import fields, models

from ..constants import STATE_CNAB

_logger = logging.getLogger(__name__)


class L10nBrCnabLote(models.Model):
    _name = 'l10n_br.cnab.lote'
    _description = 'l10n_br CNAB Lot'

    account_bank_id = fields.Many2one(
        string='Conta Bancária', comodel_name='res.partner.bank'
    )
    cnab_id = fields.Many2one(
        string='CNAB', comodel_name='l10n_br.cnab', ondelete='cascade'
    )
    company_registration_number = fields.Char(string='Número de Inscrição')
    company_registration_type = fields.Char(string='Tipo de Inscrição')
    event_id = fields.One2many(
        string='Eventos', comodel_name='l10n_br.cnab.evento', inverse_name='lot_id'
    )
    message = fields.Char(string='Mensagem')
    register_qty = fields.Integer(string='Quantidade de Registros')
    operation_service = fields.Char(string='Tipo de Operação')
    state = fields.Selection(
        string='State', related='cnab_id.state', selection=STATE_CNAB, default='draft'
    )
    service_type = fields.Char(string='Tipo do Serviço')
    total_value = fields.Float(string='Valor Total')
