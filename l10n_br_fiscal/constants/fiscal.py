# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _

OPERATION_STATE = [
    ("draft", "Draft"),
    ("review", "Review"),
    ("approved", "Approved"),
    ("expired", "Expired"),
]


OPERATION_STATE_DEFAULT = "draft"


OPERATION_FISCAL_TYPE = [
    ("purchase", "Purchase"),
    ("purchase_refund", "Purchase Return"),
    ("return_in", "Return in"),
    ("sale", "Sale"),
    ("sale_refund", "Sale Return"),
    ("return_out", "Return Out"),
    ("other", "Other")]


OPERATION_FISCAL_TYPE_DEFAULT = 'other'


COMMENT_TYPE = [("fiscal", "Fiscal"), ("commercial", "Commercial")]


COMMENT_TYPE_DEFAULT = "commercial"


PRODUCT_FISCAL_TYPE = (
    ("00", "Mercadoria para Revenda"),
    ("01", "Matéria-prima"),
    ("02", "Embalagem"),
    ("03", "Produto em Processo"),
    ("04", "Produto Acabado"),
    ("05", "Subproduto"),
    ("06", "Produto Intermediário"),
    ("07", "Material de Uso e Consumo"),
    ("08", "Ativo Imobilizado"),
    ("09", "Serviços"),
    ("10", "Outros insumos"),
    ("99", "Outras"),
)

PRODUCT_FISCAL_TYPE_SERVICE = "09"

NCM_FOR_SERVICE = "0000.00.00"
NCM_FOR_SERVICE_REF = "l10n_br_fiscal.ncm_00000000"


TAX_BASE_TYPE = (
    ("percent", _("Percent")),
    ("quantity", _("Quantity")),
    ("fixed", _("Fixed")),
)


TAX_BASE_TYPE_PERCENT = "percent"


TAX_DOMAIN = (
    ("ipi", "IPI"),
    ("icms", "ICMS - Próprio"),
    ("icmssn", "ICMS - Simples Nacional"),
    ("icmsfcp", "ICMS FCP - Fundo de Combate a Pobreza"),
    ("icmsst", "ICMS - Subistituição Tributária"),
    ("pis", "PIS"),
    ("pisst", "PIS ST"),
    ("cofins", "COFINS"),
    ("cofinsst", "COFINS ST"),
    ("issqn", "ISSQN"),
    ("irpj", "IRPJ"),
    ("ir", "IR"),
    ("csll", "CSLL"),
    ("ii", "II"),
    ("simples", "Simples Nacional"),
    ("others", "Outros"),
)


TAX_DOMAIN_IPI = "ipi"
TAX_DOMAIN_II = "ii"
TAX_DOMAIN_ICMS = "icms"
TAX_DOMAIN_ICMS_SN = "icmssn"
TAX_DOMAIN_ICMS_ST = "icmsst"
TAX_DOMAIN_ICMS_FCP = "icmsfcp"
TAX_DOMAIN_ISSQN = "issqn"
TAX_DOMAIN_PIS = "pis"
TAX_DOMAIN_PIS_ST = "pisst"
TAX_DOMAIN_COFINS = "cofins"
TAX_DOMAIN_COFINS_ST = "cofinsst"


TAX_FRAMEWORK = (
    ("1", "1 - Simples Nacional"),
    ("2", "2 - Simples Nacional – excesso de sublimite da receita bruta"),
    ("3", "3 - Regime Normal"),
)


TAX_FRAMEWORK_SIMPLES = "1"
TAX_FRAMEWORK_SIMPLES_EX = "2"
TAX_FRAMEWORK_NORMAL = "3"
TAX_FRAMEWORK_SIMPLES_ALL = ("1", "2")

PROFIT_CALCULATION = (
    ("real", "Real"),
    ("presumed", "Presumed"),
    ("arbitrary", "Arbitrary"),
)


PROFIT_CALCULATION_PRESUMED = "presumed"


INDUSTRY_TYPE = (
    ("00", "00 - Industrial - Transformação"),
    ("01", "01 - Industrial - Beneficiamento"),
    ("02", "02 - Industrial - Montagem"),
    ("03", "03 - Industrial - Acondicionamento ou Reacondicionamento"),
    ("04", "04 - Industrial - Renovação ou Recondicionamento"),
    ("05", "05 - Equiparado a industrial - Por opção"),
    ("06", "06 - Equiparado a industrial - Importação Direta"),
    ("07", "07 - Equiparado a industrial - Por lei específica"),
    ("08", "08 - Equiparado a industrial - Não enquadrado nos" " códigos 05, 06 ou 07"),
    ("09", "09 - Outros"),
)


INDUSTRY_TYPE_TRANSFORMATION = "00"


CERTIFICATE_TYPE = (("e-cpf", "E-CPF"), ("e-cnpj", "E-CNPJ"), ("nf-e", "NF-e"))


CERTIFICATE_TYPE_DEFAULT = "nf-e"


CERTIFICATE_SUBTYPE = (("a1", "A1"), ("a3", "A3"))


CERTIFICATE_SUBTYPE_DEFAULT = "a1"


FISCAL_IN_OUT = (("in", "In"), ("out", "Out"))


FISCAL_IN_OUT_ALL = (("in", "In"), ("out", "Out"), ("all", "All"))


FISCAL_IN = "in"


FISCAL_OUT = "out"


FISCAL_IN_OUT_DEFAULT = "in"


DOCUMENT_TYPE = (("icms", "ICMS"), ("service", "Serviço Municipal"))


DOCUMENT_ISSUER = (("0", "Emissão Própria"), ("1", "Terceiros"))


CFOP_DESTINATION = (
    ("1", "Operação Interna"),
    ("2", "Operação Interestadual"),
    ("3", "Operação com Exterior"),
)


CFOP_DESTINATION_INTERNAL = "1"
CFOP_DESTINATION_EXTERNAL = "2"
CFOP_DESTINATION_EXPORT = "3"


CEST_SEGMENT = (
    ("01", "Autopeças"),
    ("02", "Bebidas alcoólicas, exceto cerveja e chope"),
    ("03", "Cervejas, chopes, refrigerantes, águas e outras bebidas"),
    ("04", "Cigarros e outros produtos derivados do fumo"),
    ("05", "Cimentos"),
    ("06", "Combustíveis e lubrificantes"),
    ("07", "Energia elétrica"),
    ("08", "Ferramentas"),
    ("09", "Lâmpadas, reatores e “starter”"),
    ("10", "Materiais de construção e congêneres"),
    ("11", "Materiais de limpeza"),
    ("12", "Materiais elétricos"),
    (
        "13",
        "Medicamentos de uso humano e outros produtos"
        " farmacêuticos para uso humano ou veterinário",
    ),
    ("14", "Papéis, plásticos, produtos cerâmicos e vidros"),
    ("15", "Pneumáticos, câmaras de ar e protetores de borracha"),
    ("16", "Produtos alimentícios"),
    ("17", "Produtos de papelaria"),
    ("18", "Produtos de perfumaria e de higiene pessoal e cosméticos"),
    ("19", "Produtos eletrônicos, eletroeletrônicos e eletrodomésticos"),
    ("20", "Rações para animais domésticos"),
    ("21", "Sorvetes e preparados para fabricação de sorvetes em máquinas"),
    ("22", "Tintas e vernizes"),
    ("23", "Veículos automotores"),
    ("24", "Veículos de duas e três rodas motorizados"),
    ("25", "Venda de mercadorias pelo sistema porta a porta"),
)


NFE_IND_IE_DEST = [
    ("1", "1 - Contribuinte do ICMS"),
    ("2", "2 - Contribuinte Isento do ICMS"),
    ("9", "9 - Não Contribuinte"),
]

NFE_IND_IE_DEST_DEFAULT = NFE_IND_IE_DEST[0][0]

NFE_IND_IE_DEST_1 = "1"
NFE_IND_IE_DEST_2 = "2"
NFE_IND_IE_DEST_9 = "9"


CFOP_TYPE_MOVE = [
    ("purchase_industry", "Purchase Industry"),
    ("purchase_commerce", "Purchase Commerce"),
    ("purchase_asset", "Purchase Asset"),
    ("purchase_ownuse", "Purchase Own Use"),
    ("purchase_service", "Purchase Service"),
    ("purchase_refund", "Purchase Refund"),
    ("return_in", "Return in"),
    ("sale_industry", "Sale Industry"),
    ("sale_commerce", "Sale Commerce"),
    ("sale_asset", "Sale Asset"),
    ("sale_ownuse", "Sale Own Use"),
    ("sale_service", "Sale Service"),
    ("sale_refund", "Sale Refund"),
    ("return_out", "Return Out"),
    ("other", "Other"),
]

CFOP_TYPE_MOVE_DEFAULT = "other"

MODELO_FISCAL_NFE = "55"
MODELO_FISCAL_NFCE = "65"
MODELO_FISCAL_NFSE = "SE"
MODELO_FISCAL_CFE = "59"
MODELO_FISCAL_CUPOM_FISCAL_ECF = "2D"
MODELO_FISCAL_CTE = "57"
MODELO_FISCAL_RL = "RL"

MODELO_FISCAL_EMISSAO_PRODUTO = (
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_CFE,
    MODELO_FISCAL_CUPOM_FISCAL_ECF,
)
MODELO_FISCAL_EMISSAO_SERVICO = (
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFSE,
    MODELO_FISCAL_RL,
)

AUTORIZADO = ("100", "150")
DENEGADO = ("110", "301", "302")
LOTE_RECEBIDO = ["103"]
LOTE_PROCESSADO = ["104"]
LOTE_EM_PROCESSAMENTO = ["105"]

CANCELAMENTO_HOMOLOGADO = ["101", "151"]

CANCELADO_DENTRO_PRAZO = ["135"]
CANCELADO_FORA_PRAZO = ["155"]

CANCELADO = CANCELADO_DENTRO_PRAZO + CANCELADO_FORA_PRAZO + CANCELAMENTO_HOMOLOGADO

AUTORIZADO_OU_DENEGADO = AUTORIZADO + DENEGADO


SITUACAO_EDOC_EM_DIGITACAO = "em_digitacao"
SITUACAO_EDOC_A_ENVIAR = "a_enviar"
SITUACAO_EDOC_ENVIADA = "enviada"
SITUACAO_EDOC_REJEITADA = "rejeitada"
SITUACAO_EDOC_AUTORIZADA = "autorizada"
SITUACAO_EDOC_CANCELADA = "cancelada"
SITUACAO_EDOC_DENEGADA = "denegada"
SITUACAO_EDOC_INUTILIZADA = "inutilizada"


SITUACAO_EDOC = (
    (SITUACAO_EDOC_EM_DIGITACAO, "Em digitação"),
    (SITUACAO_EDOC_A_ENVIAR, "Aguardando envio"),
    (SITUACAO_EDOC_ENVIADA, "Aguardando processamento"),
    (SITUACAO_EDOC_REJEITADA, "Rejeitada"),
    (SITUACAO_EDOC_AUTORIZADA, "Autorizada"),
    (SITUACAO_EDOC_CANCELADA, "Cancelada"),
    (SITUACAO_EDOC_DENEGADA, "Denegada"),
    (SITUACAO_EDOC_INUTILIZADA, "Inutilizada"),
)
SITUACAO_EDOC_DICT = dict(SITUACAO_EDOC)

SITUACAO_FISCAL_REGULAR = "00"
SITUACAO_FISCAL_REGULAR_EXTEMPORANEO = "01"
SITUACAO_FISCAL_CANCELADO = "02"
SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO = "03"
SITUACAO_FISCAL_DENEGADO = "04"
SITUACAO_FISCAL_INUTILIZADO = "05"
SITUACAO_FISCAL_COMPLEMENTAR = "06"
SITUACAO_FISCAL_COMPLEMENTAR_EXTEMPORANEO = "07"
SITUACAO_FISCAL_REGIME_ESPECIAL = "08"
SITUACAO_FISCAL_MERCADORIA_NAO_CIRCULOU = "NC"
SITUACAO_FISCAL_MERCADORIA_NAO_RECEBIDA = "MR"

SITUACAO_FISCAL = (
    (SITUACAO_FISCAL_REGULAR, "Regular"),
    (SITUACAO_FISCAL_REGULAR_EXTEMPORANEO, "Regular extemporâneo"),
    (SITUACAO_FISCAL_CANCELADO, "Cancelado"),
    (SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO, "Cancelado extemporâneo"),
    (SITUACAO_FISCAL_DENEGADO, "Denegado"),
    (SITUACAO_FISCAL_INUTILIZADO, "Numeração inutilizada"),
    (SITUACAO_FISCAL_COMPLEMENTAR, "Complementar"),
    (SITUACAO_FISCAL_COMPLEMENTAR_EXTEMPORANEO, "Complementar extemporâneo"),
    (SITUACAO_FISCAL_REGIME_ESPECIAL, "Regime especial ou norma específica"),
    (SITUACAO_FISCAL_MERCADORIA_NAO_CIRCULOU, "Mercadoria não circulou"),
    (SITUACAO_FISCAL_MERCADORIA_NAO_RECEBIDA, "Mercadoria não recebida"),
)
SITUACAO_FISCAL_DICT = dict(SITUACAO_FISCAL)


SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO = (
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
    SITUACAO_FISCAL_DENEGADO,
    SITUACAO_FISCAL_INUTILIZADO,
)

SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO = (
    SITUACAO_FISCAL_REGULAR,
    SITUACAO_FISCAL_REGULAR_EXTEMPORANEO,
    SITUACAO_FISCAL_COMPLEMENTAR,
    SITUACAO_FISCAL_COMPLEMENTAR_EXTEMPORANEO,
    SITUACAO_FISCAL_REGIME_ESPECIAL,
)

SITUACAO_FISCAL_EXTEMPORANEO = (
    SITUACAO_FISCAL_REGULAR_EXTEMPORANEO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
    SITUACAO_FISCAL_COMPLEMENTAR_EXTEMPORANEO,
)

WORKFLOW_DOCUMENTO_NAO_ELETRONICO = [
    (SITUACAO_EDOC_EM_DIGITACAO, SITUACAO_EDOC_A_ENVIAR),
    (SITUACAO_EDOC_EM_DIGITACAO, SITUACAO_EDOC_AUTORIZADA),
    (SITUACAO_EDOC_A_ENVIAR, SITUACAO_EDOC_AUTORIZADA),
    (SITUACAO_EDOC_EM_DIGITACAO, SITUACAO_EDOC_CANCELADA),
    (SITUACAO_EDOC_AUTORIZADA, SITUACAO_EDOC_CANCELADA),
    (SITUACAO_EDOC_CANCELADA, SITUACAO_EDOC_EM_DIGITACAO),
]

WORKFLOW_EDOC = WORKFLOW_DOCUMENTO_NAO_ELETRONICO + [
    (SITUACAO_EDOC_EM_DIGITACAO, SITUACAO_EDOC_ENVIADA),
    (SITUACAO_EDOC_EM_DIGITACAO, SITUACAO_EDOC_REJEITADA),
    (SITUACAO_EDOC_EM_DIGITACAO, SITUACAO_EDOC_DENEGADA),
    (SITUACAO_EDOC_A_ENVIAR, SITUACAO_EDOC_ENVIADA),
    (SITUACAO_EDOC_A_ENVIAR, SITUACAO_EDOC_REJEITADA),
    (SITUACAO_EDOC_A_ENVIAR, SITUACAO_EDOC_AUTORIZADA),
    (SITUACAO_EDOC_A_ENVIAR, SITUACAO_EDOC_DENEGADA),
    (SITUACAO_EDOC_A_ENVIAR, SITUACAO_EDOC_CANCELADA),
    (SITUACAO_EDOC_ENVIADA, SITUACAO_EDOC_REJEITADA),
    (SITUACAO_EDOC_ENVIADA, SITUACAO_EDOC_AUTORIZADA),
    (SITUACAO_EDOC_ENVIADA, SITUACAO_EDOC_DENEGADA),
    (SITUACAO_EDOC_REJEITADA, SITUACAO_EDOC_AUTORIZADA),
    (SITUACAO_EDOC_REJEITADA, SITUACAO_EDOC_EM_DIGITACAO),
    (SITUACAO_EDOC_REJEITADA, SITUACAO_EDOC_REJEITADA),
]

PROCESSADOR_NENHUM = 'nenhum'

PROCESSADOR = [(
    PROCESSADOR_NENHUM, 'Nenhum'
)]
