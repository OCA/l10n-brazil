# © 2012 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


SEQUENCIAL_EMPRESA = "0"
SEQUENCIAL_FATURA = "1"
SEQUENCIAL_CARTEIRA = "2"


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
LIQUIDACAO_TITULOS_PROPRIO_BANCO = (
    "30",
    "30 - Liquidação de Títulos do Próprio Banco",
)
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

CODIGO_INSTRUCAO_MOVIMENTO = [
    ("0", "00 - Inclusão de Registro Detalhe Liberado"),
    ("9", "09 - Inclusão do Registro Detalhe Bloqueado"),
    ("10", "10 - Alteração do Pagamento Liberado para Bloqueado (Bloqueio)"),
    ("11", "11 - Alteração do Pagamento Bloqueado para Liberado (Liberação)"),
    ("17", "17 - Alteração do Valor do Título"),
    ("19", "19 - Alteração da Data de Pagamento"),
    ("23", "23 - Pagamento Direto ao Fornecedor - Baixar"),
    ("25", "25 - Manutenção em Carteira - Não Pagar"),
    ("27", "27 - Retirada de Carteira - Não Pagar"),
    (
        "33",
        "33 - Estorno por Devolução da Câmara Centralizadora "
        "(somente para Tipo de Movimento = '3')",
    ),
    ("40", "40 - Alegação do Pagador"),
    ("99", "99 - Exclusão do Registro Detalhe Incluído Anteriormente"),
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
