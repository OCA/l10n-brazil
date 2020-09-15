# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import models, api, fields, _


class CNABReturnLog(models.Model):
    """
        The class is used to register the LOG of CNAB return file
        because there is the possibility that imported file don't
        generate account.move .
    """
    _name = 'cnab.return.log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'CNAB Return Log'

    name = fields.Char(string='Name')
    filename = fields.Char(string='Nome do Arquivo')
    number_events = fields.Integer(string='Número de Eventos')
    number_lots = fields.Integer(string='Número de Lotes')
    cnab_date = fields.Date(
        string='Data CNAB', required=True, default=datetime.now().date())
    bank_account_id = fields.Many2one(
        string='Conta cedente', comodel_name='res.partner.bank'
    )
    # TODO - validar o campo a partir do primeiro arquivo incluido
    #  para evitar de 'pular' a sequencia ?
    sequential_file = fields.Char(string='Sequencial do Arquivo')

    cnab_return_log_line_ids = fields.One2many(
        string='Eventos', comodel_name='cnab.return.log.line',
        inverse_name='cnab_return_log_id'
    )
    amount_total_title = fields.Float(string='Valor Total Títulos')
    amount_total_received = fields.Float(string='Valor Total Recebido')
    # The LOG can have or not Journal Entry
    move_id = fields.Many2one(
        string='Journal Entry', comodel_name='account.move'
    )


class CNABReturnLogLine(models.Model):
    _name = 'cnab.return.log.line'
    _description = 'CNAB Return Log Line'

    bank_payment_line_id = fields.Many2one(
        string='Bank Payment Line', comodel_name='bank.payment.line'
    )
    real_payment_date = fields.Date(string='Data do Crédito')
    occurrence_date = fields.Date(string='Data da Ocorrência')
    due_date = fields.Date(string='Data de Vencimento')
    favored_bank_account_id = fields.Many2one(
        string='Conta Bancária', comodel_name='res.partner.bank'
    )
    favored_id = fields.Many2one(string='Favorecido', comodel_name='res.partner')
    company_title_identification = fields.Char(
        string='Identificação do Título da Empresa', required=False
    )
    invoice_id = fields.Many2one(comodel_name='account.invoice', string='Fatura')
    interest_fee_value = fields.Float(string='Juros de Mora/Multa')

    # TODO - Não vi necessidade de ter um objeto para registrar o LOTE,
    #  Apenas um campo informando de qual lote se trata não seria
    #  o suficiente ?
    # lot_id = fields.Many2one(
    #    string='Lote', comodel_name='l10n_br.cnab.lote', ondelete='cascade'
    # )
    cnab_lot = fields.Char(string='Lote')
    cnab_return_log_id = fields.Many2one(
        string='CNAB Return Log', comodel_name='cnab.return.log',
        inverse_name='cnab_return_log_ids'
    )
    own_number = fields.Char(string='Nosso Número')
    occurrences = fields.Char(string='Ocorrências')
    other_credits = fields.Float(string='Outros Créditos')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Associado')
    segment = fields.Char(string='Segmento')
    your_number = fields.Char(string='Seu Número')
    str_motiv_a = fields.Char('Motivo da ocorrência 01')
    str_motiv_b = fields.Char('Motivo de ocorrência 02')
    str_motiv_c = fields.Char('Motivo de ocorrência 03')
    str_motiv_d = fields.Char('Motivo de ocorrência 04')
    str_motiv_e = fields.Char('Motivo de ocorrência 05')
    currency_type = fields.Char(string='Tipo de Moeda')
    tariff_charge = fields.Float(string='Tarifa')
    title_value = fields.Float(string='Valor da Linha')
    rebate_value = fields.Float(
        string='Valor do Abatimento',
        help='''Se o desconto ou abatimento é concedido na entrada do boleto
        estes campos são retornados zerados(apesar de corretamente registrados
        no Itaú). Se concedidos após a entrada, retornam com os valores
        do desconto ou abatimento.
        Na liquidação, desconto e abatimento retornam somados no campo
        desconto; opcionalmente, mediante cadastro prévio em nosso sistema,
        estes valores poderão retornar separados, conforme mostra o
        indicador 36.4 do Item 5 - Condições Personalizadas.''',
    )
    discount_value = fields.Float(
        string='Valor do Desconto',
        help='''Se o desconto ou abatimento é concedido na entrada do boleto
        estes campos são retornados zerados(apesar de corretamente registrados
        no Itaú). Se concedidos após a entrada, retornam com os valores
        do desconto ou abatimento.
        Na liquidação, desconto e abatimento retornam somados no campo
        desconto; opcionalmente, mediante cadastro prévio em nosso sistema,
        estes valores poderão retornar separados, conforme mostra o
        indicador 36.4 do Item 5 - Condições Personalizadas.''',
    )
    iof_value = fields.Float(string='Valor do IOF')
    payment_value = fields.Float(string='Valor do Pagamento')
