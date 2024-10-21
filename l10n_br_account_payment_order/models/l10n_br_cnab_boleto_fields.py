# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..constants import get_boleto_especies


class L10nBrCNABBoletoFields(models.AbstractModel):
    _name = "l10n_br_cnab.boleto.fields"
    _inherit = "mail.thread"
    _description = "CNAB - Boleto Fields."

    invoice_print = fields.Boolean(string="Gerar relatorio na conclusão da fatura?")

    instructions = fields.Text(
        string="Instruções de cobrança",
    )

    # Devido a falta de padrão entre os Bancos/CNAB mesmo um campo que
    # possui o objetivo de armazenar a mesma informação pode ter diferentes
    # nomes Código da Empresa/Beneficiario/Convenio/Transmissão mas é
    # possível identifica-lo como:
    #    Campo que tem o código que identifica a Empresa no Banco
    #    e que na maioria dos casos tem o tamanho 20
    # Para evitar criar campos duplicados porque todos contém a mesma
    # informação, como nesse exemplo, foi usado apenas um e na visão
    # está sendo alterado o atributo String de acordo com a nomenclatura
    # usada por cada Banco
    cnab_company_bank_code = fields.Char(
        string="Código da Empresa no Banco",
        size=20,
        help="""Campo que tem o Código que identifica a Empresa no Banco e que
        tem na maioria dos casos o tamanho 20, devido a falta de padrão entre
        os Bancos e CNAB pode ter diferentes nomes Código da Empresa, Beneficiario,
        Convenio, Transmissão, campo G007 e etc porém contém a mesma informação.""",
        tracking=True,
    )

    # Em alguns casos além do 'Código da Empresa no Banco' pode existir
    # outro campo com uma informação referente a:
    #   Um código com tamanho 7 que faz referencia a um
    #   Convenio ou contrato entre a empresa e o Banco
    # Aqui entra a mesma questão do campo acima, devido a falta de
    # nomenclatura dependendendo do Banco/CNAB o nome pode variar mas
    # é importante identifica-lo para evitar a necessidade de criar um
    # novo campo assim diminuindo a duplicação de campos.
    # Por enquanto os casos mapeados são:
    # - Banco do Brasil - chamado de Código do Convênio Líder
    # - Banco Santander - chamado de Código do Convênio
    convention_code = fields.Char(
        string="Código do Convênio",
        size=7,
        help="""Código do Convênio, campo com tamanho 7 usado em alguns casos
        onde além do 'Código da Empresa tamanho 20' existe esse segundo campo,
        casos mapeados hoje são Banco do Brasil como Código do Convênio Líder
        e o Banco Santander como Código do Convênio.
        """,
        tracking=True,
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
        tracking=True,
    )

    boleto_modality = fields.Char(
        string="Modalidade",
        size=2,
        tracking=True,
    )

    boleto_variation = fields.Char(
        string="Variação",
        size=2,
        tracking=True,
    )

    boleto_accept = fields.Selection(
        selection=[("S", "Sim"), ("N", "Não")],
        string="Aceite",
        default="N",
        tracking=True,
    )

    boleto_species = fields.Selection(
        selection=get_boleto_especies(),
        string="Espécie do Título",
        default="01",
        tracking=True,
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
        tracking=True,
    )

    boleto_days_protest = fields.Char(
        string="Número de Dias para Protesto",
        size=2,
        help="Número de dias decorrentes após a data de vencimento "
        "para inicialização do processo de cobrança via protesto.",
        tracking=True,
    )

    generate_own_number = fields.Boolean(
        string="Gerar nosso número?",
        default=True,
        help="Dependendo da carteira, banco, etc. "
        "O nosso número pode ser gerado pelo banco.",
    )

    own_number_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Sequência do Nosso Número",
        help="Para usar essa Sequencia é preciso definir o campo Tipo do "
        "Nosso Número como Sequencial Único por Carteira no cadastro da "
        "empresa",
        tracking=True,
    )

    boleto_interest_code = fields.Char(
        string="Código da Mora",
        size=1,
        help="Código adotado pela FEBRABAN para identificação "
        "do tipo de pagamento de mora de juros.",
        tracking=True,
    )

    boleto_interest_perc = fields.Float(
        string="Percentual de Juros de Mora",
        digits="Account",
        tracking=True,
    )

    boleto_fee_code = fields.Char(
        string="Código da Multa",
        size=1,
        help="Código adotado pela FEBRABAN para identificação "
        "do tipo de pagamento de multa.",
        tracking=True,
    )

    boleto_fee_perc = fields.Float(
        string="Percentual de Multa",
        digits="Account",
        tracking=True,
    )

    boleto_discount_perc = fields.Float(
        string="Percentual de Desconto até a Data de Vencimento",
        digits="Account",
        tracking=True,
    )

    # Contas Contabeis usadas pelo Boleto

    # TODO - criar outro campo para separar a Conta Contabil de Multa ?
    #  o valor vem somado ao Juros Mora no retorno do cnab 400 unicred,
    #  isso seria o padrão dos outros bancos ?
    interest_fee_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Conta Contabil de Juros Mora e Multa",
        help="Conta padrão para Juros Mora",
        tracking=True,
    )

    discount_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Conta Contabil de Desconto",
        help="Conta padrão para Desconto",
        tracking=True,
    )

    rebate_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Conta Contabil de Abatimanto",
        help="Conta padrão para Abatimento",
        tracking=True,
    )

    tariff_charge_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Conta Contabil Tarifa Bancaria",
        help="Conta padrão para a Tarifa Bancaria",
        tracking=True,
    )

    not_payment_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Conta Contabil para Não Pagamento/Inadimplência",
        help="Conta padrão para Não Pagamento/Inadimplência",
        tracking=True,
    )

    # Codigos de Instrução do Movimento

    # Codigo de Remessa/Inclusão de Registro Detalhe Liberado
    # TODO: Remover o campo na próxima versão,
    #  usando apenas para migração para o l10n_br_cnab.code
    cnab_sending_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Sending Movement Instruction Code",
        help="Sending Movement Instruction Code",
        tracking=True,
    )
    sending_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.code",
        string="Sending Movement Instruction Code",
        help="Sending Movement Instruction Code",
        tracking=True,
    )

    # Codigo para Título/Pagamento Direto ao Fornecedor -Baixar
    # TODO: Remover o campo na próxima versão,
    #  usando apenas para migração para o l10n_br_cnab.code
    cnab_write_off_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Write Off Movement Instruction Code",
        help="Write Off Movement Instruction Code",
        tracking=True,
    )
    write_off_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.code",
        string="Write Off Movement Instruction Code",
        help="Write Off Movement Instruction Code",
        tracking=True,
    )

    # Codigo para Alteração do Valor do Titulo
    # TODO: Remover o campo na próxima versão,
    #  usando apenas para migração para o l10n_br_cnab.code
    cnab_code_change_title_value_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Change Title Value Movement Instruction Code",
        help="CNAB Movement Instruction Code for Change Title Value.",
        tracking=True,
    )
    change_title_value_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.code",
        string="Change Title Value Movement Instruction Code",
        help="CNAB Movement Instruction Code for Change Title Value.",
        tracking=True,
    )

    # Codigo para Alteração da Data de Vencimento
    # TODO: Remover o campo na próxima versão,
    #  usando apenas para migração para o l10n_br_cnab.code
    cnab_code_change_maturity_date_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Change Maturity Date Movement Instruction Code",
        help="CNAB Movement Instruction Code for Change Maturity Date.",
        tracking=True,
    )
    change_maturity_date_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.code",
        string="Change Maturity Date Movement Instruction Code",
        help="CNAB Movement Instruction Code for Change Maturity Date.",
        tracking=True,
    )

    # Codigo para Protestar Título
    # TODO: Remover o campo na próxima versão,
    #  usando apenas para migração para o l10n_br_cnab.code
    cnab_code_protest_title_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Protest Tittle Instruction Code",
        help="CNAB Movement Instruction Code for Protest Tittle.",
        tracking=True,
    )
    protest_title_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.code",
        string="Protest Tittle Instruction Code",
        help="CNAB Movement Instruction Code for Protest Tittle.",
        tracking=True,
    )

    # Codigo para Suspender Protesto e Manter em Carteira
    # TODO: Remover o campo na próxima versão,
    #  usando apenas para migração para o l10n_br_cnab.code
    cnab_code_suspend_protest_keep_wallet_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Suspend Protest an Keep in Wallet Instruction Code",
        help="CNAB Movement Instruction Code for"
        " Suspend Protest and Keep in Wallet.",
        tracking=True,
    )
    suspend_protest_keep_wallet_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.code",
        string="Suspend Protest an Keep in Wallet Instruction Code",
        help="CNAB Movement Instruction Code for"
        " Suspend Protest and Keep in Wallet.",
        tracking=True,
    )

    # Codigo para Suspender Protesto e Baixar Título
    # TODO: Remover o campo na próxima versão,
    #  usando apenas para migração para o l10n_br_cnab.code
    cnab_code_suspend_protest_write_off_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Suspend Protest an Writte Off Instruction Code",
        help="CNAB Movement Instruction Code for" " Suspend Protest and Writte Off.",
        tracking=True,
    )
    suspend_protest_write_off_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.code",
        string="Suspend Protest an Writte Off Instruction Code",
        help="CNAB Movement Instruction Code for Suspend Protest and Writte Off.",
        tracking=True,
    )

    # Codigo para Conceder Abatimento
    # TODO: Remover o campo na próxima versão,
    #  usando apenas para migração para o l10n_br_cnab.code
    cnab_code_grant_rebate_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Grant Rebate Instruction Code",
        help="CNAB Movement Instruction Code for" " Grant Rebate.",
        tracking=True,
    )
    grant_rebate_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.code",
        string="Grant Rebate Instruction Code",
        help="CNAB Movement Instruction Code for Grant Rebate.",
        tracking=True,
    )

    # Codigo para Cancelar Abatimento
    # TODO: Remover o campo na próxima versão,
    #  usando apenas para migração para o l10n_br_cnab.code
    cnab_code_cancel_rebate_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Cancel Rebate Instruction Code",
        help="CNAB Movement Instruction Code for" " Cancel Rebate.",
        tracking=True,
    )
    cancel_rebate_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.code",
        string="Cancel Rebate Instruction Code",
        help="CNAB Movement Instruction Code for Cancel Rebate.",
        tracking=True,
    )

    # Codigo para Conceder Desconto
    # TODO: Remover o campo na próxima versão,
    #  usando apenas para migração para o l10n_br_cnab.code
    cnab_code_grant_discount_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Grant Discount Instruction Code",
        help="CNAB Movement Instruction Code for" " Grant Discount.",
        tracking=True,
    )
    grant_discount_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.code",
        string="Grant Discount Instruction Code",
        help="CNAB Movement Instruction Code for Grant Discount.",
        tracking=True,
    )

    # Codigo para Cancelar Desconto
    # TODO: Remover o campo na próxima versão,
    #  usando apenas para migração para o l10n_br_cnab.code
    cnab_code_cancel_discount_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Cancel Discount Instruction Code",
        help="CNAB Movement Instruction Code for Cancel Discount.",
        tracking=True,
    )
    cancel_discount_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.code",
        string="Cancel Discount Instruction Code",
        help="CNAB Movement Instruction Code for Cancel Discount.",
        tracking=True,
    )

    # Campos Especificos de cada Banco

    # Sicredi e Sicoob
    boleto_byte_idt = fields.Char(
        string="Byte IDT",
        size=1,
        help="Byte de identificação do cedente do bloqueto "
        "utilizado para compor o nosso número, "
        "usado pelos bancos Sicred/Unicred e Sicoob.",
        tracking=True,
    )

    boleto_post = fields.Char(
        string="Posto da Cooperativa de Crédito",
        size=2,
        help="Código do Posto da Cooperativa de Crédito,"
        " usado pelos bancos Sicred/Unicred e Sicoob.",
        tracking=True,
    )

    # Código da Carteira ou Tipo de Cobrança usado por
    # Santanter 400 e 240
    # Bradesco 240
    # TODO: Remover o campo na próxima versão,
    #  usando apenas para migração para o l10n_br_cnab.code
    boleto_wallet_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.boleto.wallet.code",
        string="Boleto Wallet Code",
        tracking=True,
    )
    wallet_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.code",
        string="Boleto Wallet Code",
        tracking=True,
    )
