# © 2012 KMEE INFORMATICA LTDA
#   @author  Luiz Felipe do Divino Costa <luiz.divino@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class L10nBrCNABReturnLot(models.Model):
    """
    The class is used to register the Lots of Events in CNAB return file.
    """

    _name = "l10n_br_cnab.return.lot"
    _description = "CNAB Return Lot"

    lot_event_ids = fields.One2many(
        string="Eventos",
        comodel_name="l10n_br_cnab.return.event",
        inverse_name="lot_id",
    )
    # TODO - deveria ter alguma relação com o objeto cnab.return.log
    #  diretamente ? Já que já existe com no Evento
    # cnab_return_log_id = fields.Many2one(
    #    string='CNAB Return Log', comodel_name='cnab.return.log', ondelete='cascade'
    # )
    account_bank_id = fields.Many2one(
        string="Conta Bancária", comodel_name="res.partner.bank"
    )
    company_registration_number = fields.Char(string="Número de Inscrição")
    company_registration_type = fields.Char(string="Tipo de Inscrição")
    message = fields.Char(string="Mensagem")
    register_qty = fields.Integer(string="Quantidade de Registros")
    operation_service = fields.Char(string="Tipo de Operação")
    service_type = fields.Char(string="Tipo do Serviço")
    total_value = fields.Float(string="Valor Total")
