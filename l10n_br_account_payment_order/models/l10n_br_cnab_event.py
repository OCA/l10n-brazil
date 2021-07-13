# © 2012 KMEE INFORMATICA LTDA
#   @author  Luiz Felipe do Divino Costa <luiz.divino@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class L10nBrCNABReturnEvent(models.Model):
    """
    The class is used to register the Events of CNAB return file.
    """

    _name = "l10n_br_cnab.return.event"
    _description = "CNAB Return Event"

    cnab_return_log_id = fields.Many2one(
        string="CNAB Return Log",
        comodel_name="l10n_br_cnab.return.log",
    )
    # Field used to make invisible/visible fields refer to Lot
    is_cnab_lot = fields.Boolean(string="Is CNAB Lot?")
    # O arquivo de Retorno pode ter ou não Lotes
    lot_id = fields.Many2one(
        string="Lote", comodel_name="l10n_br_cnab.return.lot", ondelete="cascade"
    )
    bank_payment_line_id = fields.Many2one(
        string="Bank Payment Line", comodel_name="bank.payment.line"
    )
    real_payment_date = fields.Date(string="Data do Crédito")
    occurrence_date = fields.Date(string="Data da Ocorrência")
    due_date = fields.Date(string="Data de Vencimento")
    favored_bank_account_id = fields.Many2one(
        string="Conta Bancária", comodel_name="res.partner.bank"
    )
    favored_id = fields.Many2one(string="Favorecido", comodel_name="res.partner")
    company_title_identification = fields.Char(
        string="Identificação do Título da Empresa", required=False
    )
    invoice_id = fields.Many2one(comodel_name="account.invoice", string="Fatura")
    interest_fee_value = fields.Float(string="Juros de Mora/Multa")
    own_number = fields.Char(string="Nosso Número")
    occurrences = fields.Char(string="Ocorrências")
    other_credits = fields.Float(string="Outros Créditos")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Associado")
    segment = fields.Char(string="Segmento")
    your_number = fields.Char(string="Seu Número")
    str_motiv_a = fields.Char("Motivo da ocorrência 01")
    str_motiv_b = fields.Char("Motivo de ocorrência 02")
    str_motiv_c = fields.Char("Motivo de ocorrência 03")
    str_motiv_d = fields.Char("Motivo de ocorrência 04")
    str_motiv_e = fields.Char("Motivo de ocorrência 05")
    currency_type = fields.Char(string="Tipo de Moeda")
    tariff_charge = fields.Float(string="Tarifa")
    title_value = fields.Float(string="Valor da Linha")
    rebate_value = fields.Float(
        string="Valor do Abatimento",
        help="""Se o desconto ou abatimento é concedido na entrada do boleto
        estes campos são retornados zerados(apesar de corretamente registrados
        no Itaú). Se concedidos após a entrada, retornam com os valores
        do desconto ou abatimento.
        Na liquidação, desconto e abatimento retornam somados no campo
        desconto; opcionalmente, mediante cadastro prévio em nosso sistema,
        estes valores poderão retornar separados, conforme mostra o
        indicador 36.4 do Item 5 - Condições Personalizadas.""",
    )
    discount_value = fields.Float(
        string="Valor do Desconto",
        help="""Se o desconto ou abatimento é concedido na entrada do boleto
        estes campos são retornados zerados(apesar de corretamente registrados
        no Itaú). Se concedidos após a entrada, retornam com os valores
        do desconto ou abatimento.
        Na liquidação, desconto e abatimento retornam somados no campo
        desconto; opcionalmente, mediante cadastro prévio em nosso sistema,
        estes valores poderão retornar separados, conforme mostra o
        indicador 36.4 do Item 5 - Condições Personalizadas.""",
    )
    iof_value = fields.Float(string="Valor do IOF")
    payment_value = fields.Float(string="Valor do Pagamento")
    move_line_id = fields.Many2one(
        comodel_name="account.move.line", string="Journal Item", ondelete="restrict"
    )
