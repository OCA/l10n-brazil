# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals


TIPO_ORDEM_PAGAMENTO_BOLETO = 'boleto'
#TIPO_ORDEM_PAGAMENTO_DEBITO_AUTOMATICO = 'debito_automatico'
TIPO_ORDEM_PAGAMENTO_PAGAMENTO = 'pagamento'
TIPO_ORDEM_PAGAMENTO_FOLHA = 'folha'

TIPO_ORDEM_PAGAMENTO = [
    (TIPO_ORDEM_PAGAMENTO_BOLETO, 'Cobrança / Boleto'),
    #(TIPO_ORDEM_PAGAMENTO_DEBITO_AUTOMATICO, 'Cobrança / Débito automático'),
    (TIPO_ORDEM_PAGAMENTO_PAGAMENTO, 'Pagamento de contas/impostos'),
    (TIPO_ORDEM_PAGAMENTO_FOLHA, 'Folha de Pagamento'),
]

TIPO_SERVICO_COBRANCA = '01'
TIPO_SERVICO_BOLETO_PAGAMENTO_ELETRONICO = '03'
TIPO_SERVICO_CONCILIACAO_BANCARIA = '04'
TIPO_SERVICO_DEBITOS = '05'
TIPO_SERVICO_CUSTODIA_CHEQUES = '06'
TIPO_SERVICO_GESTAO_CAIXA = '07'
TIPO_SERVICO_CONSULTA_INFORMACAO_MARGEM = '08'
TIPO_SERVICO_AVERBACAO_CONSIGNACAO_RETENCAO = '09'
TIPO_SERVICO_PAGAMENTO_DIVIDENDOS = '10'
TIPO_SERVICO_MANUTENCAO_CONSIGNACAO = '11'
TIPO_SERVICO_CONSIGNACAO_PARCELAS = '12'
TIPO_SERVICO_GLOSA_CONSIGNACAO = '13'
TIPO_SERVICO_CONSULTA_TRIBUTOS_PAGAR = '14'
TIPO_SERVICO_PAGAMENTO_FORNECEDOR = '20'
TIPO_SERVICO_PAGAMENTO_CONTAS_TRIBUTOS_IMPOSTOS = '22'
TIPO_SERVICO_INTEROPERABILIDADE_CONTAS = '23'
TIPO_SERVICO_COMPROR = '25'
TIPO_SERVICO_COMPROR_ROTATIVO = '26'
TIPO_SERVICO_ALEGACAO_PAGADOR = '29'
TIPO_SERVICO_PAGAMENTO_SALARIOS = '30'
TIPO_SERVICO_PAGAMENTO_HONORARIOS = '32'
TIPO_SERVICO_PAGAMENTO_BOLSA_AUXILIO = '33'
TIPO_SERVICO_PAGAMENTO_PREBENDA = '34'
TIPO_SERVICO_VENDOR = '40'
TIPO_SERVICO_VENDOR_TERMO = '41'
TIPO_SERVICO_PAGAMENTO_SINISTROS_SEGURADOS = '50'
TIPO_SERVICO_PAGAMENTO_DESPESAS_VIAJANTE = '60'
TIPO_SERVICO_PAGAMENTO_AUTORIZADO = '70'
TIPO_SERVICO_PAGAMENTO_CREDENCIADOS = '75'
TIPO_SERVICO_PAGAMENTO_REMUNERACAO = '77'
TIPO_SERVICO_PAGAMENTO_REPRESENTANTES = '80'
TIPO_SERVICO_PAGAMENTO_BENEFICIOS = '90'
TIPO_SERVICO_PAGAMENTOS_DIVERSOS = '98'

TIPO_SERVICO = [
    (TIPO_SERVICO_COBRANCA,
        '01 - Cobrança'),
    (TIPO_SERVICO_BOLETO_PAGAMENTO_ELETRONICO,
        '03 - Boleto de Pagamento Eletrônico'),
    (TIPO_SERVICO_CONCILIACAO_BANCARIA,
        '04 - Conciliação Bancária'),
    (TIPO_SERVICO_DEBITOS,
        '05 - Débitos'),
    (TIPO_SERVICO_CUSTODIA_CHEQUES,
        '06 - Custódia de Cheques'),
    (TIPO_SERVICO_GESTAO_CAIXA,
        '07 - Gestão de Caixa'),
    (TIPO_SERVICO_CONSULTA_INFORMACAO_MARGEM,
        '08 - Consulta/Informação Margem'),
    (TIPO_SERVICO_AVERBACAO_CONSIGNACAO_RETENCAO,
        '09 - Averbação da Consignação/Retenção'),
    (TIPO_SERVICO_PAGAMENTO_DIVIDENDOS,
        '10 - Pagamento Dividendos'),
    (TIPO_SERVICO_MANUTENCAO_CONSIGNACAO,
        '11 - Manutenção da Consignação'),
    (TIPO_SERVICO_CONSIGNACAO_PARCELAS,
        '12 - Consignação de Parcelas'),
    (TIPO_SERVICO_GLOSA_CONSIGNACAO,
        '13 - Glosa da Consignação (INSS)'),
    (TIPO_SERVICO_CONSULTA_TRIBUTOS_PAGAR,
        '14 - Consulta de Tributos a Pagar'),
    (TIPO_SERVICO_PAGAMENTO_FORNECEDOR,
        '20 - Pagamento a Fornecedor'),
    (TIPO_SERVICO_PAGAMENTO_CONTAS_TRIBUTOS_IMPOSTOS,
        '22 - Pagamento de Contas, Tributos e Impostos'),
    (TIPO_SERVICO_INTEROPERABILIDADE_CONTAS,
        '23 - Interoperabilidade entre Contas de Instituições de Pagamentos'),
    (TIPO_SERVICO_COMPROR,
        '25 - Compror'),
    (TIPO_SERVICO_COMPROR_ROTATIVO,
        '26 - Compror Rotativo'),
    (TIPO_SERVICO_ALEGACAO_PAGADOR,
        '29 - Alegação do Pagador'),
    (TIPO_SERVICO_PAGAMENTO_SALARIOS,
        '30 - Pagamento de Salários'),
    (TIPO_SERVICO_PAGAMENTO_HONORARIOS,
        '32 - Pagamento de Honorários'),
    (TIPO_SERVICO_PAGAMENTO_BOLSA_AUXILIO,
        '33 - Pagamento de Bolsa Auxílio'),
    (TIPO_SERVICO_PAGAMENTO_PREBENDA,
        '34 - Pagamento de Prebenda (remuneração a padres e sacerdotes)'),
    (TIPO_SERVICO_VENDOR,
        '40 - Vendor'),
    (TIPO_SERVICO_VENDOR_TERMO,
        '41 - Vendor a Termo'),
    (TIPO_SERVICO_PAGAMENTO_SINISTROS_SEGURADOS,
        '50 - Pagamento de Sinistros Segurados'),
    (TIPO_SERVICO_PAGAMENTO_DESPESAS_VIAJANTE,
        '60 - Pagamento de Despesas de Viajante em Trânsito'),
    (TIPO_SERVICO_PAGAMENTO_AUTORIZADO,
        '70 - Pagamento Autorizado'),
    (TIPO_SERVICO_PAGAMENTO_CREDENCIADOS,
        '75 - Pagamento a Credenciados'),
    (TIPO_SERVICO_PAGAMENTO_REMUNERACAO,
        '77 - Pagamento de Remuneração'),
    (TIPO_SERVICO_PAGAMENTO_REPRESENTANTES,
        '80 - Pagamento de Representantes / Vendedores Autorizados'),
    (TIPO_SERVICO_PAGAMENTO_BENEFICIOS,
        '90 - Pagamento de Benefícios'),
    (TIPO_SERVICO_PAGAMENTOS_DIVERSOS,
        '98 - Pagamentos Diversos'),
]

TIPO_SERVICO_COMPLEMENTO_CREDITO_EM_CONTA = '01'
TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_ALUGUEL = '02'
TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_DUPLICATA_TITULOS = '03'
TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_DIVIDENDOS = '04'
TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_MENSALIDADE_ESCOLAR = '05'
TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_SALARIOS = '06'
TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_FORNECEDORES = '07'
TIPO_SERVICO_COMPLEMENTO_OPERACOES_CAMBIOS_FUNDOS_BOLSA = '08'
TIPO_SERVICO_COMPLEMENTO_REPASSE_ARRECADACAO = '09'
TIPO_SERVICO_COMPLEMENTO_TRANSFERECIA_INTERNACIONAL_EM_REAL = '10'
TIPO_SERVICO_COMPLEMENTO_DOC_POUPANCA = '11'
TIPO_SERVICO_COMPLEMENTO_DOC_DEPOSITO_JUDICIAL = '12'
TIPO_SERVICO_COMPLEMENTO_OUTROS = '13'
TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_BOLSA_AUXILIO = '16'
TIPO_SERVICO_COMPLEMENTO_REMUNERACAO_COOPERADO = '17'
TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_HONORARIOS = '18'
TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_PREBENDA = '19'

TIPO_SERVICO_COMPLEMENTO = [
    (TIPO_SERVICO_COMPLEMENTO_CREDITO_EM_CONTA,
        '01 - Crédito em Conta'),
    (TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_ALUGUEL,
        '02 - Pagamento de Aluguel/Condomínio'),
    (TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_DUPLICATA_TITULOS,
        '03 - Pagamento de Duplicata/Títulos'),
    (TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_DIVIDENDOS,
        '04 - Pagamento de Dividendos'),
    (TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_MENSALIDADE_ESCOLAR,
        '05 - Pagamento de Mensalidade Escolar'),
    (TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_SALARIOS,
        '06 - Pagamento de Salários'),
    (TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_FORNECEDORES,
        '07 - Pagamento a Fornecedores'),
    (TIPO_SERVICO_COMPLEMENTO_OPERACOES_CAMBIOS_FUNDOS_BOLSA,
        '08 - Operações de Câmbios/Fundos/Bolsa de Valores'),
    (TIPO_SERVICO_COMPLEMENTO_REPASSE_ARRECADACAO,
        '09 - Repasse de Arrecadação/Pagamento de Tributos'),
    (TIPO_SERVICO_COMPLEMENTO_TRANSFERECIA_INTERNACIONAL_EM_REAL,
        '10 - Transferência Internacional em Real'),
    (TIPO_SERVICO_COMPLEMENTO_DOC_POUPANCA,
        '11 - DOC para Poupança'),
    (TIPO_SERVICO_COMPLEMENTO_DOC_DEPOSITO_JUDICIAL,
        '12 - DOC para Depósito Judicial'),
    (TIPO_SERVICO_COMPLEMENTO_OUTROS,
        '13 - Outros'),
    (TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_BOLSA_AUXILIO,
        '16 - Pagamento de Bolsa Auxílio'),
    (TIPO_SERVICO_COMPLEMENTO_REMUNERACAO_COOPERADO,
        '17 - Remuneração a Cooperado'),
    (TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_HONORARIOS,
        '18 - Pagamento de Honorários'),
    (TIPO_SERVICO_COMPLEMENTO_PAGAMENTO_PREBENDA,
        '19 - Pagamento de Prebenda (remuneração a padres e sacerdotes)'),
]

FORMA_LANCAMENTO_CREDITO_CONTA_CORRENTE_SALARIO = '01'
FORMA_LANCAMENTO_CHEQUE_PAGAMENTO_ADMINISTRATIVO = '02'
FORMA_LANCAMENTO_DOC_TED = '03'
FORMA_LANCAMENTO_CARTAO_SALARIO = '04'
FORMA_LANCAMENTO_CREDITO_CONTA_POUPANCA = '05'
FORMA_LANCAMENTO_OP_A_DISPOSICAO = '10'
FORMA_LANCAMENTO_PAGAMENTO_CONTAS_TRIBUTOS_CODIGO_BARRAS = '11'
FORMA_LANCAMENTO_TRIBUTO_DARF_NORMAL = '16'
FORMA_LANCAMENTO_TRIBUTO_GPS = '17'
FORMA_LANCAMENTO_TRIBUTO_DARF_SIMPLES = '18'
FORMA_LANCAMENTO_TRIBUTO_IPTU_PREFEITURAS = '19'
FORMA_LANCAMENTO_PAGAMENTO_AUTENTICACAO = '20'
FORMA_LANCAMENTO_TRIBUTO_DARJ = '21'
FORMA_LANCAMENTO_TRIBUTO_GARE_SP_ICMS = '22'
FORMA_LANCAMENTO_TRIBUTO_GARE_SP_DR = '23'
FORMA_LANCAMENTO_TRIBUTO_GARE_SP_ITCMD = '24'
FORMA_LANCAMENTO_TRIBUTO_IPVA = '25'
FORMA_LANCAMENTO_TRIBUTO_LICENCIAMENTO = '26'
FORMA_LANCAMENTO_TRIBUTO_DPVAT = '27'
FORMA_LANCAMENTO_LIQUIDACAO_TITULOS_PROPRIO_BANCO = '30'
FORMA_LANCAMENTO_PAGAMENTO_TITULOS_OUTROS_BANCOS = '31'
FORMA_LANCAMENTO_EXTRATO_CONTA_CORRENTE = '40'
FORMA_LANCAMENTO_TED_OUTRA_TITULARIDADE = '41'
FORMA_LANCAMENTO_TED_MESMA_TITULARIDADE = '43'
FORMA_LANCAMENTO_TED_TRANSFERENCIA_CONTA_INVESTIMENTO = '44'
FORMA_LANCAMENTO_DEBITO_CONTA_CORRENTE = '50'
FORMA_LANCAMENTO_EXTRATO_GESTAO_CAIXA = '70'
FORMA_LANCAMENTO_DEPOSITO_JUDICIAL_CONTA_CORRENTE = '71'
FORMA_LANCAMENTO_DEPOSITO_JUDICIAL_POUPANCA = '72'
FORMA_LANCAMENTO_EXTRATO_CONTA_INVESTIMENTO = '73'

FORMA_LANCAMENTO = [
    (FORMA_LANCAMENTO_CREDITO_CONTA_CORRENTE_SALARIO,
        '01 - Crédito em Conta Corrente/Salário'),
    (FORMA_LANCAMENTO_CHEQUE_PAGAMENTO_ADMINISTRATIVO,
        '02 - Cheque Pagamento/Administrativo'),
    (FORMA_LANCAMENTO_DOC_TED,
        '03 - DOC/TED'),
    (FORMA_LANCAMENTO_CARTAO_SALARIO,
        '04 - Cartão Salário (somente para Tipo de Serviço = "30")'),
    (FORMA_LANCAMENTO_CREDITO_CONTA_POUPANCA,
        '05 - Crédito em Conta Poupança'),
    (FORMA_LANCAMENTO_OP_A_DISPOSICAO,
        '10 - OP à Disposição'),
    (FORMA_LANCAMENTO_PAGAMENTO_CONTAS_TRIBUTOS_CODIGO_BARRAS,
        '11 - Pagamento de Contas e Tributos com Código de Barras'),
    (FORMA_LANCAMENTO_TRIBUTO_DARF_NORMAL,
        '16 - Tributo - DARF Normal'),
    (FORMA_LANCAMENTO_TRIBUTO_GPS,
        '17 - Tributo - GPS (Guia da Previdência Social)'),
    (FORMA_LANCAMENTO_TRIBUTO_DARF_SIMPLES,
        '18 - Tributo - DARF Simples'),
    (FORMA_LANCAMENTO_TRIBUTO_IPTU_PREFEITURAS,
        '19 - Tributo - IPTU – Prefeituras'),
    (FORMA_LANCAMENTO_PAGAMENTO_AUTENTICACAO,
        '20 - Pagamento com Autenticação'),
    (FORMA_LANCAMENTO_TRIBUTO_DARJ,
        '21 - Tributo – DARJ'),
    (FORMA_LANCAMENTO_TRIBUTO_GARE_SP_ICMS,
        '22 - Tributo - GARE-SP ICMS'),
    (FORMA_LANCAMENTO_TRIBUTO_GARE_SP_DR,
        '23 - Tributo - GARE-SP DR'),
    (FORMA_LANCAMENTO_TRIBUTO_GARE_SP_ITCMD,
        '24 - Tributo - GARE-SP ITCMD'),
    (FORMA_LANCAMENTO_TRIBUTO_IPVA,
        '25 - Tributo - IPVA'),
    (FORMA_LANCAMENTO_TRIBUTO_LICENCIAMENTO,
        '26 - Tributo - Licenciamento'),
    (FORMA_LANCAMENTO_TRIBUTO_DPVAT,
        '27 - Tributo – DPVAT'),
    (FORMA_LANCAMENTO_LIQUIDACAO_TITULOS_PROPRIO_BANCO,
        '30 - Liquidação de Títulos do Próprio Banco'),
    (FORMA_LANCAMENTO_PAGAMENTO_TITULOS_OUTROS_BANCOS,
        '31 - Pagamento de Títulos de Outros Bancos'),
    (FORMA_LANCAMENTO_EXTRATO_CONTA_CORRENTE,
        '40 - Extrato de Conta Corrente'),
    (FORMA_LANCAMENTO_TED_OUTRA_TITULARIDADE,
        '41 - TED – Outra Titularidade'),
    (FORMA_LANCAMENTO_TED_MESMA_TITULARIDADE,
        '43 - TED – Mesma Titularidade'),
    (FORMA_LANCAMENTO_TED_TRANSFERENCIA_CONTA_INVESTIMENTO,
        '44 - TED para Transferência de Conta Investimento'),
    (FORMA_LANCAMENTO_DEBITO_CONTA_CORRENTE,
        '50 - Débito em Conta Corrente'),
    (FORMA_LANCAMENTO_EXTRATO_GESTAO_CAIXA,
        '70 - Extrato para Gestão de Caixa'),
    (FORMA_LANCAMENTO_DEPOSITO_JUDICIAL_CONTA_CORRENTE,
        '71 - Depósito Judicial em Conta Corrente'),
    (FORMA_LANCAMENTO_DEPOSITO_JUDICIAL_POUPANCA,
        '72 - Depósito Judicial em Poupança'),
    (FORMA_LANCAMENTO_EXTRATO_CONTA_INVESTIMENTO,
         '73 - Extrato de Conta Investimento'),
]

# Codigo adotado pelo Banco Central para identificar a
# finalidade da TED. Utitilizar os
# códigos de finalidade cliente, disponíveis no site do Banco Central do Brasil
# (www.bcb.gov.br), Sistema de Pagamentos Brasileiro,
# Transferência de Arquivos,
# Dicionários de Domínios para o SPB.
CODIGO_FINALIDADE_TED = [
    ('    ', 'Padrão')
]

AVISO_FAVORECIDO_NAO_EMITE = '0'
AVISO_FAVORECIDO_EMITE_AO_REMETENTE = '2'
AVISO_FAVORECIDO_EMITE_AO_FAVORECIDO = '5'
AVISO_FAVORECIDO_EMITE_AO_REMETENTE_E_FAVORECIDO = '6'
AVISO_FAVORECIDO_EMITE_AO_FAVORECIDO_E_2_VIAS_AO_REMETENTE = '7'

AVISO_FAVORECIDO = [
    (AVISO_FAVORECIDO_NAO_EMITE,
        '0 - Não emite'),
    (AVISO_FAVORECIDO_EMITE_AO_REMETENTE,
        '2 - Emite aviso somente ao remetente'),
    (AVISO_FAVORECIDO_EMITE_AO_FAVORECIDO,
        '5 - Emite aviso somente ao favorecido'),
    (AVISO_FAVORECIDO_EMITE_AO_REMETENTE_E_FAVORECIDO,
        '6 - Emite aviso ao remetente e ao favorecido'),
    (AVISO_FAVORECIDO_EMITE_AO_FAVORECIDO_E_2_VIAS_AO_REMETENTE,
        '7 - Emite aviso ao favorecido e 2 vias ao remetente'),
]

FORMA_PAGAMENTO = [
    ('01', '01 - Débito em Conta Corrente'),
    ('02', '02 - Débito Empréstimo/Financiamento'),
    ('03', '03 - Débito Cartão de Crédito'),
]

TIPO_MOVIMENTO = [
    ('0', '0 - Inclusão'),
    ('1', '1 - Consulta'),
    ('2', '2 - Suspensão'),
    ('3', '3 - Estorno (somente para retorno)'),
    ('4', '4 - Reativação'),
    ('5', '5 - Alteração'),
    ('7', '7 - Liquidação'),
    ('9', '9 - Exclusão'),
]

INSTRUCAO_MOVIMENTO = [
    ('00', '00 - Inclusão de Registro Detalhe Liberado'),
    ('09', '09 - Inclusão do Registro Detalhe Bloqueado'),
    ('10', '10 - Alteração do Pagamento Liberado para Bloqueado (Bloqueio)'),
    ('11', '11 - Alteração do Pagamento Bloqueado para Liberado (Liberação)'),
    ('17', '17 - Alteração do Valor do Título'),
    ('19', '19 - Alteração da Data de Pagamento'),
    ('23', '23 - Pagamento Direto ao Fornecedor - Baixar'),
    ('25', '25 - Manutenção em Carteira - Não Pagar'),
    ('27', '27 - Retirada de Carteira - Não Pagar'),
    ('33', '33 - Estorno por Devolução da Câmara Centralizadora '
           '(somente para Tipo de Movimento = "3")'),
    ('40', '40 - Alegação do Pagador'),
    ('99', '99 - Exclusão do Registro Detalhe Incluído Anteriormente'),
]
INSTRUCAO_MOVIMENTO_INCLUSAO_DETALHE_LIBERADO = '00'

CODIGO_OCORRENCIAS = [
    ('00', '00 - Crédito ou Débito Efetivado'),
    ('01', '01 - Insuficiência de Fundos - Débito Não Efetuado'),
    ('02', '02 - Crédito ou Débito Cancelado pelo Pagador/Credor'),
    ('03', '03 - Débito Autorizado pela Agência - Efetuado'),
    ('AA', 'AA - Controle Inválido'),
    ('AB', 'AB - Tipo de Operação Inválido'),
    ('AC', 'AC - Tipo de Serviço Inválido'),
    ('AD', 'AD - Forma de Lançamento Inválida'),
    ('AE', 'AE - Tipo/Número de Inscrição Inválido'),
    ('AF', 'AF - Código de Convênio Inválido'),
    ('AG', 'AG - Agência/Conta Corrente/DV Inválido'),
    ('AH', 'AH - Nº Seqüencial do Registro no Lote Inválido'),
    ('AI', 'AI - Código de Segmento de Detalhe Inválido'),
    ('AJ', 'AJ - Tipo de Movimento Inválido'),
    ('AK', 'AK - Código da Câmara de Compensação do Banco'
           ' Favorecido/Depositário Inválido'),
    ('AL', 'AL - Código do Banco Favorecido, Instituição de Pagamento'
           ' ou Depositário Inválido'),
    ('AM', 'AM - Agência Mantenedora da Conta Corrente do'
           ' Favorecido Inválida'),
    ('AN', 'AN - Conta Corrente/DV/Conta de Pagamento do'
           ' Favorecido Inválido'),
    ('AO', 'AO - Nome do Favorecido Não Informado'),
    ('AP', 'AP - Data Lançamento Inválido'),
    ('AQ', 'AQ - Tipo/Quantidade da Moeda Inválido'),
    ('AR', 'AR - Valor do Lançamento Inválido'),
    ('AS', 'AS - Aviso ao Favorecido - Identificação Inválida'),
    ('AT', 'AT - Tipo/Número de Inscrição do Favorecido Inválido'),
    ('AU', 'AU - Logradouro do Favorecido Não Informado'),
    ('AV', 'AV - Nº do Local do Favorecido Não Informado'),
    ('AW', 'AW - Cidade do Favorecido Não Informada'),
    ('AX', 'AX - CEP/Complemento do Favorecido Inválido'),
    ('AY', 'AY - Sigla do Estado do Favorecido Inválida'),
    ('AZ', 'AZ - Código/Nome do Banco Depositário Inválido'),
    ('BA', 'BA - Código/Nome da Agência Depositária Não Informado'),
    ('BB', 'BB - Seu Número Inválido'),
    ('BC', 'BC - Nosso Número Inválido'),
    ('BD', 'BD - Inclusão Efetuada com Sucesso'),
    ('BE', 'BE - Alteração Efetuada com Sucesso'),
    ('BF', 'BF - Exclusão Efetuada com Sucesso'),
    ('BG', 'BG - Agência/Conta Impedida Legalmente'),
    ('BH', 'BH - Empresa não pagou salário'),
    ('BI', 'BI - Falecimento do mutuário'),
    ('BJ', 'BJ - Empresa não enviou remessa do mutuário'),
    ('BK', 'BK - Empresa não enviou remessa no vencimento'),
    ('BL', 'BL - Valor da parcela inválida'),
    ('BM', 'BM - Identificação do contrato inválida'),
    ('BN', 'BN - Operação de Consignação Incluída com Sucesso'),
    ('BO', 'BO - Operação de Consignação Alterada com Sucesso'),
    ('BP', 'BP - Operação de Consignação Excluída com Sucesso'),
    ('BQ', 'BQ - Operação de Consignação Liquidada com Sucesso'),
    ('BR', 'BR - Reativação Efetuada com Sucesso'),
    ('BS', 'BS - Suspensão Efetuada com Sucesso'),
    ('CA', 'CA - Código de Barras - Código do Banco Inválido'),
    ('CB', 'CB - Código de Barras - Código da Moeda Inválido'),
    ('CC', 'CC - Código de Barras - Dígito Verificador Geral Inválido'),
    ('CD', 'CD - Código de Barras - Valor do Título Inválido'),
    ('CE', 'CE - Código de Barras - Campo Livre Inválido'),
    ('CF', 'CF - Valor do Documento Inválido'),
    ('CG', 'CG - Valor do Abatimento Inválido'),
    ('CH', 'CH - Valor do Desconto Inválido'),
    ('CI', 'CI - Valor de Mora Inválido'),
    ('CJ', 'CJ - Valor da Multa Inválido'),
    ('CK', 'CK - Valor do IR Inválido'),
    ('CL', 'CL - Valor do ISS Inválido'),
    ('CM', 'CM - Valor do IOF Inválido'),
    ('CN', 'CN - Valor de Outras Deduções Inválido'),
    ('CO', 'CO - Valor de Outros Acréscimos Inválido'),
    ('CP', 'CP - Valor do INSS Inválido'),
    ('HA', 'HA - Lote Não Aceito'),
    ('HB', 'HB - Inscrição da Empresa Inválida para o Contrato'),
    ('HC', 'HC - Convênio com a Empresa Inexistente/Inválido'
           ' para o Contrato'),
    ('HD', 'HD - Agência/Conta Corrente da Empresa Inexistente/Inválido'
           ' para o Contrato'),
    ('HE', 'HE - Tipo de Serviço Inválido para o Contrato'),
    ('HF', 'HF - Conta Corrente da Empresa com Saldo Insuficiente'),
    ('HG', 'HG - Lote de Serviço Fora de Seqüência'),
    ('HH', 'HH - Lote de Serviço Inválido'),
    ('HI', 'HI - Arquivo não aceito'),
    ('HJ', 'HJ - Tipo de Registro Inválido'),
    ('HK', 'HK - Código Remessa / Retorno Inválido'),
    ('HL', 'HL - Versão de layout inválida'),
    ('HM', 'HM - Mutuário não identificado'),
    ('HN', 'HN - Tipo do beneficio não permite empréstimo'),
    ('HO', 'HO - Beneficio cessado/suspenso'),
    ('HP', 'HP - Beneficio possui representante legal'),
    ('HQ', 'HQ - Beneficio é do tipo PA (Pensão alimentícia)'),
    ('HR', 'HR - Quantidade de contratos permitida excedida'),
    ('HS', 'HS - Beneficio não pertence ao Banco informado'),
    ('HT', 'HT - Início do desconto informado já ultrapassado'),
    ('HU', 'HU - Número da parcela inválida'),
    ('HV', 'HV - Quantidade de parcela inválida'),
    ('HW', 'HW - Margem consignável excedida para o mutuário dentro'
           ' do prazo do contrato'),
    ('HX', 'HX - Empréstimo já cadastrado'),
    ('HY', 'HY - Empréstimo inexistente'),
    ('HZ', 'HZ - Empréstimo já encerrado'),
    ('H1', 'H1 - Arquivo sem trailer'),
    ('H2', 'H2 - Mutuário sem crédito na competência'),
    ('H3', 'H3 - Não descontado – outros motivos'),
    ('H4', 'H4 - Retorno de Crédito não pago'),
    ('H5', 'H5 - Cancelamento de empréstimo retroativo'),
    ('H6', 'H6 - Outros Motivos de Glosa'),
    ('H7', 'H7 - Margem consignável excedida para o mutuário acima'
           ' do prazo do contrato'),
    ('H8', 'H8 - Mutuário desligado do empregador'),
    ('H9', 'H9 - Mutuário afastado por licença'),
    ('IA', 'IA - Primeiro nome do mutuário diferente do primeiro nome'
           ' do movimento do censo ou diferente da base de Titular'
           ' do Benefício'),
    ('IB', 'IB - Benefício suspenso/cessado pela APS ou Sisobi'),
    ('IC', 'IC - Benefício suspenso por dependência de cálculo'),
    ('ID', 'ID - Benefício suspenso/cessado pela inspetoria/auditoria'),
    ('IE', 'IE - Benefício bloqueado para empréstimo pelo beneficiário'),
    ('IF', 'IF - Benefício bloqueado para empréstimo por TBM'),
    ('IG', 'IG - Benefício está em fase de concessão de PA ou desdobramento'),
    ('IH', 'IH - Benefício cessado por óbito'),
    ('II', 'II - Benefício cessado por fraude'),
    ('IJ', 'IJ - Benefício cessado por concessão de outro benefício'),
    ('IK', 'IK - Benefício cessado: estatutário transferido'
           ' para órgão de origem'),
    ('IL', 'IL - Empréstimo suspenso pela APS'),
    ('IM', 'IM - Empréstimo cancelado pelo banco'),
    ('IN', 'IN - Crédito transformado em PAB'),
    ('IO', 'IO - Término da consignação foi alterado'),
    ('IP', 'IP - Fim do empréstimo ocorreu durante período'
           ' de suspensão ou concessão'),
    ('IQ', 'IQ - Empréstimo suspenso pelo banco'),
    ('IR', 'IR - Não averbação de contrato – quantidade de'
           ' parcelas/competências informadas ultrapassou a data limite'
           ' da extinção de cota do dependente titular de benefícios'),
    ('TA', 'TA - Lote Não Aceito - Totais do Lote com Diferença'),
    ('YA', 'YA - Título Não Encontrado'),
    ('YB', 'YB - Identificador Registro Opcional Inválido'),
    ('YC', 'YC - Código Padrão Inválido'),
    ('YD', 'YD - Código de Ocorrência Inválido'),
    ('YE', 'YE - Complemento de Ocorrência Inválido'),
    ('YF', 'YF - Alegação já Informada'),
    ('ZA', 'ZA - Agência / Conta do Favorecido Substituída'),
    ('ZB', 'ZB - Divergência entre o primeiro e último nome do beneficiário'
           ' versus primeiro e último nome na Receita Federal'),
    ('ZC', 'ZC - Confirmação de Antecipação de Valor'),
    ('ZD', 'ZD - Antecipação parcial de valor'),
    ('ZE', 'ZE - Título bloqueado na base'),
    ('ZF', 'ZF - Sistema em contingência'
           ' – título valor maior que referência'),
    ('ZG', 'ZG - Sistema em contingência – título vencido'),
    ('ZH', 'ZH - Sistema em contingência – título indexado'),
    ('ZI', 'ZI - Beneficiário divergente'),
    ('ZJ', 'ZJ - Limite de pagamentos parciais excedido'),
    ('ZK', 'ZK - Boleto já liquidado'),
]


BOLETO_ESPECIE = [
    ('01', 'CH Cheque'),
    ('02', 'DM Duplicata Mercantil'),
    ('03', 'DMI Duplicata Mercantil p/ Indicação'),
    ('04', 'DS Duplicata de Serviço'),
    ('05', 'DSI Duplicata de Serviço p/ Indicação'),
    ('06', 'DR Duplicata Rural'),
    ('07', 'LC Letra de Câmbio'),
    ('08', 'NCC Nota de Crédito Comercial'),
    ('09', 'NCE Nota de Crédito a Exportação'),
    ('10', 'NCI Nota de Crédito Industrial'),
    ('11', 'NCR Nota de Crédito Rural'),
    ('12', 'NP Nota Promissória'),
    ('13', 'NPR Nota Promissória Rural'),
    ('14', 'TM Triplicata Mercantil'),
    ('15', 'TS Triplicata de Serviço'),
    ('16', 'NS Nota de Seguro'),
    ('17', 'RC Recibo'),
    ('18', 'FAT Fatura'),
    ('19', 'ND Nota de Débito'),
    ('20', 'AP Apólice de Seguro'),
    ('21', 'ME Mensalidade Escolar'),
    ('22', 'PC Parcela de Consórcio'),
    ('23', 'NF Nota Fiscal'),
    ('24', 'DD Documento de Dívida'),
    ('25', 'Cédula de Produto Rural'),
    ('26', 'Warrant'),
    ('27', 'Dívida Ativa de Estado'),
    ('28', 'Dívida Ativa de Município'),
    ('29', 'Dívida Ativa da União'),
    ('30', 'Encargos Condominiais'),
    ('31', 'CC Cartão de Crédito'),
    ('32', 'BDP Boleto de Proposta'),
    ('99', 'Outros')
]

BOLETO_ESPECIE_DUPLICATA_MERCANTIL = '01'
BOLETO_ESPECIE_NOTA_PROMISSORIA = '02'
BOLETO_ESPECIE_NOTA_SEGURO = '03'
BOLETO_ESPECIE_MENSALIDADE_ESCOLAR = '04'
BOLETO_ESPECIE_RECIBO = '05'
BOLETO_ESPECIE_CONTRATO = '06'
BOLETO_ESPECIE_COSSEGUROS = '07'
BOLETO_ESPECIE_DUPLICATA_SERVICO = '08'
BOLETO_ESPECIE_LETRA_CAMBIO = '09'
BOLETO_ESPECIE_NOTA_DEBITOS = '13'
BOLETO_ESPECIE_DOCUMENTO_DIVIDA = '15'
BOLETO_ESPECIE_ENCARGOS_CONDOMINIAIS = '16'
BOLETO_ESPECIE_CONTA_PRESTACAO_SERVICOS = '17'
BOLETO_ESPECIE_DIVERSOS = '99'


BOLETO_EMISSAO = [
    ('1', '1 - Banco emite'),
    ('2', '2 - Beneficiário emite'),
    #('3', '3 - Banco pré-emite, beneficiário complementa'),
    #('4', '4 - Banco reemite'),
    #('5', '5 - Banco não reemite'),
    #('7', '7 - Banco emitente - aberta'),
    #('8', '8 - Banco emitente - auto-envelopável'),
]
BOLETO_EMISSAO_BANCO = '1'
BOLETO_EMISSAO_BENEFICIARIO = '2'

BOLETO_DISTRIBUICAO = [
    ('1', '1 - Banco distribui'),
    ('2', '2 - Beneficiário distribui'),
    ('3', '3 - Banco envia por email'),
    ('4', '4 - Banco envia por SMS'),
]
BOLETO_DISTRIBUICAO_BANCO = '1'
BOLETO_DISTRIBUICAO_BENEFICIARIO = '2'
