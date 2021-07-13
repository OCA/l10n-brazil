# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons import decimal_precision as dp

from ..constants import BOLETO_ESPECIE


class L10nBrCNABBoletoFields(models.Model):
    _name = "l10n_br_cnab.boleto.fields"
    _description = "CNAB - Boleto Fields."

    invoice_print = fields.Boolean(string="Gerar relatorio na conclusão da fatura?")

    instructions = fields.Text(
        string="Instruções de cobrança",
    )

    code_convetion = fields.Char(
        string="Código do Convênio no Banco",
        size=20,
        help="Campo G007 do CNAB",
        track_visibility="always",
    )

    condition_issuing_paper = fields.Selection(
        selection=[
            ("1", "Banco emite e Processa"),
            ("2", "Cliente emite e banco processa"),
        ],
        string="Condição Emissão de Papeleta",
        default="1",
    )

    communication_2 = fields.Char(
        string="Comunicação para o sacador avalista",
    )

    boleto_wallet = fields.Char(
        string="Carteira",
        size=3,
        track_visibility="always",
    )

    boleto_modality = fields.Char(
        string="Modalidade",
        size=2,
        track_visibility="always",
    )

    boleto_variation = fields.Char(
        string="Variação",
        size=2,
        track_visibility="always",
    )

    boleto_accept = fields.Selection(
        selection=[("S", "Sim"), ("N", "Não")],
        string="Aceite",
        default="N",
        track_visibility="always",
    )

    boleto_species = fields.Selection(
        selection=BOLETO_ESPECIE,
        string="Espécie do Título",
        default="01",
        track_visibility="always",
    )

    # Na configuração ou implementação de outros campos é
    # melhor seguir a idéia abaixo pois os campos não são usados com
    # frequencia e incluir um campo do tipo Char permitindo que seja
    # informado o valor de acordo com a configuração do Boleto ao
    # invês de diversos campos do Tipo Select para cada Banco parece
    # ser melhor.
    # [ Deixado manualmente, pois cada banco parece ter sua tabela.
    # ('0', u'Sem instrução'),
    # ('1', u'Protestar (Dias Corridos)'),
    # ('2', u'Protestar (Dias Úteis)'),
    # ('3', u'Não protestar'),
    # ('7', u'Negativar (Dias Corridos)'),
    # ('8', u'Não Negativar')
    # ]
    boleto_protest_code = fields.Char(
        string="Código de Protesto",
        default="0",
        help="Código adotado pela FEBRABAN para identificar o tipo "
        "de prazo a ser considerado para o protesto.",
        track_visibility="always",
    )

    boleto_days_protest = fields.Char(
        string="Número de Dias para Protesto",
        size=2,
        help="Número de dias decorrentes após a data de vencimento "
        "para inicialização do processo de cobrança via protesto.",
        track_visibility="always",
    )

    generate_own_number = fields.Boolean(
        string="Gerar nosso número?",
        default=True,
        help="Dependendo da carteira, banco, etc. "
        "O nosso número pode ser gerado pelo banco.",
    )

    product_tax_id = fields.Many2one(
        comodel_name="product.product",
        string="Taxa Adicional",
        track_visibility="always",
    )

    own_number_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Sequência do Nosso Número",
        help="Para usar essa Sequencia é preciso definir o campo Tipo do "
        "Nosso Número como Sequencial Único por Carteira no cadastro da "
        "empresa",
        track_visibility="always",
    )

    boleto_interest_code = fields.Char(
        string="Código da Mora",
        size=1,
        help="Código adotado pela FEBRABAN para identificação "
        "do tipo de pagamento de mora de juros.",
        track_visibility="always",
    )

    boleto_interest_perc = fields.Float(
        string="Percentual de Juros de Mora",
        digits=dp.get_precision("Account"),
        track_visibility="always",
    )

    boleto_fee_code = fields.Char(
        string="Código da Multa",
        size=1,
        help="Código adotado pela FEBRABAN para identificação "
        "do tipo de pagamento de multa.",
        track_visibility="always",
    )

    boleto_fee_perc = fields.Float(
        string="Percentual de Multa",
        digits=dp.get_precision("Account"),
        track_visibility="always",
    )

    boleto_discount_perc = fields.Float(
        string=u"Percentual de Desconto até a Data de Vencimento",
        digits=dp.get_precision("Account"),
        track_visibility="always",
    )

    # Contas Contabeis usadas pelo Boleto

    product_tax_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Conta de Taxa do Produto",
        help="Conta padrão para a Taxa do Produto",
        track_visibility="always",
    )

    # TODO - criar outro campo para separar a Conta Contabil de Multa ?
    #  o valor vem somado ao Juros Mora no retorno do cnab 400 unicred,
    #  isso seria o padrão dos outros bancos ?
    interest_fee_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Conta Contabil de Juros Mora e Multa",
        help="Conta padrão para Juros Mora",
        track_visibility="always",
    )

    discount_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Conta Contabil de Desconto",
        help="Conta padrão para Desconto",
        track_visibility="always",
    )

    rebate_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Conta Contabil de Abatimanto",
        help="Conta padrão para Abatimento",
        track_visibility="always",
    )

    tariff_charge_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Conta Contabil Tarifa Bancaria",
        help="Conta padrão para a Tarifa Bancaria",
        track_visibility="always",
    )

    not_payment_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Conta Contabil para Não Pagamento/Inadimplência",
        help="Conta padrão para Não Pagamento/Inadimplência",
        track_visibility="always",
    )

    # Codigos de Instrução do Movimento

    # Codigo de Remessa/Inclusão de Registro Detalhe Liberado
    cnab_sending_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Sending Movement Instruction Code",
        help="Sending Movement Instruction Code",
        track_visibility="always",
    )

    # Codigo para Título/Pagamento Direto ao Fornecedor -Baixar
    cnab_write_off_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Write Off Movement Instruction Code",
        help="Write Off Movement Instruction Code",
        track_visibility="always",
    )

    # Codigo para Alteração do Valor do Titulo
    cnab_code_change_title_value_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Change Title Value Movement Instruction Code",
        help="CNAB Movement Instruction Code for Change Title Value.",
        track_visibility="always",
    )

    # Codigo para Alteração da Data de Vencimento
    cnab_code_change_maturity_date_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Change Maturity Date Movement Instruction Code",
        help="CNAB Movement Instruction Code for Change Maturity Date.",
        track_visibility="always",
    )

    # Codigo para Protestar Título
    cnab_code_protest_title_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Protest Tittle Instruction Code",
        help="CNAB Movement Instruction Code for Protest Tittle.",
        track_visibility="always",
    )

    # Codigo para Suspender Protesto e Manter em Carteira
    cnab_code_suspend_protest_keep_wallet_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Suspend Protest an Keep in Wallet Instruction Code",
        help="CNAB Movement Instruction Code for"
        " Suspend Protest and Keep in Wallet.",
        track_visibility="always",
    )

    # Codigo para Suspender Protesto e Baixar Título
    cnab_code_suspend_protest_write_off_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Suspend Protest an Writte Off Instruction Code",
        help="CNAB Movement Instruction Code for" " Suspend Protest and Writte Off.",
        track_visibility="always",
    )

    # Codigo para Conceder Abatimento
    cnab_code_grant_rebate_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Grant Rebate Instruction Code",
        help="CNAB Movement Instruction Code for" " Grant Rebate.",
        track_visibility="always",
    )

    # Codigo para Cancelar Abatimento
    cnab_code_cancel_rebate_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Cancel Rebate Instruction Code",
        help="CNAB Movement Instruction Code for" " Cancel Rebate.",
        track_visibility="always",
    )

    # Codigo para Conceder Desconto
    cnab_code_grant_discount_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Grant Discount Instruction Code",
        help="CNAB Movement Instruction Code for" " Grant Discount.",
        track_visibility="always",
    )

    # Codigo para Cancelar Abatimento
    cnab_code_cancel_discount_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Cancel Discount Instruction Code",
        help="CNAB Movement Instruction Code for" " Cancel Discount.",
        track_visibility="always",
    )

    # Campos Especificos de cada Banco

    # Sicredi e Sicoob
    boleto_byte_idt = fields.Char(
        string="Byte IDT",
        size=1,
        help="Byte de identificação do cedente do bloqueto "
        "utilizado para compor o nosso número, "
        "usado pelos bancos Sicred/Unicred e Sicoob.",
        track_visibility="always",
    )

    boleto_post = fields.Char(
        string="Posto da Cooperativa de Crédito",
        size=2,
        help="Código do Posto da Cooperativa de Crédito,"
        " usado pelos bancos Sicred/Unicred e Sicoob.",
        track_visibility="always",
    )
