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

CODIGO_OCORRENCIAS = [
    ("00", "00 - Crédito ou Débito Efetivado"),
    ("01", "01 - Insuficiência de Fundos - Débito Não Efetuado"),
    ("02", "02 - Crédito ou Débito Cancelado pelo Pagador/Credor"),
    ("03", "03 - Débito Autorizado pela Agência - Efetuado"),
    ("AA", "AA - Controle Inválido"),
    ("AB", "AB - Tipo de Operação Inválido"),
    ("AC", "AC - Tipo de Serviço Inválido"),
    ("AD", "AD - Forma de Lançamento Inválida"),
    ("AE", "AE - Tipo/Número de Inscrição Inválido"),
    ("AF", "AF - Código de Convênio Inválido"),
    ("AG", "AG - Agência/Conta Corrente/DV Inválido"),
    ("AH", "AH - Nº Seqüencial do Registro no Lote Inválido"),
    ("AI", "AI - Código de Segmento de Detalhe Inválido"),
    ("AJ", "AJ - Tipo de Movimento Inválido"),
    (
        "AK",
        "AK - Código da Câmara de Compensação do Banco"
        " Favorecido/Depositário Inválido",
    ),
    (
        "AL",
        "AL - Código do Banco Favorecido, Instituição de Pagamento"
        " ou Depositário Inválido",
    ),
    ("AM", "AM - Agência Mantenedora da Conta Corrente do" " Favorecido Inválida"),
    ("AN", "AN - Conta Corrente/DV/Conta de Pagamento do" " Favorecido Inválido"),
    ("AO", "AO - Nome do Favorecido Não Informado"),
    ("AP", "AP - Data Lançamento Inválido"),
    ("AQ", "AQ - Tipo/Quantidade da Moeda Inválido"),
    ("AR", "AR - Valor do Lançamento Inválido"),
    ("AS", "AS - Aviso ao Favorecido - Identificação Inválida"),
    ("AT", "AT - Tipo/Número de Inscrição do Favorecido Inválido"),
    ("AU", "AU - Logradouro do Favorecido Não Informado"),
    ("AV", "AV - Nº do Local do Favorecido Não Informado"),
    ("AW", "AW - Cidade do Favorecido Não Informada"),
    ("AX", "AX - CEP/Complemento do Favorecido Inválido"),
    ("AY", "AY - Sigla do Estado do Favorecido Inválida"),
    ("AZ", "AZ - Código/Nome do Banco Depositário Inválido"),
    ("BA", "BA - Código/Nome da Agência Depositária Não Informado"),
    ("BB", "BB - Seu Número Inválido"),
    ("BC", "BC - Nosso Número Inválido"),
    ("BD", "BD - Inclusão Efetuada com Sucesso"),
    ("BE", "BE - Alteração Efetuada com Sucesso"),
    ("BF", "BF - Exclusão Efetuada com Sucesso"),
    ("BG", "BG - Agência/Conta Impedida Legalmente"),
    ("BH", "BH - Empresa não pagou salário"),
    ("BI", "BI - Falecimento do mutuário"),
    ("BJ", "BJ - Empresa não enviou remessa do mutuário"),
    ("BK", "BK - Empresa não enviou remessa no vencimento"),
    ("BL", "BL - Valor da parcela inválida"),
    ("BM", "BM - Identificação do contrato inválida"),
    ("BN", "BN - Operação de Consignação Incluída com Sucesso"),
    ("BO", "BO - Operação de Consignação Alterada com Sucesso"),
    ("BP", "BP - Operação de Consignação Excluída com Sucesso"),
    ("BQ", "BQ - Operação de Consignação Liquidada com Sucesso"),
    ("BR", "BR - Reativação Efetuada com Sucesso"),
    ("BS", "BS - Suspensão Efetuada com Sucesso"),
    ("CA", "CA - Código de Barras - Código do Banco Inválido"),
    ("CB", "CB - Código de Barras - Código da Moeda Inválido"),
    ("CC", "CC - Código de Barras - Dígito Verificador Geral Inválido"),
    ("CD", "CD - Código de Barras - Valor do Título Inválido"),
    ("CE", "CE - Código de Barras - Campo Livre Inválido"),
    ("CF", "CF - Valor do Documento Inválido"),
    ("CG", "CG - Valor do Abatimento Inválido"),
    ("CH", "CH - Valor do Desconto Inválido"),
    ("CI", "CI - Valor de Mora Inválido"),
    ("CJ", "CJ - Valor da Multa Inválido"),
    ("CK", "CK - Valor do IR Inválido"),
    ("CL", "CL - Valor do ISS Inválido"),
    ("CM", "CM - Valor do IOF Inválido"),
    ("CN", "CN - Valor de Outras Deduções Inválido"),
    ("CO", "CO - Valor de Outros Acréscimos Inválido"),
    ("CP", "CP - Valor do INSS Inválido"),
    ("HA", "HA - Lote Não Aceito"),
    ("HB", "HB - Inscrição da Empresa Inválida para o Contrato"),
    ("HC", "HC - Convênio com a Empresa Inexistente/Inválido" " para o Contrato"),
    (
        "HD",
        "HD - Agência/Conta Corrente da Empresa Inexistente/Inválido"
        " para o Contrato",
    ),
    ("HE", "HE - Tipo de Serviço Inválido para o Contrato"),
    ("HF", "HF - Conta Corrente da Empresa com Saldo Insuficiente"),
    ("HG", "HG - Lote de Serviço Fora de Seqüência"),
    ("HH", "HH - Lote de Serviço Inválido"),
    ("HI", "HI - Arquivo não aceito"),
    ("HJ", "HJ - Tipo de Registro Inválido"),
    ("HK", "HK - Código Remessa / Retorno Inválido"),
    ("HL", "HL - Versão de layout inválida"),
    ("HM", "HM - Mutuário não identificado"),
    ("HN", "HN - Tipo do beneficio não permite empréstimo"),
    ("HO", "HO - Beneficio cessado/suspenso"),
    ("HP", "HP - Beneficio possui representante legal"),
    ("HQ", "HQ - Beneficio é do tipo PA (Pensão alimentícia)"),
    ("HR", "HR - Quantidade de contratos permitida excedida"),
    ("HS", "HS - Beneficio não pertence ao Banco informado"),
    ("HT", "HT - Início do desconto informado já ultrapassado"),
    ("HU", "HU - Número da parcela inválida"),
    ("HV", "HV - Quantidade de parcela inválida"),
    (
        "HW",
        "HW - Margem consignável excedida para o mutuário dentro"
        " do prazo do contrato",
    ),
    ("HX", "HX - Empréstimo já cadastrado"),
    ("HY", "HY - Empréstimo inexistente"),
    ("HZ", "HZ - Empréstimo já encerrado"),
    ("H1", "H1 - Arquivo sem trailer"),
    ("H2", "H2 - Mutuário sem crédito na competência"),
    ("H3", "H3 - Não descontado – outros motivos"),
    ("H4", "H4 - Retorno de Crédito não pago"),
    ("H5", "H5 - Cancelamento de empréstimo retroativo"),
    ("H6", "H6 - Outros Motivos de Glosa"),
    (
        "H7",
        "H7 - Margem consignável excedida para o mutuário acima"
        " do prazo do contrato",
    ),
    ("H8", "H8 - Mutuário desligado do empregador"),
    ("H9", "H9 - Mutuário afastado por licença"),
    (
        "IA",
        "IA - Primeiro nome do mutuário diferente do primeiro nome"
        " do movimento do censo ou diferente da base de Titular"
        " do Benefício",
    ),
    ("IB", "IB - Benefício suspenso/cessado pela APS ou Sisobi"),
    ("IC", "IC - Benefício suspenso por dependência de cálculo"),
    ("ID", "ID - Benefício suspenso/cessado pela inspetoria/auditoria"),
    ("IE", "IE - Benefício bloqueado para empréstimo pelo beneficiário"),
    ("IF", "IF - Benefício bloqueado para empréstimo por TBM"),
    ("IG", "IG - Benefício está em fase de concessão de PA ou desdobramento"),
    ("IH", "IH - Benefício cessado por óbito"),
    ("II", "II - Benefício cessado por fraude"),
    ("IJ", "IJ - Benefício cessado por concessão de outro benefício"),
    ("IK", "IK - Benefício cessado: estatutário transferido" " para órgão de origem"),
    ("IL", "IL - Empréstimo suspenso pela APS"),
    ("IM", "IM - Empréstimo cancelado pelo banco"),
    ("IN", "IN - Crédito transformado em PAB"),
    ("IO", "IO - Término da consignação foi alterado"),
    (
        "IP",
        "IP - Fim do empréstimo ocorreu durante período" " de suspensão ou concessão",
    ),
    ("IQ", "IQ - Empréstimo suspenso pelo banco"),
    (
        "IR",
        "IR - Não averbação de contrato – quantidade de"
        " parcelas/competências informadas ultrapassou a data limite"
        " da extinção de cota do dependente titular de benefícios",
    ),
    ("TA", "TA - Lote Não Aceito - Totais do Lote com Diferença"),
    ("YA", "YA - Título Não Encontrado"),
    ("YB", "YB - Identificador Registro Opcional Inválido"),
    ("YC", "YC - Código Padrão Inválido"),
    ("YD", "YD - Código de Ocorrência Inválido"),
    ("YE", "YE - Complemento de Ocorrência Inválido"),
    ("YF", "YF - Alegação já Informada"),
    ("ZA", "ZA - Agência / Conta do Favorecido Substituída"),
    (
        "ZB",
        "ZB - Divergência entre o primeiro e último nome do beneficiário"
        " versus primeiro e último nome na Receita Federal",
    ),
    ("ZC", "ZC - Confirmação de Antecipação de Valor"),
    ("ZD", "ZD - Antecipação parcial de valor"),
    ("ZE", "ZE - Título bloqueado na base"),
    ("ZF", "ZF - Sistema em contingência" " – título valor maior que referência"),
    ("ZG", "ZG - Sistema em contingência – título vencido"),
    ("ZH", "ZH - Sistema em contingência – título indexado"),
    ("ZI", "ZI - Beneficiário divergente"),
    ("ZJ", "ZJ - Limite de pagamentos parciais excedido"),
    ("ZK", "ZK - Boleto já liquidado"),
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

# COD_REGISTROS_REJEITADOS_CNAB400 -> USADO QUANDO HA CODIGO DE OCORRENCIA 03
# NA POSIÇÃO 109-110
COD_REGISTROS_REJEITADOS_CNAB400 = {
    3: "AG. COBRADORA - CEP SEM ATENDIMENTO DE PROTESTO NO MOMENTO",
    4: "ESTADO - SIGLA DO ESTADO INVÁLIDA",
    5: "DATA VENCIMENTO - PRAZO DA OPERAÇÃO MENOR QUE PRAZO MÍNIMO OU MAIOR QUE O MÁXIMO",  # noqa
    7: "VALOR DO TÍTULO - VALOR DO TÍTULO MAIOR QUE 10.000.000,00",
    8: "NOME DO PAGADOR - NÃO INFORMADO OU DESLOCADO",
    9: "AGENCIA/CONTA - AGÊNCIA ENCERRADA",
    10: "LOGRADOURO - NÃO INFORMADO OU DESLOCADO",
    11: "CEP - CEP NÃO NUMÉRICO OU CEP INVÁLIDO",
    12: "SACADOR / AVALISTA - NOME NÃO INFORMADO OU DESLOCADO (BANCOS CORRESPONDENTES)",  # noqa
    13: "ESTADO/CEP - CEP INCOMPATÍVEL COM A SIGLA DO ESTADO",
    14: "NOSSO NÚMERO - NOSSO NÚMERO JÁ REGISTRADO NO CADASTRO DO BANCO OU FORA DA FAIXA",  # noqa
    15: "NOSSO NÚMERO - NOSSO NÚMERO EM DUPLICIDADE NO MESMO MOVIMENTO",
    18: "DATA DE ENTRADA - DATA DE ENTRADA INVÁLIDA PARA OPERAR COM ESTA CARTEIRA",
    19: "OCORRÊNCIA - OCORRÊNCIA INVÁLIDA",
    21: "AG. COBRADORA - CARTEIRA NÃO ACEITA DEPOSITÁRIA CORRESPONDENTE ESTADO DA AGÊNCIA DIFERENTE DO ESTADO DO PAGADOR AG. COBRADORA NÃO CONSTA NO CADASTRO OU ENCERRANDO",  # noqa
    22: "CARTEIRA - CARTEIRA NÃO PERMITIDA (NECESSÁRIO CADASTRAR FAIXA LIVRE)",
    26: "AGÊNCIA/CONTA - AGÊNCIA/CONTA NÃO LIBERADA PARA OPERAR COM COBRANÇA",
    27: "CNPJ INAPTO - CNPJ DO BENEFICIÁRIO INAPTO DEVOLUÇÃO DE TÍTULO EM GARANTIA",
    29: "CÓDIGO EMPRESA - CATEGORIA DA CONTA INVÁLIDA",
    30: "ENTRADA BLOQUEADA - ENTRADAS BLOQUEADAS, CONTA SUSPENSA EM COBRANÇA",
    31: "AGÊNCIA/CONTA - CONTA NÃO TEM PERMISSÃO PARA PROTESTAR (CONTATE SEU GERENTE)",
    35: "VALOR DO IOF - IOF MAIOR QUE 5%",
    36: "QTDADE DE MOEDA - QUANTIDADE DE MOEDA INCOMPATÍVEL COM VALOR DO TÍTULO",
    37: "CNPJ/CPF DO PAGADOR - NÃO NUMÉRICO OU IGUAL A ZEROS",
    42: "NOSSO NÚMERO - NOSSO NÚMERO FORA DE FAIXA",
    52: "AG. COBRADORA - EMPRESA NÃO ACEITA BANCO CORRESPONDENTE",
    53: "AG. COBRADORA - EMPRESA NÃO ACEITA BANCO CORRESPONDENTE - COBRANÇA MENSAGEM",
    54: "DATA DE VENCTO - BANCO CORRESPONDENTE - TÍTULO COM VENCIMENTO INFERIOR A 15 DIAS",  # noqa
    55: "DEP/BCO CORRESP - CEP NÃO PERTENCE À DEPOSITÁRIA INFORMADA",
    56: "DT VENCTO/BCO CORRESP - VENCTO SUPERIOR A 180 DIAS DA DATA DE ENTRADA",
    57: "DATA DE VENCTO - CEP SÓ DEPOSITÁRIA BCO DO BRASIL COM VENCTO INFERIOR A 8 DIAS",  # noqa
    60: "ABATIMENTO - VALOR DO ABATIMENTO INVÁLIDO",
    61: "JUROS DE MORA - JUROS DE MORA MAIOR QUE O PERMITIDO",
    62: "DESCONTO - VALOR DO DESCONTO MAIOR QUE VALOR DO TÍTULO",
    63: "DESCONTO DE ANTECIPAÇÃO - VALOR DA IMPORTÂNCIA POR DIA DE DESCONTO (IDD) NÃO PERMITIDO",  # noqa
    64: "DATA DE EMISSÃO - DATA DE EMISSÃO DO TÍTULO INVÁLIDA",
    65: "TAXA FINANCTO - TAXA INVÁLIDA (VENDOR)",
    66: "DATA DE VENCTO - INVALIDA/FORA DE PRAZO DE OPERAÇÃO (MÍNIMO OU MÁXIMO)",
    67: "VALOR/QTIDADE - VALOR DO TÍTULO/QUANTIDADE DE MOEDA INVÁLIDO",
    68: "CARTEIRA - CARTEIRA INVÁLIDA OU NÃO CADASTRADA NO INTERCÂMBIO DA COBRANÇA",
    69: "CARTEIRA - CARTEIRA INVÁLIDA PARA TÍTULOS COM RATEIO DE CRÉDITO",
    70: "AGÊNCIA/CONTA - BENEFICIÁRIO NÃO CADASTRADO PARA FAZER RATEIO DE CRÉDITO",
    78: "AGÊNCIA/CONTA - DUPLICIDADE DE AGÊNCIA/CONTA BENEFICIÁRIA DO RATEIO DE CRÉDITO",  # noqa
    80: "AGÊNCIA/CONTA - QUANTIDADE DE CONTAS BENEFICIÁRIAS DO RATEIO MAIOR DO QUE O PERMITIDO (MÁXIMO DE 30 CONTAS POR TÍTULO)",  # noqa
    81: "AGÊNCIA/CONTA - CONTA PARA RATEIO DE CRÉDITO INVÁLIDA / NÃO PERTENCE AO ITAÚ",
    82: "DESCONTO/ABATI-MENTO - DESCONTO/ABATIMENTO NÃO PERMITIDO PARA TÍTULOS COM RATEIO DE CRÉDITO",  # noqa
    83: "VALOR DO TÍTULO - VALOR DO TÍTULO MENOR QUE A SOMA DOS VALORES ESTIPULADOS PARA RATEIO",  # noqa
    84: "AGÊNCIA/CONTA - AGÊNCIA/CONTA BENEFICIÁRIA DO RATEIO É A CENTRALIZADORA DE CRÉDITO DO BENEFICIÁRIO",  # noqa
    85: "AGÊNCIA/CONTA - AGÊNCIA/CONTA DO BENEFICIÁRIO É CONTRATUAL / RATEIO DE CRÉDITO NÃO PERMITIDO",  # noqa
    86: "TIPO DE VALOR - CÓDIGO DO TIPO DE VALOR INVÁLIDO / NÃO PREVISTO PARA TÍTULOS COM RATEIO DE CRÉDITO",  # noqa
    87: "AGÊNCIA/CONTA - REGISTRO TIPO 4 SEM INFORMAÇÃO DE AGÊNCIAS/CONTAS BENEFICIÁRIAS DO RATEIO",  # noqa
    90: "NRO DA LINHA - COBRANÇA MENSAGEM - NÚMERO DA LINHA DA MENSAGEM INVÁLIDO OU QUANTIDADE DE LINHAS EXCEDIDAS",  # noqa
    97: "SEM MENSAGEM - COBRANÇA MENSAGEM SEM MENSAGEM (SÓ DE CAMPOS FIXOS), PORÉM COM REGISTRO DO TIPO 7 OU 8",  # noqa
    98: "FLASH INVÁLIDO - REGISTRO MENSAGEM SEM FLASH CADASTRADO OU FLASH INFORMADO DIFERENTE DO CADASTRADO",  # noqa
    99: "FLASH INVÁLIDO - CONTA DE COBRANÇA COM FLASH CADASTRADO E SEM REGISTRO DE MENSAGEM CORRESPONDENTE",  # noqa
}


CODIGO_OCORRENCIAS_CNAB200 = {
    2: "ENTRADA CONFIRMADA COM POSSIBILIDADE DE MENSAGEM (NOTA 20 – TABELA 10)",  # noqa
    3: "ENTRADA REJEITADA (NOTA 20 – TABELA 1)",  # noqa
    4: "ALTERAÇÃO DE DADOS – NOVA ENTRADA OU ALTERAÇÃO/EXCLUSÃO DE DADOS ACATADA",  # noqa
    5: "ALTERAÇÃO DE DADOS – BAIXA",
    6: "LIQUIDAÇÃO NORMAL",
    7: "LIQUIDAÇÃO PARCIAL – COBRANÇA INTELIGENTE (B2B)",
    8: "LIQUIDAÇÃO EM CARTÓRIO",
    9: "BAIXA SIMPLES",
    10: "BAIXA POR TER SIDO LIQUIDADO",
    11: "EM SER (SÓ NO RETORNO MENSAL)",
    12: "ABATIMENTO CONCEDIDO",
    13: "ABATIMENTO CANCELADO",
    14: "VENCIMENTO ALTERADO",
    15: "BAIXAS REJEITADAS (NOTA 20 – TABELA 4)",
    16: "INSTRUÇÕES REJEITADAS (NOTA 20 – TABELA 3)",
    17: "ALTERAÇÃO/EXCLUSÃO DE DADOS REJEITADOS (NOTA 20 – TABELA 2)",
    18: "COBRANÇA CONTRATUAL – INSTRUÇÕES/ALTERAÇÕES REJEITADAS/PENDENTES (NOTA 20 – TABELA 5)",  # noqa
    19: "CONFIRMA RECEBIMENTO DE INSTRUÇÃO DE PROTESTO",
    20: "CONFIRMA RECEBIMENTO DE INSTRUÇÃO DE SUSTAÇÃO DE PROTESTO /TARIFA",
    21: "CONFIRMA RECEBIMENTO DE INSTRUÇÃO DE NÃO PROTESTAR",
    23: "TÍTULO ENVIADO A CARTÓRIO/TARIFA",
    24: "INSTRUÇÃO DE PROTESTO REJEITADA / SUSTADA / PENDENTE (NOTA 20 – TABELA 7)",  # noqa
    25: "ALEGAÇÕES DO PAGADOR (NOTA 20 – TABELA 6)",
    26: "TARIFA DE AVISO DE COBRANÇA",
    27: "TARIFA DE EXTRATO POSIÇÃO (B40X)",
    28: "TARIFA DE RELAÇÃO DAS LIQUIDAÇÕES",
    29: "TARIFA DE MANUTENÇÃO DE TÍTULOS VENCIDOS",
    30: "DÉBITO MENSAL DE TARIFAS (PARA ENTRADAS E BAIXAS)",
    32: "BAIXA POR TER SIDO PROTESTADO",
    33: "CUSTAS DE PROTESTO",
    34: "CUSTAS DE SUSTAÇÃO",
    35: "CUSTAS DE CARTÓRIO DISTRIBUIDOR",
    36: "CUSTAS DE EDITAL",
    37: "TARIFA DE EMISSÃO DE BOLETO/TARIFA DE ENVIO DE DUPLICATA",
    38: "TARIFA DE INSTRUÇÃO",
    39: "TARIFA DE OCORRÊNCIAS",
    40: "TARIFA MENSAL DE EMISSÃO DE BOLETO/TARIFA MENSAL DE ENVIO DE DUPLICATA",  # noqa
    41: "DÉBITO MENSAL DE TARIFAS – EXTRATO DE POSIÇÃO (B4EP/B4OX)",
    42: "DÉBITO MENSAL DE TARIFAS – OUTRAS INSTRUÇÕES",
    43: "DÉBITO MENSAL DE TARIFAS – MANUTENÇÃO DE TÍTULOS VENCIDOS",
    44: "DÉBITO MENSAL DE TARIFAS – OUTRAS OCORRÊNCIAS",
    45: "DÉBITO MENSAL DE TARIFAS – PROTESTO",
    46: "DÉBITO MENSAL DE TARIFAS – SUSTAÇÃO DE PROTESTO",
    47: "BAIXA COM TRANSFERÊNCIA PARA DESCONTO",
    48: "CUSTAS DE SUSTAÇÃO JUDICIAL",
    51: "TARIFA MENSAL REF A ENTRADAS BANCOS CORRESPONDENTES NA CARTEIRA",
    52: "TARIFA MENSAL BAIXAS NA CARTEIRA",
    53: "TARIFA MENSAL BAIXAS EM BANCOS CORRESPONDENTES NA CARTEIRA",
    54: "TARIFA MENSAL DE LIQUIDAÇÕES NA CARTEIRA",
    55: "TARIFA MENSAL DE LIQUIDAÇÕES EM BANCOS CORRESPONDENTES NA CARTEIRA",
    56: "CUSTAS DE IRREGULARIDADE",
    57: "INSTRUÇÃO CANCELADA (NOTA 20 – TABELA 8)",
    59: "BAIXA POR CRÉDITO EM C/C ATRAVÉS DO SISPAG",
    60: "ENTRADA REJEITADA CARNÊ (NOTA 20 – TABELA 1)",
    61: "TARIFA EMISSÃO AVISO DE MOVIMENTAÇÃO DE TÍTULOS (2154)",
    62: "DÉBITO MENSAL DE TARIFA – AVISO DE MOVIMENTAÇÃO DE TÍTULOS (2154)",
    63: "TÍTULO SUSTADO JUDICIALMENTE",
    64: "ENTRADA CONFIRMADA COM RATEIO DE CRÉDITO",
    65: "PAGAMENTO COM CHEQUE – AGUARDANDO COMPENSAÇÃO",
    69: "CHEQUE DEVOLVIDO (NOTA 20 – TABELA 9)",
    71: "ENTRADA REGISTRADA, AGUARDANDO AVALIAÇÃO",
    72: "BAIXA POR CRÉDITO EM C/C ATRAVÉS DO SISPAG SEM TÍTULO CORRESPONDENTE",
    73: "CONFIRMAÇÃO DE ENTRADA NA COBRANÇA SIMPLES – ENTRADA NÃO ACEITA NA COBRANÇA CONTRATUAL",  # noqa
    74: "INSTRUÇÃO DE NEGATIVAÇÃO EXPRESSA REJEITADA (NOTA 20 – TABELA 11)",
    75: "CONFIRMAÇÃO DE RECEBIMENTO DE INSTRUÇÃO DE ENTRADA EM NEGATIVAÇÃO EXPRESSA",  # noqa
    76: "CHEQUE COMPENSADO",
    77: "CONFIRMAÇÃO DE RECEBIMENTO DE INSTRUÇÃO DE EXCLUSÃO DE ENTRADA EM NEGATIVAÇÃO EXPRESSA",  # noqa
    78: "CONFIRMAÇÃO DE RECEBIMENTO DE INSTRUÇÃO DE CANCELAMENTO DE NEGATIVAÇÃO EXPRESSA",  # noqa
    79: "NEGATIVAÇÃO EXPRESSA INFORMACIONAL (NOTA 20 – TABELA 12)",
    80: "CONFIRMAÇÃO DE ENTRADA EM NEGATIVAÇÃO EXPRESSA – TARIFA",
    82: "CONFIRMAÇÃO DO CANCELAMENTO DE NEGATIVAÇÃO EXPRESSA – TARIFA",
    83: "CONFIRMAÇÃO DE EXCLUSÃO DE ENTRADA EM NEGATIVAÇÃO EXPRESSA POR LIQUIDAÇÃO – TARIFA",  # noqa
    85: "TARIFA POR BOLETO (ATÉ 03 ENVIOS) COBRANÇA ATIVA ELETRÔNICA",
    86: "TARIFA EMAIL COBRANÇA ATIVA ELETRÔNICA",
    87: "TARIFA SMS COBRANÇA ATIVA ELETRÔNICA",
    88: "TARIFA MENSAL POR BOLETO (ATÉ 03 ENVIOS) COBRANÇA ATIVA ELETRÔNICA",
    89: "TARIFA MENSAL EMAIL COBRANÇA ATIVA ELETRÔNICA",
    90: "TARIFA MENSAL SMS COBRANÇA ATIVA ELETRÔNICA",
    91: "TARIFA MENSAL DE EXCLUSÃO DE ENTRADA DE NEGATIVAÇÃO EXPRESSA",
    92: "TARIFA MENSAL DE CANCELAMENTO DE NEGATIVAÇÃO EXPRESSA",
    93: "TARIFA MENSAL DE EXCLUSÃO DE NEGATIVAÇÃO EXPRESSA POR LIQUIDAÇÃO",
}

STR_EVENTO_FORMAT = "%d%m%y"
