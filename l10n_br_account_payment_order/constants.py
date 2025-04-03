# © 2012 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

CODE_CNAB_240 = "240"
CODE_CNAB_400 = "400"
CODE_CNAB_500 = "500"

CODE_MANUAL_TEST = "manual_test"

BR_CODES_PAYMENT_ORDER = (
    CODE_CNAB_240,
    CODE_CNAB_400,
    CODE_CNAB_500,
    CODE_MANUAL_TEST,
)

COBRANCA = "01"
BOLETO_PAGAMENTO_ELETRONICO = "03"
CONCILIACAO_BANCARIA = "04"
DEBITOS = "05"
CUSTODIA_CHEQUES = "06"
GESTAO_CAIXA = "07"
CONSULTA_INFORMACAO_MARGEM = "08"
AVERBACAO_CONSIGNACAO_RETENCAO = "09"
PAGAMENTO_DIVIDENDOS = "10"
MANUTENCAO_CONSIGNACAO = "11"
CONSIGNACAO_PARCELAS = "12"
GLOSA_CONSIGNACAO = "13"
CONSULTA_TRIBUTOS_PAGAR = "14"
PAGAMENTO_FORNECEDOR = "20"
PAGAMENTO_CONTAS_TRIBUTOS_IMPOSTOS = "22"
INTEROPERABILIDADE_CONTAS = "23"
COMPROR = "25"
COMPROR_ROTATIVO = "26"
ALEGACAO_PAGADOR = "29"
PAGAMENTO_SALARIOS = "30"
PAGAMENTO_HONORARIOS = "32"
PAGAMENTO_BOLSA_AUXILIO = "33"
PAGAMENTO_PREBENDA = "34"
VENDOR = "40"
VENDOR_TERMO = "41"
PAGAMENTO_SINISTROS_SEGURADOS = "50"
PAGAMENTO_DESPESAS_VIAJANTE = "60"
PAGAMENTO_AUTORIZADO = "70"
PAGAMENTO_CREDENCIADOS = "75"
PAGAMENTO_REMUNERACAO = "77"
PAGAMENTO_REPRESENTANTES = "80"
PAGAMENTO_BENEFICIOS = "90"
PAGAMENTOS_DIVERSOS = "98"

TIPO_SERVICO = [
    (COBRANCA, COBRANCA + " - Cobrança"),
    (
        BOLETO_PAGAMENTO_ELETRONICO,
        BOLETO_PAGAMENTO_ELETRONICO + " - Boleto de Pagamento Eletrônico",
    ),
    (CONCILIACAO_BANCARIA, CONCILIACAO_BANCARIA + " - Conciliação Bancária"),
    (DEBITOS, DEBITOS + " - Débitos"),
    (CUSTODIA_CHEQUES, CUSTODIA_CHEQUES + " - Custódia de Cheques"),
    (GESTAO_CAIXA, GESTAO_CAIXA + " - Gestão de Caixa"),
    (
        CONSULTA_INFORMACAO_MARGEM,
        CONSULTA_INFORMACAO_MARGEM + " - Consulta/Informação Margem",
    ),
    (
        AVERBACAO_CONSIGNACAO_RETENCAO,
        AVERBACAO_CONSIGNACAO_RETENCAO + " - Averbação da Consignação/Retenção",
    ),
    (PAGAMENTO_DIVIDENDOS, PAGAMENTO_DIVIDENDOS + " - Pagamento Dividendos"),
    (MANUTENCAO_CONSIGNACAO, MANUTENCAO_CONSIGNACAO + " - Manutenção da Consignação"),
    (CONSIGNACAO_PARCELAS, CONSIGNACAO_PARCELAS + " - Consignação de Parcelas"),
    (GLOSA_CONSIGNACAO, GLOSA_CONSIGNACAO + " -  Glosa da Consignação (INSS)"),
    (
        CONSULTA_TRIBUTOS_PAGAR,
        CONSULTA_TRIBUTOS_PAGAR + " - Consulta de Tributos a pagar",
    ),
    (PAGAMENTO_FORNECEDOR, PAGAMENTO_FORNECEDOR + " - Pagamento Fornecedor"),
    (
        PAGAMENTO_CONTAS_TRIBUTOS_IMPOSTOS,
        PAGAMENTO_CONTAS_TRIBUTOS_IMPOSTOS
        + " - Pagamento de Contas, Tributos e Impostos",
    ),
    (
        INTEROPERABILIDADE_CONTAS,
        INTEROPERABILIDADE_CONTAS
        + " - Interoperabilidade entre Contas de Instituições de Pagamentos",
    ),
    (COMPROR, COMPROR + " - Compror"),
    (COMPROR_ROTATIVO, COMPROR_ROTATIVO + " - Compror Rotativo"),
    (ALEGACAO_PAGADOR, ALEGACAO_PAGADOR + " - Alegação do Pagador"),
    (PAGAMENTO_SALARIOS, PAGAMENTO_SALARIOS + " - Pagamento Salários"),
    (PAGAMENTO_HONORARIOS, PAGAMENTO_HONORARIOS + " - Pagamento de honorários"),
    (
        PAGAMENTO_BOLSA_AUXILIO,
        PAGAMENTO_BOLSA_AUXILIO + " - Pagamento de bolsa auxílio",
    ),
    (
        PAGAMENTO_PREBENDA,
        PAGAMENTO_PREBENDA
        + " - Pagamento de prebenda (remuneração a padres e sacerdotes)",
    ),
    (VENDOR, VENDOR + " - Vendor"),
    (VENDOR_TERMO, VENDOR_TERMO + " - Vendor a Termo"),
    (
        PAGAMENTO_SINISTROS_SEGURADOS,
        PAGAMENTO_SINISTROS_SEGURADOS + " - Pagamento Sinistros Segurados",
    ),
    (
        PAGAMENTO_DESPESAS_VIAJANTE,
        PAGAMENTO_DESPESAS_VIAJANTE + " - Pagamento Despesas Viajante em Trânsito",
    ),
    (PAGAMENTO_AUTORIZADO, PAGAMENTO_AUTORIZADO + " - Pagamento Autorizado"),
    (PAGAMENTO_CREDENCIADOS, PAGAMENTO_CREDENCIADOS + " - Pagamento Credenciados"),
    (PAGAMENTO_REMUNERACAO, PAGAMENTO_REMUNERACAO + " - Pagamento de Remuneração"),
    (
        PAGAMENTO_REPRESENTANTES,
        PAGAMENTO_REPRESENTANTES
        + " - Pagamento Representantes / Vendedores Autorizados",
    ),
    (PAGAMENTO_BENEFICIOS, PAGAMENTO_BENEFICIOS + " - Pagamento Benefícios"),
    (PAGAMENTOS_DIVERSOS, PAGAMENTOS_DIVERSOS + " - Pagamentos Diversos"),
]

CREDITO_CONTA_CORRENTE_SALARIO = ("01", "01 - Crédito em Conta Corrente/Salário")
CHEQUE_PAGAMENTO_ADMINISTRATIVO = ("02", "02 - Cheque Pagamento / Administrativo")
DOC_TED = ("03", "03 - DOC/TED (1) (2)")
CARTAO_SALARIO = ("04", "04 - Cartão Salário (somente para Tipo de Serviço = '30')")
CREDITO_CONTA_POUPANCA = ("05", "05 - Crédito em Conta Poupança")
OP_A_DISPOSICAO = ("10", "10 - OP à Disposição")
PAGAMENTO_CONTAS_TRIBUTOS_CODIGO_BARRAS = (
    "11",
    "11 - Pagamento de Contas e Tributos com Código de Barras",
)
TRIBUTO_DARF_NORMAL = ("16", "16 - Tributo - DARF Normal")
TRIBUTO_GPS = ("17", "17 - Tributo - GPS (Guia da Previdência Social)")
TRIBUTO_DARF_SIMPLES = ("18", "18 - Tributo - DARF Simples")
TRIBUTO_IPTU_PREFEITURAS = ("19", "19 - Tributo - IPTU – Prefeituras")
PAGAMENTO_AUTENTICACAO = ("20", "20 - Pagamento com Autenticação")
TRIBUTO_DARJ = ("21", "21 - Tributo – DARJ")
TRIBUTO_GARE_SP_ICMS = ("22", "22 - Tributo - GARE-SP ICMS")
TRIBUTO_GARE_SP_DR = ("23", "23 - Tributo - GARE-SP DR")
TRIBUTO_GARE_SP_ITCMD = ("24", "24 - Tributo - GARE-SP ITCMD")
TRIBUTO_IPVA = ("25", "25 - Tributo - IPVA")
TRIBUTO_LICENCIAMENTO = ("26", "26 - Tributo - Licenciamento")
TRIBUTO_DPVAT = ("27", "27 - Tributo – DPVAT")
LIQUIDACAO_TITULOS_PROPRIO_BANCO = ("30", "30 - Liquidação de Títulos do Próprio Banco")
PAGAMENTO_TITULOS_OUTROS_BANCOS = ("31", "31 - Pagamento de Títulos de Outros Bancos")
EXTRATO_CONTA_CORRENTE = ("40", "40 - Extrato de Conta Corrente")
TED_OUTRA_TITULARIDADE = ("41", "41 - TED – Outra Titularidade (1)")
TED_MESMA_TITULARIDADE = ("43", "43 - TED – Mesma Titularidade (1)")
TED_TRANSFERENCIA_CONTA_INVESTIMENTO = (
    "44",
    "44 - TED para Transferência de Conta Investimento",
)
DEBITO_CONTA_CORRENTE = ("50", "50 - Débito em Conta Corrente")
EXTRATO_GESTAO_CAIXA = ("70", "70 - Extrato para Gestão de Caixa")
DEPOSITO_JUDICIAL_CONTA_CORRENTE = ("71", "71 - Depósito Judicial em Conta Corrente")
DEPOSITO_JUDICIAL_POUPANCA = ("72", "72 - Depósito Judicial em Poupança")
EXTRATO_CONTA_INVESTIMENTO = ("73", "73 - Extrato de Conta Investimento")

FORMA_LANCAMENTO = [
    CREDITO_CONTA_CORRENTE_SALARIO,
    CHEQUE_PAGAMENTO_ADMINISTRATIVO,
    DOC_TED,
    CARTAO_SALARIO,
    CREDITO_CONTA_POUPANCA,
    OP_A_DISPOSICAO,
    PAGAMENTO_CONTAS_TRIBUTOS_CODIGO_BARRAS,
    TRIBUTO_DARF_NORMAL,
    TRIBUTO_GPS,
    TRIBUTO_DARF_SIMPLES,
    TRIBUTO_IPTU_PREFEITURAS,
    PAGAMENTO_AUTENTICACAO,
    TRIBUTO_DARJ,
    TRIBUTO_GARE_SP_ICMS,
    TRIBUTO_GARE_SP_DR,
    TRIBUTO_GARE_SP_ITCMD,
    TRIBUTO_IPVA,
    TRIBUTO_LICENCIAMENTO,
    TRIBUTO_DPVAT,
    LIQUIDACAO_TITULOS_PROPRIO_BANCO,
    PAGAMENTO_TITULOS_OUTROS_BANCOS,
    EXTRATO_CONTA_CORRENTE,
    TED_OUTRA_TITULARIDADE,
    TED_MESMA_TITULARIDADE,
    TED_TRANSFERENCIA_CONTA_INVESTIMENTO,
    DEBITO_CONTA_CORRENTE,
    EXTRATO_GESTAO_CAIXA,
    DEPOSITO_JUDICIAL_CONTA_CORRENTE,
    DEPOSITO_JUDICIAL_POUPANCA,
    EXTRATO_CONTA_INVESTIMENTO,
]

CREDITO_EM_CONTA = ("01", "01 - Crédito em Conta")
PAGAMENTO_ALUGUEL = ("02", "02 - Pagamento de Aluguel/Condomínio")
PAGAMENTO_DUPLICATA_TITULOS = ("03", "03 - Pagamento de Duplicata/Títulos")
PAGAMENTO_DIVIDENDOS_C = ("04", "04 - Pagamento de Dividendos")
PAGAMENTO_MENSALIDADE_ESCOLAR = ("05", "05 - Pagamento de Mensalidade Escolar")
PAGAMENTO_SALARIOS_C = ("06", "06 - Pagamento de Salários")
PAGAMENTO_FORNECEDORES = ("07", "07 - Pagamento a Fornecedores")
OPERACOES_CAMBIOS_FUNDOS_BOLSA = (
    "08",
    "08 - Operações de Câmbios/Fundos/Bolsa de Valores",
)
REPASSE_ARRECADACAO = ("09", "09 - Repasse de Arrecadação/Pagamento de Tributos")
TRANSFERECIA_INTERNACIONAL_EM_REAL = ("10", "10 - Transferência Internacional em Real")
DOC_POUPANCA = ("11", "11 - DOC para Poupança")
DOC_DEPOSITO_JUDICIAL = ("12", "12 - DOC para Depósito Judicial")
OUTROS = ("13", "13 - Outros")
PAGAMENTO_BOLSA_AUXILIO_C = ("16", "16 - Pagamento de bolsa auxílio")
REMUNERACAO_COOPERADO = ("17", "17 - Remuneração à cooperado")
PAGAMENTO_HONORARIOS_C = ("18", "18 - Pagamento de honorários")
PAGAMENTO_PREBENDA_C = (
    "19",
    "19 - Pagamento de prebenda (Remuneração a padres e sacerdotes)",
)

COMPLEMENTO_TIPO_SERVICO = [
    CREDITO_EM_CONTA,
    PAGAMENTO_ALUGUEL,
    PAGAMENTO_DUPLICATA_TITULOS,
    PAGAMENTO_DIVIDENDOS_C,
    PAGAMENTO_MENSALIDADE_ESCOLAR,
    PAGAMENTO_SALARIOS_C,
    PAGAMENTO_FORNECEDORES,
    OPERACOES_CAMBIOS_FUNDOS_BOLSA,
    REPASSE_ARRECADACAO,
    TRANSFERECIA_INTERNACIONAL_EM_REAL,
    DOC_POUPANCA,
    DOC_DEPOSITO_JUDICIAL,
    OUTROS,
    PAGAMENTO_BOLSA_AUXILIO_C,
    REMUNERACAO_COOPERADO,
    PAGAMENTO_HONORARIOS_C,
    PAGAMENTO_PREBENDA_C,
]

# Codigo adotado pelo Banco Central para identificar a
# finalidade da TED. Utitilizar os
# códigos de finalidade cliente, disponíveis no site do Banco Central do Brasil
# (www.bcb.gov.br), Sistema de Pagamentos Brasileiro,
# Transferência de Arquivos,
# Dicionários de Domínios para o SPB.
CODIGO_FINALIDADE_TED = [("    ", "Padrão")]

NAO_EMITE_AVISO = ("0", "0 - Não Emite Aviso")
EMITE_AVISO_REMETENTE = ("2", "2 - Emite Aviso Somente para o Remetente")
EMITE_AVISO_FAVORECIDO = ("5", "5 - Emite Aviso Somente para o Favorecido")
EMITE_AVISO_REMETENTE_FAVORECIDO = (
    "6",
    "6 - Emite Aviso para o Remetente e Favorecido",
)
EMITE_AVISO_FAVORECIDO_2_VIAS_REMETENTE = (
    "7",
    "7 - Emite Aviso para o Favorecido e 2 Vias para o Remetente",
)

AVISO_FAVORECIDO = [
    NAO_EMITE_AVISO,
    EMITE_AVISO_REMETENTE,
    EMITE_AVISO_FAVORECIDO,
    EMITE_AVISO_REMETENTE_FAVORECIDO,
    EMITE_AVISO_FAVORECIDO_2_VIAS_REMETENTE,
]

INDICATIVO_FORMA_PAGAMENTO = [
    ("01", "01 - Débito em Conta Corrente"),
    ("02", "02 - Débito Empréstimo/Financiamento"),
    ("03", "03 - Débito Cartão de Crédito"),
]

TIPO_MOVIMENTO = [
    ("0", "0 - Indica INCLUSÃO"),
    ("1", "1 - Indica CONSULTA"),
    ("2", "2 - Indica SUSPENSÃO"),
    ("3", "3 - Indica ESTORNO (somente para retorno)"),
    ("4", "4 - Indica REATIVAÇÃO"),
    ("5", "5 - Indica ALTERAÇÃO"),
    ("7", "7 - Indica LIQUIDAÇAO"),
    ("9", "9 - Indica EXCLUSÃO"),
]

ESTADOS_CNAB = [
    ("draft", "Inicial"),
    ("added", "Adicionada à ordem de pagamento"),
    ("added_paid", "Adicionada para Baixa"),
    ("exported", "Exportada"),
    ("exporting_error", "Erro ao exportar"),
    ("accepted", "Aceita"),
    ("accepted_hml", "Aceita em Homologação"),
    ("not_accepted", "Não aceita pelo banco"),
    ("done", "Concluído"),
]

SITUACAO_PAGAMENTO = [
    ("inicial", "Inicial"),
    ("aberta", "Aberta"),
    ("paga", "Paga"),
    ("liquidada", "Liquidada"),
    ("baixa", "Baixa Simples"),
    ("baixa_liquidacao", "Baixa por Liquidação fora do CNAB"),
    ("nao_pagamento", "Baixa por Não Pagamento/Inadimplência"),
    ("fatura_cancelada", "Baixa por Cancelamento da Fatura"),
]

BOLETO_ESPECIE = [
    # CODE, DESCRIPTION, SHORT NAME
    ("01", "DUPLICATA MERCANTIL", "DM"),
    ("02", "NOTA PROMISSÓRIA", "NP"),
    ("03", "NOTA DE SEGURO", "NS"),
    ("04", "MENSALIDADE ESCOLAR", "ME"),
    ("05", "RECIBO", "REC"),
    ("06", "CONTRATO", "CONT"),
    ("07", "COSSEGUROS", "COSSEG"),
    ("08", "DUPLICATA DE SERVIÇO", "DS"),
    ("09", "LETRA DE CÂMBIO", "LC"),
    ("13", "NOTA DE DÉBITOS", "ND"),
    ("15", "DOCUMENTO DE DÍVIDA", "DD"),
    ("16", "ENCARGOS CONDOMINIAIS", "EC"),
    ("17", "CONTA DE PRESTAÇÃO DE SERVIÇOS", "CPS"),
    ("99", "DIVERSOS", "DIV"),
]


def get_boleto_especies():
    # return the list of "boleto especie" only code and description
    return [(code, desc) for code, desc, _ in BOLETO_ESPECIE]


def get_boleto_especie_short_name(selected_code):
    # return the short name of "boleto especie"
    for code, _, short_name in BOLETO_ESPECIE:
        if code == selected_code:
            return short_name
    return None


STATE_CNAB = [
    ("draft", "Novo"),
    ("done", "Processado"),
    ("error", "Erro no Processamento"),
]

TIPO_OPERACAO_CNAB = {
    "C": "Lançamento a Crédito",
    "D": "Lançamento a Débito",
    "E": "Extrato para Conciliação",
    "G": "Extrato para Gestão de Caixa",
    "I": "Informações de Títulos Capturados do Próprio Banco",
    "R": "Arquivo Remessa",
    "T": "Arquivo Retorno",
}
