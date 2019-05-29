# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


SEQUENCIAL_EMPRESA = '0'
SEQUENCIAL_FATURA = '1'
SEQUENCIAL_CARTEIRA = '2'


COBRANCA = '01'
BOLETO_PAGAMENTO_ELETRONICO = '03'
CONCILIACAO_BANCARIA = '04'
DEBITOS = '05'
CUSTODIA_CHEQUES = '06'
GESTAO_CAIXA = '07'
CONSULTA_INFORMACAO_MARGEM = '08'
AVERBACAO_CONSIGNACAO_RETENCAO = '09'
PAGAMENTO_DIVIDENDOS = '10'
MANUTENCAO_CONSIGNACAO = '11'
CONSIGNACAO_PARCELAS = '12'
GLOSA_CONSIGNACAO = '13'
CONSULTA_TRIBUTOS_PAGAR = '14'
PAGAMENTO_FORNECEDOR = '20'
PAGAMENTO_CONTAS_TRIBUTOS_IMPOSTOS = '22'
INTEROPERABILIDADE_CONTAS = '23'
COMPROR = '25'
COMPROR_ROTATIVO = '26'
ALEGACAO_PAGADOR = '29'
PAGAMENTO_SALARIOS = '30'
PAGAMENTO_HONORARIOS = '32'
PAGAMENTO_BOLSA_AUXILIO = '33'
PAGAMENTO_PREBENDA = '34'
VENDOR = '40'
VENDOR_TERMO = '41'
PAGAMENTO_SINISTROS_SEGURADOS = '50'
PAGAMENTO_DESPESAS_VIAJANTE = '60'
PAGAMENTO_AUTORIZADO = '70'
PAGAMENTO_CREDENCIADOS = '75'
PAGAMENTO_REMUNERACAO = '77'
PAGAMENTO_REPRESENTANTES = '80'
PAGAMENTO_BENEFICIOS = '90'
PAGAMENTOS_DIVERSOS = '98'

TIPO_SERVICO = [
    (COBRANCA, COBRANCA + u' - Cobrança'),
    (BOLETO_PAGAMENTO_ELETRONICO, BOLETO_PAGAMENTO_ELETRONICO +
     u' - Boleto de Pagamento Eletrônico'),
    (CONCILIACAO_BANCARIA, CONCILIACAO_BANCARIA + u' - Conciliação Bancária'),
    (DEBITOS, DEBITOS + u' - Débitos'),
    (CUSTODIA_CHEQUES, CUSTODIA_CHEQUES + u' - Custódia de Cheques'),
    (GESTAO_CAIXA, GESTAO_CAIXA + u' - Gestão de Caixa'),
    (CONSULTA_INFORMACAO_MARGEM, CONSULTA_INFORMACAO_MARGEM +
     u' - Consulta/Informação Margem'),
    (AVERBACAO_CONSIGNACAO_RETENCAO, AVERBACAO_CONSIGNACAO_RETENCAO +
     u' - Averbação da Consignação/Retenção'),
    (PAGAMENTO_DIVIDENDOS, PAGAMENTO_DIVIDENDOS + u' - Pagamento Dividendos'),
    (MANUTENCAO_CONSIGNACAO, MANUTENCAO_CONSIGNACAO +
     u' - Manutenção da Consignação'),
    (CONSIGNACAO_PARCELAS, CONSIGNACAO_PARCELAS +
     u' - Consignação de Parcelas'),
    (GLOSA_CONSIGNACAO, GLOSA_CONSIGNACAO +
     u' -  Glosa da Consignação (INSS)'),
    (CONSULTA_TRIBUTOS_PAGAR, CONSULTA_TRIBUTOS_PAGAR +
     u' - Consulta de Tributos a pagar'),
    (PAGAMENTO_FORNECEDOR, PAGAMENTO_FORNECEDOR +
     u' - Pagamento Fornecedor'),
    (PAGAMENTO_CONTAS_TRIBUTOS_IMPOSTOS, PAGAMENTO_CONTAS_TRIBUTOS_IMPOSTOS +
     u' - Pagamento de Contas, Tributos e Impostos'),
    (INTEROPERABILIDADE_CONTAS, INTEROPERABILIDADE_CONTAS +
     u' - Interoperabilidade entre Contas de Instituições de Pagamentos'),
    (COMPROR, COMPROR + u' - Compror'),
    (COMPROR_ROTATIVO, COMPROR_ROTATIVO + u' - Compror Rotativo'),
    (ALEGACAO_PAGADOR, ALEGACAO_PAGADOR + u' - Alegação do Pagador'),
    (PAGAMENTO_SALARIOS, PAGAMENTO_SALARIOS + u' - Pagamento Salários'),
    (PAGAMENTO_HONORARIOS, PAGAMENTO_HONORARIOS +
     u' - Pagamento de honorários'),
    (PAGAMENTO_BOLSA_AUXILIO, PAGAMENTO_BOLSA_AUXILIO +
     u' - Pagamento de bolsa auxílio'),
    (PAGAMENTO_PREBENDA, PAGAMENTO_PREBENDA +
     u' - Pagamento de prebenda (remuneração a padres e sacerdotes)'),
    (VENDOR, VENDOR + u' - Vendor'),
    (VENDOR_TERMO, VENDOR_TERMO + u' - Vendor a Termo'),
    (PAGAMENTO_SINISTROS_SEGURADOS, PAGAMENTO_SINISTROS_SEGURADOS +
     u' - Pagamento Sinistros Segurados'),
    (PAGAMENTO_DESPESAS_VIAJANTE, PAGAMENTO_DESPESAS_VIAJANTE +
     u' - Pagamento Despesas Viajante em Trânsito'),
    (PAGAMENTO_AUTORIZADO, PAGAMENTO_AUTORIZADO + u' - Pagamento Autorizado'),
    (PAGAMENTO_CREDENCIADOS, PAGAMENTO_CREDENCIADOS +
     u' - Pagamento Credenciados'),
    (PAGAMENTO_REMUNERACAO, PAGAMENTO_REMUNERACAO +
     u' - Pagamento de Remuneração'),
    (PAGAMENTO_REPRESENTANTES, PAGAMENTO_REPRESENTANTES +
     u' - Pagamento Representantes / Vendedores Autorizados'),
    (PAGAMENTO_BENEFICIOS, PAGAMENTO_BENEFICIOS + u' - Pagamento Benefícios'),
    (PAGAMENTOS_DIVERSOS, PAGAMENTOS_DIVERSOS + u' - Pagamentos Diversos'),
]

CREDITO_CONTA_CORRENTE_SALARIO = (
    '01', u'01 - Crédito em Conta Corrente/Salário')
CHEQUE_PAGAMENTO_ADMINISTRATIVO = (
    '02', u'02 - Cheque Pagamento / Administrativo')
DOC_TED = ('03', u'03 - DOC/TED (1) (2)')
CARTAO_SALARIO = (
    '04', u'04 - Cartão Salário (somente para Tipo de Serviço = \'30\')')
CREDITO_CONTA_POUPANCA = ('05', u'05 - Crédito em Conta Poupança')
OP_A_DISPOSICAO = ('10', u'10 - OP à Disposição')
PAGAMENTO_CONTAS_TRIBUTOS_CODIGO_BARRAS = (
    '11', u'11 - Pagamento de Contas e Tributos com Código de Barras')
TRIBUTO_DARF_NORMAL = ('16', u'16 - Tributo - DARF Normal')
TRIBUTO_GPS = ('17', u'17 - Tributo - GPS (Guia da Previdência Social)')
TRIBUTO_DARF_SIMPLES = ('18', u'18 - Tributo - DARF Simples')
TRIBUTO_IPTU_PREFEITURAS = ('19', u'19 - Tributo - IPTU – Prefeituras')
PAGAMENTO_AUTENTICACAO = ('20', u'20 - Pagamento com Autenticação')
TRIBUTO_DARJ = ('21', u'21 - Tributo – DARJ')
TRIBUTO_GARE_SP_ICMS = ('22', u'22 - Tributo - GARE-SP ICMS')
TRIBUTO_GARE_SP_DR = ('23', u'23 - Tributo - GARE-SP DR')
TRIBUTO_GARE_SP_ITCMD = ('24', u'24 - Tributo - GARE-SP ITCMD')
TRIBUTO_IPVA = ('25', u'25 - Tributo - IPVA')
TRIBUTO_LICENCIAMENTO = ('26', u'26 - Tributo - Licenciamento')
TRIBUTO_DPVAT = ('27', u'27 - Tributo – DPVAT')
LIQUIDACAO_TITULOS_PROPRIO_BANCO = (
    '30', u'30 - Liquidação de Títulos do Próprio Banco')
PAGAMENTO_TITULOS_OUTROS_BANCOS = (
    '31', u'31 - Pagamento de Títulos de Outros Bancos')
EXTRATO_CONTA_CORRENTE = ('40', u'40 - Extrato de Conta Corrente')
TED_OUTRA_TITULARIDADE = ('41', u'41 - TED – Outra Titularidade (1)')
TED_MESMA_TITULARIDADE = ('43', u'43 - TED – Mesma Titularidade (1)')
TED_TRANSFERENCIA_CONTA_INVESTIMENTO = (
    '44', u'44 - TED para Transferência de Conta Investimento')
DEBITO_CONTA_CORRENTE = ('50', u'50 - Débito em Conta Corrente')
EXTRATO_GESTAO_CAIXA = ('70', u'70 - Extrato para Gestão de Caixa')
DEPOSITO_JUDICIAL_CONTA_CORRENTE = (
    '71', u'71 - Depósito Judicial em Conta Corrente')
DEPOSITO_JUDICIAL_POUPANCA = ('72', u'72 - Depósito Judicial em Poupança')
EXTRATO_CONTA_INVESTIMENTO = ('73', u'73 - Extrato de Conta Investimento')

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

CREDITO_EM_CONTA = ('01', u'01 - Crédito em Conta')
PAGAMENTO_ALUGUEL = ('02', u'02 - Pagamento de Aluguel/Condomínio')
PAGAMENTO_DUPLICATA_TITULOS = ('03', u'03 - Pagamento de Duplicata/Títulos')
PAGAMENTO_DIVIDENDOS_C = ('04', u'04 - Pagamento de Dividendos')
PAGAMENTO_MENSALIDADE_ESCOLAR = (
    '05', u'05 - Pagamento de Mensalidade Escolar')
PAGAMENTO_SALARIOS_C = ('06', u'06 - Pagamento de Salários')
PAGAMENTO_FORNECEDORES = ('07', u'07 - Pagamento a Fornecedores')
OPERACOES_CAMBIOS_FUNDOS_BOLSA = (
    '08', u'08 - Operações de Câmbios/Fundos/Bolsa de Valores')
REPASSE_ARRECADACAO = (
    '09', u'09 - Repasse de Arrecadação/Pagamento de Tributos')
TRANSFERECIA_INTERNACIONAL_EM_REAL = (
    '10', u'10 - Transferência Internacional em Real')
DOC_POUPANCA = ('11', u'11 - DOC para Poupança')
DOC_DEPOSITO_JUDICIAL = ('12', u'12 - DOC para Depósito Judicial')
OUTROS = ('13', u'13 - Outros')
PAGAMENTO_BOLSA_AUXILIO_C = ('16', u'16 - Pagamento de bolsa auxílio')
REMUNERACAO_COOPERADO = ('17', u'17 - Remuneração à cooperado')
PAGAMENTO_HONORARIOS_C = ('18', u'18 - Pagamento de honorários')
PAGAMENTO_PREBENDA_C = (
    '19', u'19 - Pagamento de prebenda (Remuneração a padres e sacerdotes)')

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
CODIGO_FINALIDADE_TED = [
    ('    ', u'Padrão')
]

NAO_EMITE_AVISO = ('0', u'0 - Não Emite Aviso')
EMITE_AVISO_REMETENTE = ('2', u'2 - Emite Aviso Somente para o Remetente')
EMITE_AVISO_FAVORECIDO = ('5', u'5 - Emite Aviso Somente para o Favorecido')
EMITE_AVISO_REMETENTE_FAVORECIDO = \
    ('6', u'6 - Emite Aviso para o Remetente e Favorecido')
EMITE_AVISO_FAVORECIDO_2_VIAS_REMETENTE = \
    ('7', u'7 - Emite Aviso para o Favorecido e 2 Vias para o Remetente')

AVISO_FAVORECIDO = [
    NAO_EMITE_AVISO,
    EMITE_AVISO_REMETENTE,
    EMITE_AVISO_FAVORECIDO,
    EMITE_AVISO_REMETENTE_FAVORECIDO,
    EMITE_AVISO_FAVORECIDO_2_VIAS_REMETENTE,
]

INDICATIVO_FORMA_PAGAMENTO = [
    ('01', u'01 - Débito em Conta Corrente'),
    ('02', u'02 - Débito Empréstimo/Financiamento'),
    ('03', u'03 - Débito Cartão de Crédito'),
]

TIPO_MOVIMENTO = [
    ('0', u'0 - Indica INCLUSÃO'),
    ('1', u'1 - Indica CONSULTA'),
    ('2', u'2 - Indica SUSPENSÃO'),
    ('3', u'3 - Indica ESTORNO (somente para retorno)'),
    ('4', u'4 - Indica REATIVAÇÃO'),
    ('5', u'5 - Indica ALTERAÇÃO'),
    ('7', u'7 - Indica LIQUIDAÇAO'),
    ('9', u'9 - Indica EXCLUSÃO'),
]

CODIGO_INSTRUCAO_MOVIMENTO = [
    ('0', u'00 - Inclusão de Registro Detalhe Liberado'),
    ('9', u'09 - Inclusão do Registro Detalhe Bloqueado'),
    ('10', u'10 - Alteração do Pagamento Liberado para Bloqueado (Bloqueio)'),
    ('11', u'11 - Alteração do Pagamento Bloqueado para Liberado (Liberação)'),
    ('17', u'17 - Alteração do Valor do Título'),
    ('19', u'19 - Alteração da Data de Pagamento'),
    ('23', u'23 - Pagamento Direto ao Fornecedor - Baixar'),
    ('25', u'25 - Manutenção em Carteira - Não Pagar'),
    ('27', u'27 - Retirada de Carteira - Não Pagar'),
    ('33', u'33 - Estorno por Devolução da Câmara Centralizadora '
           u'(somente para Tipo de Movimento = \'3\')'),
    ('40', u'40 - Alegação do Pagador'),
    ('99', u'99 - Exclusão do Registro Detalhe Incluído Anteriormente'),
]

CODIGO_OCORRENCIAS = [
    ('00', u'00 - Crédito ou Débito Efetivado'),
    ('01', u'01 - Insuficiência de Fundos - Débito Não Efetuado'),
    ('02', u'02 - Crédito ou Débito Cancelado pelo Pagador/Credor'),
    ('03', u'03 - Débito Autorizado pela Agência - Efetuado'),
    ('AA', u'AA - Controle Inválido'),
    ('AB', u'AB - Tipo de Operação Inválido'),
    ('AC', u'AC - Tipo de Serviço Inválido'),
    ('AD', u'AD - Forma de Lançamento Inválida'),
    ('AE', u'AE - Tipo/Número de Inscrição Inválido'),
    ('AF', u'AF - Código de Convênio Inválido'),
    ('AG', u'AG - Agência/Conta Corrente/DV Inválido'),
    ('AH', u'AH - Nº Seqüencial do Registro no Lote Inválido'),
    ('AI', u'AI - Código de Segmento de Detalhe Inválido'),
    ('AJ', u'AJ - Tipo de Movimento Inválido'),
    ('AK', u'AK - Código da Câmara de Compensação do Banco'
           u' Favorecido/Depositário Inválido'),
    ('AL', u'AL - Código do Banco Favorecido, Instituição de Pagamento'
           u' ou Depositário Inválido'),
    ('AM', u'AM - Agência Mantenedora da Conta Corrente do'
           u' Favorecido Inválida'),
    ('AN', u'AN - Conta Corrente/DV/Conta de Pagamento do'
           u' Favorecido Inválido'),
    ('AO', u'AO - Nome do Favorecido Não Informado'),
    ('AP', u'AP - Data Lançamento Inválido'),
    ('AQ', u'AQ - Tipo/Quantidade da Moeda Inválido'),
    ('AR', u'AR - Valor do Lançamento Inválido'),
    ('AS', u'AS - Aviso ao Favorecido - Identificação Inválida'),
    ('AT', u'AT - Tipo/Número de Inscrição do Favorecido Inválido'),
    ('AU', u'AU - Logradouro do Favorecido Não Informado'),
    ('AV', u'AV - Nº do Local do Favorecido Não Informado'),
    ('AW', u'AW - Cidade do Favorecido Não Informada'),
    ('AX', u'AX - CEP/Complemento do Favorecido Inválido'),
    ('AY', u'AY - Sigla do Estado do Favorecido Inválida'),
    ('AZ', u'AZ - Código/Nome do Banco Depositário Inválido'),
    ('BA', u'BA - Código/Nome da Agência Depositária Não Informado'),
    ('BB', u'BB - Seu Número Inválido'),
    ('BC', u'BC - Nosso Número Inválido'),
    ('BD', u'BD - Inclusão Efetuada com Sucesso'),
    ('BE', u'BE - Alteração Efetuada com Sucesso'),
    ('BF', u'BF - Exclusão Efetuada com Sucesso'),
    ('BG', u'BG - Agência/Conta Impedida Legalmente'),
    ('BH', u'BH - Empresa não pagou salário'),
    ('BI', u'BI - Falecimento do mutuário'),
    ('BJ', u'BJ - Empresa não enviou remessa do mutuário'),
    ('BK', u'BK - Empresa não enviou remessa no vencimento'),
    ('BL', u'BL - Valor da parcela inválida'),
    ('BM', u'BM - Identificação do contrato inválida'),
    ('BN', u'BN - Operação de Consignação Incluída com Sucesso'),
    ('BO', u'BO - Operação de Consignação Alterada com Sucesso'),
    ('BP', u'BP - Operação de Consignação Excluída com Sucesso'),
    ('BQ', u'BQ - Operação de Consignação Liquidada com Sucesso'),
    ('BR', u'BR - Reativação Efetuada com Sucesso'),
    ('BS', u'BS - Suspensão Efetuada com Sucesso'),
    ('CA', u'CA - Código de Barras - Código do Banco Inválido'),
    ('CB', u'CB - Código de Barras - Código da Moeda Inválido'),
    ('CC', u'CC - Código de Barras - Dígito Verificador Geral Inválido'),
    ('CD', u'CD - Código de Barras - Valor do Título Inválido'),
    ('CE', u'CE - Código de Barras - Campo Livre Inválido'),
    ('CF', u'CF - Valor do Documento Inválido'),
    ('CG', u'CG - Valor do Abatimento Inválido'),
    ('CH', u'CH - Valor do Desconto Inválido'),
    ('CI', u'CI - Valor de Mora Inválido'),
    ('CJ', u'CJ - Valor da Multa Inválido'),
    ('CK', u'CK - Valor do IR Inválido'),
    ('CL', u'CL - Valor do ISS Inválido'),
    ('CM', u'CM - Valor do IOF Inválido'),
    ('CN', u'CN - Valor de Outras Deduções Inválido'),
    ('CO', u'CO - Valor de Outros Acréscimos Inválido'),
    ('CP', u'CP - Valor do INSS Inválido'),
    ('HA', u'HA - Lote Não Aceito'),
    ('HB', u'HB - Inscrição da Empresa Inválida para o Contrato'),
    ('HC', u'HC - Convênio com a Empresa Inexistente/Inválido'
           u' para o Contrato'),
    ('HD', u'HD - Agência/Conta Corrente da Empresa Inexistente/Inválido'
           u' para o Contrato'),
    ('HE', u'HE - Tipo de Serviço Inválido para o Contrato'),
    ('HF', u'HF - Conta Corrente da Empresa com Saldo Insuficiente'),
    ('HG', u'HG - Lote de Serviço Fora de Seqüência'),
    ('HH', u'HH - Lote de Serviço Inválido'),
    ('HI', u'HI - Arquivo não aceito'),
    ('HJ', u'HJ - Tipo de Registro Inválido'),
    ('HK', u'HK - Código Remessa / Retorno Inválido'),
    ('HL', u'HL - Versão de layout inválida'),
    ('HM', u'HM - Mutuário não identificado'),
    ('HN', u'HN - Tipo do beneficio não permite empréstimo'),
    ('HO', u'HO - Beneficio cessado/suspenso'),
    ('HP', u'HP - Beneficio possui representante legal'),
    ('HQ', u'HQ - Beneficio é do tipo PA (Pensão alimentícia)'),
    ('HR', u'HR - Quantidade de contratos permitida excedida'),
    ('HS', u'HS - Beneficio não pertence ao Banco informado'),
    ('HT', u'HT - Início do desconto informado já ultrapassado'),
    ('HU', u'HU - Número da parcela inválida'),
    ('HV', u'HV - Quantidade de parcela inválida'),
    ('HW', u'HW - Margem consignável excedida para o mutuário dentro'
           u' do prazo do contrato'),
    ('HX', u'HX - Empréstimo já cadastrado'),
    ('HY', u'HY - Empréstimo inexistente'),
    ('HZ', u'HZ - Empréstimo já encerrado'),
    ('H1', u'H1 - Arquivo sem trailer'),
    ('H2', u'H2 - Mutuário sem crédito na competência'),
    ('H3', u'H3 - Não descontado – outros motivos'),
    ('H4', u'H4 - Retorno de Crédito não pago'),
    ('H5', u'H5 - Cancelamento de empréstimo retroativo'),
    ('H6', u'H6 - Outros Motivos de Glosa'),
    ('H7', u'H7 - Margem consignável excedida para o mutuário acima'
           u' do prazo do contrato'),
    ('H8', u'H8 - Mutuário desligado do empregador'),
    ('H9', u'H9 - Mutuário afastado por licença'),
    ('IA', u'IA - Primeiro nome do mutuário diferente do primeiro nome'
           u' do movimento do censo ou diferente da base de Titular'
           u' do Benefício'),
    ('IB', u'IB - Benefício suspenso/cessado pela APS ou Sisobi'),
    ('IC', u'IC - Benefício suspenso por dependência de cálculo'),
    ('ID', u'ID - Benefício suspenso/cessado pela inspetoria/auditoria'),
    ('IE', u'IE - Benefício bloqueado para empréstimo pelo beneficiário'),
    ('IF', u'IF - Benefício bloqueado para empréstimo por TBM'),
    ('IG', u'IG - Benefício está em fase de concessão de PA ou desdobramento'),
    ('IH', u'IH - Benefício cessado por óbito'),
    ('II', u'II - Benefício cessado por fraude'),
    ('IJ', u'IJ - Benefício cessado por concessão de outro benefício'),
    ('IK', u'IK - Benefício cessado: estatutário transferido'
           u' para órgão de origem'),
    ('IL', u'IL - Empréstimo suspenso pela APS'),
    ('IM', u'IM - Empréstimo cancelado pelo banco'),
    ('IN', u'IN - Crédito transformado em PAB'),
    ('IO', u'IO - Término da consignação foi alterado'),
    ('IP', u'IP - Fim do empréstimo ocorreu durante período'
           u' de suspensão ou concessão'),
    ('IQ', u'IQ - Empréstimo suspenso pelo banco'),
    ('IR', u'IR - Não averbação de contrato – quantidade de'
           u' parcelas/competências informadas ultrapassou a data limite'
           u' da extinção de cota do dependente titular de benefícios'),
    ('TA', u'TA - Lote Não Aceito - Totais do Lote com Diferença'),
    ('YA', u'YA - Título Não Encontrado'),
    ('YB', u'YB - Identificador Registro Opcional Inválido'),
    ('YC', u'YC - Código Padrão Inválido'),
    ('YD', u'YD - Código de Ocorrência Inválido'),
    ('YE', u'YE - Complemento de Ocorrência Inválido'),
    ('YF', u'YF - Alegação já Informada'),
    ('ZA', u'ZA - Agência / Conta do Favorecido Substituída'),
    ('ZB', u'ZB - Divergência entre o primeiro e último nome do beneficiário'
           u' versus primeiro e último nome na Receita Federal'),
    ('ZC', u'ZC - Confirmação de Antecipação de Valor'),
    ('ZD', u'ZD - Antecipação parcial de valor'),
    ('ZE', u'ZE - Título bloqueado na base'),
    ('ZF', u'ZF - Sistema em contingência'
           u' – título valor maior que referência'),
    ('ZG', u'ZG - Sistema em contingência – título vencido'),
    ('ZH', u'ZH - Sistema em contingência – título indexado'),
    ('ZI', u'ZI - Beneficiário divergente'),
    ('ZJ', u'ZJ - Limite de pagamentos parciais excedido'),
    ('ZK', u'ZK - Boleto já liquidado'),
]
