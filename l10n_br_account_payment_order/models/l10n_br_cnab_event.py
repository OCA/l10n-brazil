# © 2012 KMEE INFORMATICA LTDA
#   @author  Luiz Felipe do Divino Costa <luiz.divino@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

_SPLIT_PAYMENT_HELP = (
    "Dado do Split Payment do IBS/CBS devolvido pelo Banco nos registros "
    "opcionais Segmento X-03 e X-04 do Retorno de Cobrança (Layout Padrão "
    "Febraban 240 posições V11.0), veja "
    "https://github.com/OCA/l10n-brazil/issues/5146 ."
)


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
    payment_line_ids = fields.Many2many(
        comodel_name="account.payment.line",
        relation="l10n_br_cnab_log_event_payment_lines_rel",
        column1="cnab_log_event_payment_line_id",
        column2="payment_line_id",
        string="Payment lines",
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
    invoice_id = fields.Many2one(comodel_name="account.move", string="Fatura")
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

    # Dados do Split Payment do IBS/CBS (LC 214/2025) devolvidos pelo Banco nos
    # registros opcionais Segmento X-03 (dados fiscais e valores de CBS/IBS) e
    # Segmento X-04 (valores da liquidação do boleto) do Retorno de Cobrança do
    # Layout Padrão Febraban 240 posições V11.0 (11/09/2026), veja
    # https://github.com/OCA/l10n-brazil/issues/5146
    split_payment_document_key = fields.Char(
        string="Chave do Documento Fiscal (Split Payment)",
        help=_SPLIT_PAYMENT_HELP + " Campo X101.",
    )
    split_payment_identifier = fields.Char(
        string="ID Split (Split Payment)",
        help=_SPLIT_PAYMENT_HELP + " Campo X112.",
    )
    split_payment_identifier_type = fields.Char(
        string="Tipo do ID Split (Split Payment)",
        help=_SPLIT_PAYMENT_HELP + " Campo X113.",
    )
    split_payment_cbs_informed = fields.Float(
        string="CBS Informado (Split Payment)",
        help=_SPLIT_PAYMENT_HELP + " Campo X102.",
    )
    split_payment_ibs_informed = fields.Float(
        string="IBS Informado (Split Payment)",
        help=_SPLIT_PAYMENT_HELP + " Campo X103.",
    )
    split_payment_cbs_corrected = fields.Float(
        string="CBS Corrigido (Split Payment)",
        help=_SPLIT_PAYMENT_HELP + " Campo X104.",
    )
    split_payment_ibs_corrected = fields.Float(
        string="IBS Corrigido (Split Payment)",
        help=_SPLIT_PAYMENT_HELP + " Campo X105.",
    )
    split_payment_cbs_open = fields.Float(
        string="CBS em Aberto (Split Payment)",
        help=_SPLIT_PAYMENT_HELP + " Campo X106.",
    )
    split_payment_ibs_open = fields.Float(
        string="IBS em Aberto (Split Payment)",
        help=_SPLIT_PAYMENT_HELP + " Campo X107.",
    )
    split_payment_cbs_segregated = fields.Float(
        string="CBS Segregado (Split Payment)",
        help=_SPLIT_PAYMENT_HELP + " Campo X108.",
    )
    split_payment_ibs_segregated = fields.Float(
        string="IBS Segregado (Split Payment)",
        help=_SPLIT_PAYMENT_HELP + " Campo X109.",
    )
    split_payment_absent_value = fields.Float(
        string="Valor Pago Ausente de CBS/IBS (Split Payment)",
        help=_SPLIT_PAYMENT_HELP + " Campo X115, do Segmento X-04.",
    )
    split_payment_transferred_value = fields.Float(
        string="Valor Repassado ao Novo Titular (Split Payment)",
        help=_SPLIT_PAYMENT_HELP
        + " Campo X117, do Segmento X-04. Enviado quando a liquidação ocorre"
        " em quatro partes.",
    )
    split_payment_residual_value = fields.Float(
        string="Valor Residual (Split Payment)",
        help=_SPLIT_PAYMENT_HELP
        + " Campo X118, do Segmento X-04: sobra que retorna ao Beneficiário"
        " original.",
    )
