# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

import logging
_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D
except (ImportError, IOError) as err:
    _logger.debug(err)

#
# Definições para cálculo do ICMS próprio
#
MODALIDADE_BASE_ICMS_PROPRIO = (
    ('0', 'Margem de valor agregado (%) × valor do produto'),
    ('1', 'Pauta (R$) × quantidade'),
    ('2', 'Preço tabelado máximo (R$) × quantidade'),
    ('3', 'Valor da operação (R$) = quantidade × valor unitário'),
)
MODALIDADE_BASE_ICMS_PROPRIO_DICT = dict(MODALIDADE_BASE_ICMS_PROPRIO)

MODALIDADE_BASE_ICMS_PROPRIO_MARGEM_VALOR_AGREGADO = '0'
MODALIDADE_BASE_ICMS_PROPRIO_PAUTA = '1'
MODALIDADE_BASE_ICMS_PROPRIO_PRECO_TABELADO_MAXIMO = '2'
MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO = '3'

MODALIDADE_BASE_ICMS_PROPRIO_PRECO_FIXO = (
    MODALIDADE_BASE_ICMS_PROPRIO_PAUTA,
    MODALIDADE_BASE_ICMS_PROPRIO_PRECO_TABELADO_MAXIMO,
)


#
# Definições para cálculo do ICMS recolhido por substituição tributária
#
MODALIDADE_BASE_ICMS_ST = (
    ('0', 'Preço tabelado ou máximo sugerido (R$) × quantidade'),
    ('1', 'Lista negativa (R$) × quantidade'),
    ('2', 'Lista positiva (R$) × quantidade'),
    ('3', 'Lista neutra (R$) × quantidade'),
    ('4', 'Margem de valor agregado (%) × valor do produto'),
    ('5', 'Pauta (R$) × quantidade'),
)
MODALIDADE_BASE_ICMS_ST_DICT = dict(MODALIDADE_BASE_ICMS_ST)

MODALIDADE_BASE_ICMS_ST_PRECO_TABELADO_MAXIMO = '0'
MODALIDADE_BASE_ICMS_ST_LISTA_NEGATIVA = '1'
MODALIDADE_BASE_ICMS_ST_LISTA_POSITIVA = '2'
MODALIDADE_BASE_ICMS_ST_LISTA_NEUTRA = '3'
MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO = '4'
MODALIDADE_BASE_ICMS_ST_PAUTA = '5'

MODALIDADE_BASE_ICMS_ST_PRECO_FIXO = (
    MODALIDADE_BASE_ICMS_ST_PRECO_TABELADO_MAXIMO,
    MODALIDADE_BASE_ICMS_ST_LISTA_NEGATIVA,
    MODALIDADE_BASE_ICMS_ST_LISTA_POSITIVA,
    MODALIDADE_BASE_ICMS_ST_LISTA_NEUTRA,
    MODALIDADE_BASE_ICMS_ST_PAUTA,
)


#
# Definições para o cálculo do IPI
#

MODALIDADE_BASE_IPI = (
    ('0', 'Tributação por alíquota'),
    ('1', 'Tributação por quantidade'),
    )
MODALIDADE_BASE_IPI_DICT = dict(MODALIDADE_BASE_IPI)

MODALIDADE_BASE_IPI_ALIQUOTA = '0'
MODALIDADE_BASE_IPI_QUANTIDADE = '1'


#
# Definições para o cálculo do PIS e da COFINS
#
MODALIDADE_BASE_PIS = (
    ('0', 'Tributação por alíquota'),
    ('1', 'Tributação por quantidade'),
    )
MODALIDADE_BASE_PIS_DICT = dict(MODALIDADE_BASE_PIS)

MODALIDADE_BASE_PIS_ALIQUOTA = '0'
MODALIDADE_BASE_PIS_QUANTIDADE = '1'

MODALIDADE_BASE_COFINS = MODALIDADE_BASE_PIS
MODALIDADE_BASE_COFINS_ALIQUOTA = MODALIDADE_BASE_PIS_ALIQUOTA
MODALIDADE_BASE_COFINS_QUANTIDADE = MODALIDADE_BASE_PIS_QUANTIDADE

#
# Definições para o cálculo do ISS
#
MODALIDADE_BASE_ISS = (
    ('0', 'Tributação por alíquota'),
    ('1', 'Tributação por quantidade'),
    )
MODALIDADE_BASE_ISS_DICT = dict(MODALIDADE_BASE_ISS)

MODALIDADE_BASE_ISS_ALIQUOTA = '0'
MODALIDADE_BASE_ISS_QUANTIDADE = '1'


#
# Definições para a emissão e controle da NF-e
#
AMBIENTE_NFE = (
    ('1', 'Produção'),
    ('2', 'Homologação'),
)
AMBIENTE_NFE_DICT = dict(AMBIENTE_NFE)

AMBIENTE_NFE_PRODUCAO = '1'
AMBIENTE_NFE_HOMOLOGACAO = '2'


ENTRADA_SAIDA = (
    ('0', 'Entrada'),
    ('1', 'Saída'),
)
ENTRADA_SAIDA_DICT = dict(ENTRADA_SAIDA)

ENTRADA_SAIDA_ENTRADA = '0'
ENTRADA_SAIDA_SAIDA = '1'


FINALIDADE_NFE = (
    ('1', 'Normal'),
    ('2', 'Complementar'),
    ('3', 'Ajuste'),
    ('4', 'Devolução de mercadoria'),
)
FINALIDADE_NFE_DICT = dict(FINALIDADE_NFE)

FINALIDADE_NFE_NORMAL = '1'
FINALIDADE_NFE_COMPLEMENTAR = '2'
FINALIDADE_NFE_AJUSTE = '3'
FINALIDADE_NFE_DEVOLUCAO = '4'


FORMA_PAGAMENTO = (
    ('0', 'À vista'),
    ('1', 'A prazo'),
    ('2', 'Outros/sem pagamento'),
)
FORMA_PAGAMENTO_DICT = dict(FORMA_PAGAMENTO)

FORMA_PAGAMENTO_A_VISTA = '0'
FORMA_PAGAMENTO_A_PRAZO = '1'
FORMA_PAGAMENTO_SEM_PAGAMENTO = '2'


MODALIDADE_FRETE = (
    ('0', 'Do emitente'),
    ('1', 'Do destinatário'),
    ('2', 'De terceiros'),
    ('9', 'Sem frete'),
)
MODALIDADE_FRETE_DICT = dict(MODALIDADE_FRETE)

MODALIDADE_FRETE_EMITENTE = '0'
MODALIDADE_FRETE_DESTINATARIO = '1'
MODALIDADE_FRETE_TERCEIROS = '2'
MODALIDADE_FRETE_SEM_FRETE = '9'


MODELO_DOCUMENTO_ARRECADACAO = (
    ('0', 'Documento estadual de arrecadacao'),
    ('1', 'GNRE'),
    )
MODELO_DOCUMENTO_ARRECADACAO_DICT = dict(MODELO_DOCUMENTO_ARRECADACAO)

MODELO_DOCUMENTO_ARRECADACAO_DEA = '0'
MODELO_DOCUMENTO_ARRECADACAO_GNRE = '1'


MOTIVO_DESONERACAO_ICMS = (
    ('0', '0 - Não desonerado'),
    ('1', '1 - Táxi'),
    ('2', '2 - Deficiente físico'),
    ('3', '3 - Produtor agropecuário'),
    ('4', '4 - Frotista/locadora'),
    ('5', '5 - Diplomático/consular'),
    ('6', '6 - Util. e mot. da Amazônia Ocidental e áreas de livre comércio'),
    ('7', '7 - SUFRAMA'),
    ('9', '9 - Outros'),
)
MOTIVO_DESONERACAO_ICMS_DICT = dict(MOTIVO_DESONERACAO_ICMS)

MOTIVO_DESONERACAO_ICMS_NAO_DESONERADO = '0'
MOTIVO_DESONERACAO_ICMS_TAXI = '1'
MOTIVO_DESONERACAO_ICMS_DEFICIENTE_FISICO = '2'
MOTIVO_DESONERACAO_ICMS_PRODUTOR_AGROPECUARIO = '3'
MOTIVO_DESONERACAO_ICMS_FROTISTA_LOCADORA = '4'
MOTIVO_DESONERACAO_ICMS_DIPLOMATICO_CONSULAR = '5'
MOTIVO_DESONERACAO_ICMS_UTILITARIOS_AMAZONIA = '6'
MOTIVO_DESONERACAO_ICMS_SUFRAMA = '7'
MOTIVO_DESONERACAO_ICMS_OUTROS = '9'


MODELO_FISCAL = (
    #('MERCADORIAS E SERVIÇOS', (
        ('65', 'NFC-e - 65'),
        ('2D', 'CF por impressora fiscal - 2D'),
        ('2C', 'CF por ponto de venda (PDV) - 2C'),
        ('2B', 'CF por máquina registradora - 2B'),
        ('59', 'CF-e - 59'),
        ('60', 'CF-e ECF - 60'),
        ('01', 'NF - 01 E 1A'),
        ('1B', 'NF avulsa - 1B'),
        ('04', 'NF de produtor rural - 04'),
        ('21', 'NF de serv. de comunicação - 21'),
        ('22', 'NF de serv. de telecomunicação - 22'),
        ('07', 'NF de serv. de transporte - 07'),
        ('27', 'NF de transp. ferroviário de cargas - 27'),
        ('02', 'NF de venda a consumidor - 02'),
        ('55', 'NF-e - 55'),
        ('06', 'NF/conta de energia elétrica - 06'),
        ('29', 'NF/conta de fornec. de água canalizada - 29'),
        ('28', 'NF/conta de fornec. de gás canalizado - 28'),
        ('18', 'CF - resumo de movimento diário - 18'),
        ('23', 'GNRE - 23'),
        #
        # Modelos não oficiais
        #
        ('SC', 'NFS - SC'),
        ('SE', 'NFS-e - SE'),
        ('RL', 'Recibo de locação - RL'),
        ('XX', 'Outros documentos não fiscais - XX'),
        ('TF', 'Atualização de tabela de fornecedor'),
    #)),
    #('TRANSPORTE', (
        ('24', 'Autorização de carregamento e transporte - 24'),
        ('14', 'Bilhete de passagem aquaviário - 14'),
        ('15', 'Bilhete de passagem e nota de bagagem -15'),
        ('2E', 'Bilhete de passagem emitido por ECF - 2E'),
        ('16', 'Bilhete de passagem ferroviário - 16'),
        ('13', 'Bilhete de passagem rodoviário - 13'),
        ('30', 'Bilhete/recibo do passageiro - 30'),
        ('10', 'Conhecimento aéreo - 10'),
        ('09', 'Conhec. de transporte aquaviário de cargas - 09'),
        ('8B', 'Conhec. de transporte de cargas avulso - 8B'),
        ('57', 'CT-e - 57'),
        ('11', 'Conhec. de transporte ferroviário de cargas - 11'),
        ('26', 'Conhec. de transporte multimodal de cargas - 26'),
        ('08', 'Conhec. de transporte rodoviário de cargas - 08'),
        ('17', 'Despacho de transporte - 17'),
        ('25', 'Manifesto de carga - 25'),
        ('20', 'Ordem de coleta de carga - 20'),
    #)),
)
MODELO_FISCAL_DICT = dict(MODELO_FISCAL)

MODELO_FISCAL_CUPOMFISCAL = (
    #('TRANSPORTE', (
        ('2E', 'bilhete de passagem emitido por ECF - 2E'),
    #)),
    #('MERCADORIAS E SERVICOS', (
        ('2D', 'CF ECF - 2D'),
        ('2C', 'CF PDV - 2C'),
        ('2B', 'CF por máquina registradora - 2B'),
        ('02', 'NF de venda a consumidor - 02'),
        ('59', 'CF-e - 59'),
        ('60', 'CF-e ECF - 60'),
    #)),
)
MODELO_FISCAL_CUPOMFISCAL_DICT = dict(MODELO_FISCAL_CUPOMFISCAL)

MODELO_FISCAL_NFE = '55'
MODELO_FISCAL_NFCE = '65'
MODELO_FISCAL_NFSE = 'SE'
MODELO_FISCAL_CUPOM_FISCAL_ECF = '2D'
MODELO_FISCAL_CTE = '57'


MODELO_FISCAL_REFERENCIADO = (
    ('55', 'NF-e - 55'),
    ('01', 'NF - 01, 1A'),
    ('1B', 'NF avulsa - 1B'),
    ('04', 'NF de produtor rural - 04'),
    ('2D', 'CF ECF - 2D'),
    ('2C', 'CF PDV - 2C'),
    ('2B', 'CF por máquina registradora - 2B'),
    ('59', 'CF-e - 59'),
    ('60', 'CF-e ECF - 60'),
    ('57', 'CT-e - 57'),
)
MODELO_FISCAL_REFERENCIADO_DICT = dict(MODELO_FISCAL_REFERENCIADO)

MODELO_FISCAL_REFERENCIADO_FILTRO = (
    '55',
    '01',
    '1B',
    '04',
    '2D',
    '2C',
    '2B',
    '59',
    '60',
    '57',
    )

ORIGEM_MERCADORIA = (
    ('0', '0 - Nacional'),
    ('1', '1 - Estrangeira - importação direta'),
    ('2', '2 - Estrangeira - adquirida no mercado interno'),
    ('3', '3 - Nacional - conteúdo de importação superior a 40%'),
    ('4', '4 - Nacional - produção feita em conformidade com os processos produtivos básicos de que tratam o decreto-lei nº 288/67, e as leis nº 8.248/91, nº 8.387/91, nº 10.176/01 e nº 11.484/07'),
    ('5', '5 - Nacional - conteúdo de importação inferior ou igual a 40%'),
    ('6', '6 - Estrangeira - importação direta, sem similar nacional, constante em lista de resolução CAMEX'),
    ('7', '7 - Estrangeira - adquirida no mercado interno, sem similar nacional, constante em lista de RESOLUÇÃO CAMEX'),
    ('8', '8 - Nacional - conteúdo de importação superior a 70%'),
)
ORIGEM_MERCADORIA_DICT = dict(ORIGEM_MERCADORIA)

ORIGEM_MERCADORIA_NACIONAL = '0'
ORIGEM_MERCADORIA_IMPORTACAO_DIRETA = '1'
ORIGEM_MERCADORIA_IMPORTACAO_INDIRETA = '2'
ORIGEM_MERCADORIA_ALIQUOTA_4 = ['1', '2', '3', '8']


PROCESSO_EMISSAO_NFE = (
    ('0', 'Contribuinte - aplicativo próprio'),
    ('1', 'Fisco - avulsa'),
    ('2', 'Contribuinte - avulsa'),
    ('3', 'Contribuinte - aplicativo do fisco'),
)
PROCESSO_EMISSAO_NFE_DICT = dict(PROCESSO_EMISSAO_NFE)

PROCESSO_EMISSAO_NFE_CONTRIBUINTE_PROPRIO = '0'
PROCESSO_EMISSAO_NFE_FISCO_AVULSA = '1'
PROCESSO_EMISSAO_NFE_CONTRIBUINTE_AVULSA = '2'
PROCESSO_EMISSAO_NFE_CONTRIBUINTE_APLICATIVO_FISCO = '3'


REGIME_TRIBUTARIO = (
    ('1', 'SIMPLES'),
    ('2', 'SIMPLES - excesso de sublimite de receita bruta'),
    ('3', 'Regime normal - lucro presumido'),
    ('3.1', 'Regime normal - lucro real'),
)
REGIME_TRIBUTARIO_DICT = dict(REGIME_TRIBUTARIO)

REGIME_TRIBUTARIO_SIMPLES = '1'
REGIME_TRIBUTARIO_SIMPLES_EXCESSO = '2'
REGIME_TRIBUTARIO_NORMAL = '3'
REGIME_TRIBUTARIO_LUCRO_PRESUMIDO = '3'
REGIME_TRIBUTARIO_LUCRO_REAL = '3.1'

REGIME_TRIBUTARIO_OPERACAO_NORMAL = (
    ('2', 'SIMPLES - excesso de sublimite de receita bruta'),
    ('3', 'Regime normal - lucro presumido'),
    ('3.1', 'Regime normal - lucro real'),
)
REGIME_TRIBUTARIO_OPERACAO_NORMAL_DICT = dict(REGIME_TRIBUTARIO_OPERACAO_NORMAL)

SITUACAO_FISCAL = (
    ('00', 'Regular'),
    ('01', 'Regular extemporâneo'),
    ('02', 'Cancelado'),
    ('03', 'Cancelado extemporâneo'),
    ('04', 'Denegado - NF-e ou CT-e'),
    ('05', 'Numeração inutilizada - NF-e ou CT-e'),
    ('06', 'Complementar'),
    ('07', 'Complementar extemporâneo'),
    ('08', 'Regime especial ou norma específica'),
    ('NC', 'Mercadoria não circulou'),
    ('MR', 'Mercadoria não recebida'),
)
SITUACAO_FISCAL_DICT = dict(SITUACAO_FISCAL)

SITUACAO_FISCAL_REGULAR = '00'
SITUACAO_FISCAL_REGULAR_EXTEMPORANEO = '01'
SITUACAO_FISCAL_CANCELADO = '02'
SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO = '03'
SITUACAO_FISCAL_DENEGADO = '04'
SITUACAO_FISCAL_INUTILIZADO = '05'
SITUACAO_FISCAL_COMPLEMENTAR = '06'
SITUACAO_FISCAL_COMPLEMENTAR_EXTEMPORANEO = '07'
SITUACAO_FISCAL_REGIME_ESPECIAL = '08'
SITUACAO_FISCAL_MERCADORIA_NAO_CIRCULOU = 'NC'
SITUACAO_FISCAL_MERCADORIA_NAO_RECEBIDA = 'MR'

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
    SITUACAO_FISCAL_COMPLEMENTAR_EXTEMPORANEO
)

ST_ICMS = (
    ('00', '00 - Tributada'),
    ('10', '10 - Tributada e com cobrança de ICMS por ST'),
    ('20', '20 - Com redução da BC'),
    ('30', '30 - Isenta ou não tributada com cobrança de ICMS por ST'),
    ('40', '40 - Isenta'),
    ('41', '41 - Não tributada'),
    ('50', '50 - Suspensão'),
    ('51', '51 - Diferimento'),
    ('60', '60 - ICMS cobrado anteriormente por ST'),
    ('70', '70 - Com redução da BC e cobrança do ICMS por ST'),
    ('90', '90 - Outras'),
)
ST_ICMS_DICT = dict(ST_ICMS)

ST_ICMS_INTEGRAL = '00'
ST_ICMS_ST = '10'
ST_ICMS_REDUCAO = '20'
ST_ICMS_ISENTA_COM_ST = '30'
ST_ICMS_ISENTA = '40'
ST_ICMS_NAO_TRIBUTADA = '41'
ST_ICMS_SUSPENSAO = '50'
ST_ICMS_DIFERIMENTO = '51'
ST_ICMS_ANTERIOR = '60'
ST_ICMS_REDUCAO_COM_ST = '70'
ST_ICMS_OUTRAS = '90'
ST_ICMS_CALCULA_PROPRIO = (ST_ICMS_INTEGRAL, ST_ICMS_ST, ST_ICMS_REDUCAO, ST_ICMS_ISENTA_COM_ST, \
    ST_ICMS_ANTERIOR, ST_ICMS_REDUCAO_COM_ST)
ST_ICMS_COM_REDUCAO = (ST_ICMS_REDUCAO, ST_ICMS_ISENTA_COM_ST, \
    ST_ICMS_ANTERIOR, ST_ICMS_REDUCAO_COM_ST)
ST_ICMS_CALCULA_ST = (ST_ICMS_ST, ST_ICMS_ISENTA_COM_ST, ST_ICMS_REDUCAO_COM_ST)
ST_ICMS_ZERA_ICMS_PROPRIO = (ST_ICMS_ISENTA_COM_ST,)

ST_ICMS_SN = (
    ('101', '101 - Tributada com permissão de crédito'),
    ('102', '102 - Tributada sem permissão de crédito'),
    ('103', '103 - Isento de icms para a faixa de receita bruta'),
    ('201', '201 - Tributada com permissão de crédito e cobrança de ICMS por ST'),
    ('202', '202 - Tributada sem permissão de crédito e cobrança de ICMS por ST'),
    ('203', '203 - Isento de ICMS para a faixa de receita bruta e cobrança de ICMS por ST'),
    ('300', '300 - Imune'),
    ('400', '400 - Não tributada pelo SIMPLES'),
    ('500', '500 - ICMS cobrado anteriormente por ST ou por antecipação'),
    ('900', '900 - Outros'),
)
ST_ICMS_SN_DICT = dict(ST_ICMS_SN)

ST_ICMS_SN_TRIB_COM_CREDITO = '101'
ST_ICMS_SN_TRIB_SEM_CREDITO = '102'
ST_ICMS_SN_ISENTO_ICMS = '103'
ST_ICMS_SN_TRIB_COM_CREDITO_COM_ST = '201'
ST_ICMS_SN_TRIB_SEM_CREDITO_COM_ST = '202'
ST_ICMS_SN_ISENTO_ICMS_COM_ST = '203'
ST_ICMS_SN_IMUNE = '300'
ST_ICMS_SN_NAO_TRIBUTADA = '400'
ST_ICMS_SN_ANTERIOR = '500'
ST_ICMS_SN_OUTRAS = '900'
ST_ICMS_SN_CALCULA_CREDITO = (ST_ICMS_SN_TRIB_COM_CREDITO, ST_ICMS_SN_TRIB_COM_CREDITO_COM_ST, ST_ICMS_SN_OUTRAS,)
ST_ICMS_SN_CALCULA_ST = (ST_ICMS_SN_TRIB_COM_CREDITO_COM_ST, ST_ICMS_SN_TRIB_SEM_CREDITO_COM_ST, ST_ICMS_SN_OUTRAS,)
ST_ICMS_SN_CALCULA_PROPRIO = (ST_ICMS_SN_OUTRAS,)

ST_ICMS_CODIGO_CEST = (ST_ICMS_ST, ST_ICMS_ISENTA_COM_ST, ST_ICMS_ANTERIOR, ST_ICMS_REDUCAO_COM_ST, ST_ICMS_OUTRAS, \
    ST_ICMS_SN_TRIB_COM_CREDITO_COM_ST, ST_ICMS_SN_TRIB_SEM_CREDITO_COM_ST, ST_ICMS_SN_ISENTO_ICMS_COM_ST, ST_ICMS_SN_ANTERIOR, ST_ICMS_SN_OUTRAS)


ST_IPI = (
    ('00', '00 - Entrada com recuperação de crédito'),
    ('01', '01 - Entrada tributada com alíquota zero'),
    ('02', '02 - Entrada isenta'),
    ('03', '03 - Entrada não tributada'),
    ('04', '04 - Entrada imune'),
    ('05', '05 - Entrada com suspensão'),
    ('49', '49 - Entrada - outras entradas'),
    ('50', '50 - Saída tributada'),
    ('51', '51 - Saída tributada com alíquota zero'),
    ('52', '52 - Saída isenta'),
    ('53', '53 - Saída não tributada'),
    ('54', '54 - Saída imune'),
    ('55', '55 - Saída com suspensão'),
    ('99', '99 - Saída - outras saídas'),
    )
ST_IPI_DICT = dict(ST_IPI)

ST_IPI_ENTRADA = (
    ('00', '00 - Entrada com recuperação de crédito'),
    ('01', '01 - Entrada tributada com alíquota zero'),
    ('02', '02 - Entrada isenta'),
    ('03', '03 - Entrada não tributada'),
    ('04', '04 - Entrada imune'),
    ('05', '05 - Entrada com suspensão'),
    ('49', '49 - Entrada - outras entradas'),
    )
ST_IPI_ENTRADA_DICT = dict(ST_IPI_ENTRADA)

ST_IPI_SAIDA = (
    ('50', '50 - Saída tributada'),
    ('51', '51 - Saída tributada com alíquota zero'),
    ('52', '52 - Saída isenta'),
    ('53', '53 - Saída não tributada'),
    ('54', '54 - Saída imune'),
    ('55', '55 - Saída com suspensão'),
    ('99', '99 - Saída - outras saídas'),
    )
ST_IPI_SAIDA_DICT = dict(ST_IPI_SAIDA)

ST_IPI_ENTRADA_RECUPERACAO_CREDITO = '00'
ST_IPI_ENTRADA_ALIQUOTA_ZERO = '01'
ST_IPI_ENTRADA_ISENTA = '02'
ST_IPI_ENTRADA_NAO_TRIBUTADA = '03'
ST_IPI_ENTRADA_IMUNE = '04'
ST_IPI_ENTRADA_SUSPENSAO = '05'
ST_IPI_ENTRADA_OUTRAS = '49'
ST_IPI_SAIDA_TRIBUTADA = '50'
ST_IPI_SAIDA_ALIQUOTA_ZERO = '51'
ST_IPI_SAIDA_ISENTA = '52'
ST_IPI_SAIDA_NAO_TRIBUTADA = '53'
ST_IPI_SAIDA_IMUNE = '54'
ST_IPI_SAIDA_SUSPENSAO = '55'
ST_IPI_SAIDA_OUTRAS = '99'
ST_IPI_CALCULA = (ST_IPI_ENTRADA_RECUPERACAO_CREDITO, ST_IPI_ENTRADA_OUTRAS, \
    ST_IPI_SAIDA_TRIBUTADA, ST_IPI_SAIDA_OUTRAS)


ST_ISS = (
    ('N', 'N - normal'),
    ('R', 'R - retido'),
    ('S', 'S - substituto'),
    ('I', 'I - isento'),
)
ST_ISS_DICT = dict(ST_ISS)

ST_ISS_NORMAL = 'N'
ST_ISS_RETIDO = 'R'
ST_ISS_SUBSTITUTO = 'S'
ST_ISS_ISENTO = 'I'


ST_PIS = (
    ('01', '01 - Tributável - BC = valor da operação (alíquota normal - cumulativo/não cumulativo)'),
    ('02', '02 - Tributável - BC = valor da operação (alíquota diferenciada)'),
    ('03', '03 - Tributável - BC = quantidade vendida × alíquota por unidade de produto'),
    ('04', '04 - Tributável - tributação monofásica (alíquota zero)'),
    ('05', '05 - Tributável - ST'),
    ('06', '06 - Tributável - alíquota zero'),
    ('07', '07 - Isenta'),
    ('08', '08 - Sem incidência'),
    ('09', '09 - Com suspensão'),
    ('49', '49 - Outras operações de saída'),
    ('50', '50 - Operação com direito a crédito - vinculada exclusivamente a receita tributada no mercado interno'),
    ('51', '51 - Operação com direito a crédito - vinculada exclusivamente a receita não tributada no mercado interno'),
    ('52', '52 - Operação com direito a crédito - vinculada exclusivamente a receita de exportação'),
    ('53', '53 - Operação com direito a crédito - vinculada a receitas tributadas e não-tributadas no mercado interno'),
    ('54', '54 - Operação com direito a crédito - vinculada a receitas tributadas no mercado interno e de exportação'),
    ('55', '55 - Operação com direito a crédito - vinculada a receitas não-tributadas no mercado interno e de exportação'),
    ('56', '56 - Operação com direito a crédito - vinculada a receitas tributadas e não-tributadas no mercado interno, e de exportação'),
    ('60', '60 - Crédito presumido - operação de aquisição vinculada exclusivamente a receita tributada no mercado interno'),
    ('61', '61 - Crédito presumido - operação de aquisição vinculada exclusivamente a receita não-tributada no mercado interno'),
    ('62', '62 - Crédito presumido - operação de aquisição vinculada exclusivamente a receita de exportação'),
    ('63', '63 - Crédito presumido - operação de aquisição vinculada a receitas tributadas e não-tributadas no mercado interno'),
    ('64', '64 - Crédito presumido - operação de aquisição vinculada a receitas tributadas no mercado interno e de exportação'),
    ('65', '65 - Crédito presumido - operação de aquisição vinculada a receitas não-tributadas no mercado interno e de exportação'),
    ('66', '66 - Crédito presumido - operação de aquisição vinculada a receitas tributadas e não-tributadas no mercado interno, e de exportação'),
    ('67', '67 - Crédito presumido - outras operações'),
    ('70', '70 - Operação de aquisição sem direito a crédito'),
    ('71', '71 - Operação de aquisição com isenção'),
    ('72', '72 - Operação de aquisição com suspensão'),
    ('73', '73 - Operação de aquisição a alíquota zero'),
    ('74', '74 - Operação de aquisição sem incidência da contribuição'),
    ('75', '75 - Operação de aquisição por ST'),
    ('98', '98 - Outras operações de entrada'),
    ('99', '99 - Outras operações'),
)
ST_PIS_DICT = dict(ST_PIS)

ST_PIS_ENTRADA = (
    ('50', '50 - Operação com direito a crédito - vinculada exclusivamente a receita tributada no mercado interno'),
    ('51', '51 - Operação com direito a crédito - vinculada exclusivamente a receita não tributada no mercado interno'),
    ('52', '52 - Operação com direito a crédito - vinculada exclusivamente a receita de exportação'),
    ('53', '53 - Operação com direito a crédito - vinculada a receitas tributadas e não-tributadas no mercado interno'),
    ('54', '54 - Operação com direito a crédito - vinculada a receitas tributadas no mercado interno e de exportação'),
    ('55', '55 - Operação com direito a crédito - vinculada a receitas não-tributadas no mercado interno e de exportação'),
    ('56', '56 - Operação com direito a crédito - vinculada a receitas tributadas e não-tributadas no mercado interno, e de exportação'),
    ('60', '60 - Crédito presumido - operação de aquisição vinculada exclusivamente a receita tributada no mercado interno'),
    ('61', '61 - Crédito presumido - operação de aquisição vinculada exclusivamente a receita não-tributada no mercado interno'),
    ('62', '62 - Crédito presumido - operação de aquisição vinculada exclusivamente a receita de exportação'),
    ('63', '63 - Crédito presumido - operação de aquisição vinculada a receitas tributadas e não-tributadas no mercado interno'),
    ('64', '64 - Crédito presumido - operação de aquisição vinculada a receitas tributadas no mercado interno e de exportação'),
    ('65', '65 - Crédito presumido - operação de aquisição vinculada a receitas não-tributadas no mercado interno e de exportação'),
    ('66', '66 - Crédito presumido - operação de aquisição vinculada a receitas tributadas e não-tributadas no mercado interno, e de exportação'),
    ('67', '67 - Crédito presumido - outras operações'),
    ('70', '70 - Operação de aquisição sem direito a crédito'),
    ('71', '71 - Operação de aquisição com isenção'),
    ('72', '72 - Operação de aquisição com suspensão'),
    ('73', '73 - Operação de aquisição a alíquota zero'),
    ('74', '74 - Operação de aquisição sem incidência da contribuição'),
    ('75', '75 - Operação de aquisição por ST'),
    ('98', '98 - Outras operações de entrada'),
    )
ST_PIS_ENTRADA_DICT = dict(ST_PIS_ENTRADA)

ST_PIS_SAIDA = (
    ('01', '01 - Tributável - BC = valor da operação (alíquota normal - cumulativo/não cumulativo)'),
    ('02', '02 - Tributável - BC = valor da operação (alíquota diferenciada)'),
    ('03', '03 - Tributável - BC = quantidade vendida × alíquota por unidade de produto'),
    ('04', '04 - Tributável - tributação monofásica (alíquota zero)'),
    ('05', '05 - Tributável - ST'),
    ('06', '06 - Tributável - alíquota zero'),
    ('07', '07 - Isenta'),
    ('08', '08 - Sem incidência'),
    ('09', '09 - Com suspensão'),
    ('49', '49 - Outras operações de saída'),
    ('99', '99 - Outras operações'),
    )
ST_PIS_SAIDA_DICT = dict(ST_PIS_SAIDA)

ST_PIS_TRIB_NORMAL = '01'
ST_PIS_TRIB_DIFERENCIADA = '02'
ST_PIS_TRIB_QUANTIDADE = '03'
ST_PIS_TRIB_MONOFASICA = '04'
ST_PIS_TRIB_SUBSTITUICAO = '05'
ST_PIS_TRIB_ALIQUOTA_ZERO = '06'
ST_PIS_ISENTA = '07'
ST_PIS_SEM_INCIDENCIA = '08'
ST_PIS_COM_SUSPENSAO = '09'
ST_PIS_CRED_EXCL_TRIB_MERC_INTERNO = '50'
ST_PIS_CRED_EXCL_NAO_TRIB_MERC_INTERNO = '51'
ST_PIS_CRED_EXCL_EXPORTACAO = '52'
ST_PIS_CRED_TRIB_MERC_INTERNO = '53'
ST_PIS_CRED_TRIB_MERC_INTERNO_EXPORTACAO = '54'
ST_PIS_CRED_NAO_TRIB_MERC_INTERNO_EXPORTACAO = '55'
ST_PIS_CRED_TRIB_NAO_TRIB_MERC_INTERNO_EXPORTACAO = '56'
ST_PIS_CRED_PRESUMIDO_EXCL_TRIB_MERC_INTERNO = '60'
ST_PIS_CRED_PRESUMIDO_EXCL_NAO_TRIB_MERC_INTERNO = '61'
ST_PIS_CRED_PRESUMIDO_EXCL_EXPORTACAO = '62'
ST_PIS_CRED_PRESUMIDO_TRIB_MERC_INTERNO = '63'
ST_PIS_CRED_PRESUMIDO_TRIB_MERC_INTERNO_EXPORTACAO = '64'
ST_PIS_CRED_PRESUMIDO_NAO_TRIB_MERC_INTERNO_EXPORTACAO = '65'
ST_PIS_CRED_PRESUMIDO_TRIB_NAO_TRIB_MERC_INTERNO_EXPORTACAO = '66'
ST_PIS_CRED_PRESUMIDO_OUTRAS = '67'
ST_PIS_AQUIS_SEM_CREDITO = '70'
ST_PIS_AQUIS_ISENTA = '71'
ST_PIS_AQUIS_COM_SUSPENSAO = '72'
ST_PIS_AQUIS_ALIQUOTA_ZERO = '73'
ST_PIS_AQUIS_SEM_INCIDENCIA = '74'
ST_PIS_AQUIS_SUBSTITUICAO = '75'
ST_PIS_OUTRAS_ENTRADA = '98'
ST_PIS_OUTRAS = '99'
ST_PIS_CALCULA = (ST_PIS_TRIB_NORMAL, ST_PIS_TRIB_DIFERENCIADA, ST_PIS_TRIB_QUANTIDADE, ST_PIS_OUTRAS)
ST_PIS_CALCULA_CREDITO = (ST_PIS_CRED_EXCL_TRIB_MERC_INTERNO, ST_PIS_CRED_EXCL_NAO_TRIB_MERC_INTERNO, ST_PIS_CRED_EXCL_EXPORTACAO, ST_PIS_CRED_TRIB_MERC_INTERNO, ST_PIS_CRED_TRIB_MERC_INTERNO_EXPORTACAO, ST_PIS_CRED_NAO_TRIB_MERC_INTERNO_EXPORTACAO, ST_PIS_CRED_TRIB_NAO_TRIB_MERC_INTERNO_EXPORTACAO)
ST_PIS_CALCULA_ALIQUOTA = (ST_PIS_TRIB_NORMAL, ST_PIS_TRIB_DIFERENCIADA) + ST_PIS_CALCULA_CREDITO
ST_PIS_CALCULA_QUANTIDADE = (ST_PIS_TRIB_QUANTIDADE,)


ST_COFINS = ST_PIS
ST_COFINS_DICT = dict(ST_COFINS)
ST_COFINS_ENTRADA = ST_PIS_ENTRADA
ST_COFINS_ENTRADA_DICT = dict(ST_COFINS_ENTRADA)
ST_COFINS_SAIDA = ST_PIS_SAIDA
ST_COFINS_SAIDA_DICT = dict(ST_COFINS_SAIDA)
ST_COFINS_TRIB_NORMAL = '01'
ST_COFINS_TRIB_DIFERENCIADA = '02'
ST_COFINS_TRIB_QUANTIDADE = '03'
ST_COFINS_TRIB_MONOFASICA = '04'
ST_COFINS_TRIB_SUBSTITUICAO = '05'
ST_COFINS_TRIB_ALIQUOTA_ZERO = '06'
ST_COFINS_ISENTA = '07'
ST_COFINS_SEM_INCIDENCIA = '08'
ST_COFINS_COM_SUSPENSAO = '09'
ST_COFINS_CRED_EXCL_TRIB_MERC_INTERNO = '50'
ST_COFINS_CRED_EXCL_NAO_TRIB_MERC_INTERNO = '51'
ST_COFINS_CRED_EXCL_EXPORTACAO = '52'
ST_COFINS_CRED_TRIB_MERC_INTERNO = '53'
ST_COFINS_CRED_TRIB_MERC_INTERNO_EXPORTACAO = '54'
ST_COFINS_CRED_NAO_TRIB_MERC_INTERNO_EXPORTACAO = '55'
ST_COFINS_CRED_TRIB_NAO_TRIB_MERC_INTERNO_EXPORTACAO = '56'
ST_COFINS_CRED_PRESUMIDO_EXCL_TRIB_MERC_INTERNO = '60'
ST_COFINS_CRED_PRESUMIDO_EXCL_NAO_TRIB_MERC_INTERNO = '61'
ST_COFINS_CRED_PRESUMIDO_EXCL_EXPORTACAO = '62'
ST_COFINS_CRED_PRESUMIDO_TRIB_MERC_INTERNO = '63'
ST_COFINS_CRED_PRESUMIDO_TRIB_MERC_INTERNO_EXPORTACAO = '64'
ST_COFINS_CRED_PRESUMIDO_NAO_TRIB_MERC_INTERNO_EXPORTACAO = '65'
ST_COFINS_CRED_PRESUMIDO_TRIB_NAO_TRIB_MERC_INTERNO_EXPORTACAO = '66'
ST_COFINS_CRED_PRESUMIDO_OUTRAS = '67'
ST_COFINS_AQUIS_SEM_CREDITO = '70'
ST_COFINS_AQUIS_ISENTA = '71'
ST_COFINS_AQUIS_COM_SUSPENSAO = '72'
ST_COFINS_AQUIS_ALIQUOTA_ZERO = '73'
ST_COFINS_AQUIS_SEM_INCIDENCIA = '74'
ST_COFINS_AQUIS_SUBSTITUICAO = '75'
ST_COFINS_OUTRAS_ENTRADA = '98'
ST_COFINS_OUTRAS = '99'
ST_COFINS_CALCULA = (ST_COFINS_TRIB_NORMAL, ST_COFINS_TRIB_DIFERENCIADA, ST_COFINS_TRIB_QUANTIDADE, ST_COFINS_OUTRAS)
ST_COFINS_CALCULA_ALIQUOTA = (ST_COFINS_TRIB_NORMAL, ST_COFINS_TRIB_DIFERENCIADA)
ST_COFINS_CALCULA_QUANTIDADE = (ST_COFINS_TRIB_QUANTIDADE,)


TIPO_EMISSAO = (
    ('0', 'Emissão própria'),
    ('1', 'Emissão por terceiros'),
    )
TIPO_EMISSAO_DICT = dict(TIPO_EMISSAO)

TIPO_EMISSAO_PROPRIA = '0'
TIPO_EMISSAO_TERCEIROS = '1'

TIPO_EMISSAO_TODAS = (
    ('%', 'Todas'),
    ('0', 'Emissão própria'),
    ('1', 'Emissão por terceiros'),
    )
TIPO_EMISSAO_TODAS_DICT = dict(TIPO_EMISSAO_TODAS)


TIPO_EMISSAO_NFE = (
    ('1', 'Normal'),
    ('2', 'Contingência FS-IA'),
    ('3', 'Contingência SCAN'),
    ('4', 'Contingência DPEC'),
    ('5', 'Contingência FS-DA'),
    ('6', 'Contingência SVC-AN'),
    ('7', 'Contingência SVC-RS'),
    ('9', 'Contingência offline NFC-e'),
)
TIPO_EMISSAO_NFE_DICT = dict(TIPO_EMISSAO_NFE)

TIPO_EMISSAO_NFE_NORMAL = '1'
TIPO_EMISSAO_NFE_CONTINGENCIA_FSIA = '2'
TIPO_EMISSAO_NFE_CONTINGENCIA_SCAN = '3'
TIPO_EMISSAO_NFE_CONTINGENCIA_DPEC = '4'
TIPO_EMISSAO_NFE_CONTINGENCIA_FSDA = '5'
TIPO_EMISSAO_NFE_CONTINGENCIA_SVCAN = '6'
TIPO_EMISSAO_NFE_CONTINGENCIA_SVCRS = '7'
TIPO_EMISSAO_NFE_CONTINGENCIA_OFFLINE_NFCE = '9'


TIPO_IMPRESSAO_NFE = (
    ('1', 'DANFE retrato'),
    ('2', 'DANFE paisagem'),
    ('3', 'DANFE simplificado'),
    ('4', 'DANFE NFC-e'),
    ('5', 'DANFE NFC-e eletrônico'),
)
TIPO_IMPRESSAO_NFE_DICT = dict(TIPO_IMPRESSAO_NFE)

TIPO_IMPRESSAO_NFE_RETRATO = '1'
TIPO_IMPRESSAO_NFE_PAISAGEM = '2'
TIPO_IMPRESSAO_NFE_SIMPLIFICADO = '3'
TIPO_IMPRESSAO_NFCE_NORMAL = '4'
TIPO_IMPRESSAO_NFCE_ELETRONICO = '5'


VERSAO_NFE = (
    ('1.10', 'Versão 1.10'),
    ('2.00', 'Versão 2.00'),
    ('3.10', 'Versão 3.10'),
)
VERSAO_NFE_DICT = dict(VERSAO_NFE)

VERSAO_NFE_110 = '1.10'
VERSAO_NFE_200 = '2.00'
VERSAO_NFE_310 = '3.10'


TIPO_PRODUTO_SERVICO = (
    ('00', 'Mercadoria para revenda'),
    ('01', 'Matéria-prima'),
    ('02', 'Embalagem'),
    ('03', 'Produto em processo'),
    ('04', 'Produto acabado'),
    ('05', 'Subproduto'),
    ('06', 'Produto intermediário'),
    ('07', 'Material de uso e consumo'),
    ('08', 'Ativo imobilizado'),
    ('09', 'Serviços'),
    ('10', 'Outros insumos'),
    ('99', 'Outros'),
    )
TIPO_PRODUTO_SERVICO_DICT = dict(TIPO_PRODUTO_SERVICO)

TIPO_PRODUTO_SERVICO_MERCADORIA_PARA_REVENDA = '00'
TIPO_PRODUTO_SERVICO_MATERIA_PRIMA = '01'
TIPO_PRODUTO_SERVICO_EMBALAGEM = '02'
TIPO_PRODUTO_SERVICO_PRODUTO_EM_PROCESSO = '03'
TIPO_PRODUTO_SERVICO_PRODUTO_ACABADO = '04'
TIPO_PRODUTO_SERVICO_SUBPRODUTO = '05'
TIPO_PRODUTO_SERVICO_PRODUTO_INTERMEDIARIO = '06'
TIPO_PRODUTO_SERVICO_MATERIAL_USO_CONSUMO = '07'
TIPO_PRODUTO_SERVICO_ATIVO_IMOBILIZADO = '08'
TIPO_PRODUTO_SERVICO_SERVICOS = '09'
TIPO_PRODUTO_SERVICO_OUTROS_INSUMOS = '10'
TIPO_PRODUTO_SERVICO_OUTROS = '99'


APURACAO_IPI = (
    ('0', 'Mensal'),
    ('1', 'Decendial'),
)
APURACAO_IPI_DICT = dict(APURACAO_IPI)

APURACAO_IPI_MENSAL = '0'
APURACAO_IPI_DECENDIAL = '1'


SITUACAO_NFE = (
    ('em_digitacao', 'Em digitação'),
    ('a_enviar', 'Aguardando envio'),
    ('enviada', 'Aguardando processamento'),
    ('rejeitada', 'RejEitada'),
    ('autorizada', 'Autorizada'),
    ('cancelada', 'Cancelada'),
    ('denegada', 'Denegada'),
    ('inutilizada', 'Inutilizada'),
)
SITUACAO_NFE_DICT = dict(SITUACAO_NFE)


NATUREZA_TRIBUTACAO_NFSE = (
    ('0', 'Tributada no município'),
    ('1', 'Tributada fora do município'),
    ('2', 'Isenta'),
    ('3', 'Imune'),
    ('4', 'Suspensa por decisão judicial'),
    ('5', 'Suspensa por procedimento administrativo'),
)

NAT_OP_TRIBUTADA_NO_MUNICIPIO = '0'
NAT_OP_TRIBUTADA_FORA_MUNICIPIO = '1'
NAT_OP_ISENTA = '2'
NAT_OP_IMUNE = '3'
NAT_OP_SUSPENSA_DECISAO_JUDICIAL = '4'
NAT_OP_SUSPENSA_PROCEDIMENTO_ADMINISTRATIVO = '5'


CLASSE_CONSUMO_ENERGIA = (
    ('01', 'Comercial'),
    ('02', 'Consumo próprio'),
    ('03', 'Iluminação pública'),
    ('04', 'Industrial'),
    ('05', 'Poder público'),
    ('06', 'Residencial'),
    ('07', 'Rural'),
    ('08', 'Serviço público'),
)


TIPO_LIGACAO_ENERGIA = (
    ('1', 'Monofásica'),
    ('2', 'Bifásica'),
    ('3', 'Trifásica'),
)


GRUPO_TENSAO_ENERGIA = (
    ('01', 'A1 - Alta tensão (230 kV ou mais)'),
    ('02', 'A2 - Alta tensão (88 a 138 kV)'),
    ('03', 'A3 - Alta tensão (69 kV)'),
    ('04', 'A3a - Alta tensão (30 kV a 44 kV)'),
    ('05', 'A4 - Alta tensão (2,3 kV a 25 kV)'),
    ('06', 'AS - Alta tensão subterrâneo'),
    ('07', 'B1 - Residencial'),
    ('08', 'B1 - Residencial de baixa renda'),
    ('09', 'B2 - Rural'),
    ('10', 'B2 - Cooperativa de eletrificação rural'),
    ('11', 'B2 - Serviço público de irrigação'),
    ('12', 'B3 - Demais classes'),
    ('13', 'B4a - Iluminação pública - rede de distribuição'),
    ('14', 'B4b - Iluminação pública - bulbo de lâmpada'),
)


CLASSE_CONSUMO_GAS = CLASSE_CONSUMO_ENERGIA


CLASSE_CONSUMO_AGUA = (
    ('00', 'Registro consolidando os documentos de consumo residencial até R$ 50,00'),
    ('01', 'Registro consolidando os documentos de consumo residencial de R$ 50,01 a R$ 100,00'),
    ('02', 'Registro consolidando os documentos de consumo residencial de R$ 100,01 a R$ 200,00'),
    ('03', 'Registro consolidando os documentos de consumo residencial de R$ 200,01 a R$ 300,00'),
    ('04', 'Registro consolidando os documentos de consumo residencial de R$ 300,01 a R$ 400,00'),
    ('05', 'Registro consolidando os documentos de consumo residencial de R$ 400,01 a R$ 500,00'),
    ('06', 'Registro consolidando os documentos de consumo residencial de R$ 500,01 a R$ 1000,00'),
    ('07', 'Registro consolidando os documentos de consumo residencial acima de R$ 1.000,01'),
    ('20', 'Registro consolidando os documentos de consumo comercial/industrial até R$ 50,00'),
    ('21', 'Registro consolidando os documentos de consumo comercial/industrial de R$ 50,01 a R$ 100,00'),
    ('22', 'Registro consolidando os documentos de consumo comercial/industrial de R$ 100,01 a R$ 200,00'),
    ('23', 'Registro consolidando os documentos de consumo comercial/industrial de R$ 200,01 a R$ 300,00'),
    ('24', 'Registro consolidando os documentos de consumo comercial/industrial de R$ 300,01 a R$ 400,00'),
    ('25', 'Registro consolidando os documentos de consumo comercial/industrial de R$ 400,01 a R$ 500,00'),
    ('26', 'Registro consolidando os documentos de consumo comercial/industrial de R$ 500,01 a R$ 1.000,00'),
    ('27', 'Registro por documento fiscal de consumo comercial/industrial acima de R$ 1.000,01'),
    ('80', 'Registro consolidando os documentos de consumo de órgão público'),
    ('90', 'Registro consolidando os documentos de outros tipos de consumo até R$ 50,00'),
    ('91', 'Registro consolidando os documentos de outros tipos de consumo de R$ 50,01 a R$ 100,00'),
    ('92', 'Registro consolidando os documentos de outros tipos de consumo de R$ 100,01 a R$ 200,00'),
    ('93', 'Registro consolidando os documentos de outros tipos de consumo de R$ 200,01 a R$ 300,00'),
    ('94', 'Registro consolidando os documentos de outros tipos de consumo de R$ 300,01 a R$ 400,00'),
    ('95', 'Registro consolidando os documentos de outros tipos de consumo de R$ 400,01 a R$ 500,00'),
    ('96', 'Registro consolidando os documentos de outros tipos de consumo de R$ 500,01 a R$ 1.000,00'),
    ('97', 'Registro consolidando os documentos de outros tipos de consumo acima de R$ 1.000,01'),
    ('99', 'Registro por documento fiscal emitido'),
)

TIPO_ASSINANTE = (
    ('1', 'Comercial/industrial'),
    ('2', 'Poder público'),
    ('3', 'Residencial/pessoa física'),
    ('4', 'Público'),
    ('5', 'Semi-público'),
    ('6', 'Outros'),
)

#
# Definições da NF-e e NFC-e de 3ª geração
#
IDENTIFICACAO_DESTINO = (
    ('1', 'Operação interna'),
    ('2', 'Operação interestadual'),
    ('3', 'Operação com exterior'),
)

IDENTIFICACAO_DESTINO_INTERNO = '1'
IDENTIFICACAO_DESTINO_INTERESTADUAL = '2'
IDENTIFICACAO_DESTINO_EXTERIOR = '3'

TIPO_CONSUMIDOR_FINAL = (
    ('0', 'Normal'),
    ('1', 'Consumidor final'),
)

TIPO_CONSUMIDOR_FINAL_NORMAL = '0'
TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL = '1'


INDICADOR_PRESENCA_COMPRADOR = (
    ('0', 'Não se aplica'),
    ('1', 'Presencial'),
    ('2', 'Operação pela internet'),
    ('3', 'Operação por teleatendimento'),
    ('4', 'Presencial - entrega em domicílio'),
    ('9', 'Não presencial - outros'),
)

INDICADOR_PRESENCA_COMPRADOR_NAO_SE_APLICA = '0'
INDICADOR_PRESENCA_COMPRADOR_PRESENCIAL = '1'
INDICADOR_PRESENCA_COMPRADOR_INTERNET = '2'
INDICADOR_PRESENCA_COMPRADOR_TELEATENDIMENTO = '3'
INDICADOR_PRESENCA_COMPRADOR_ENTREGA_EM_DOMICILIO = '4'
INDICADOR_PRESENCA_COMPRADOR_OUTROS = '9'


INDICADOR_IE_DESTINATARIO = (
    ('1', 'Contribuinte'),
    ('2', 'Isento'),
    ('9', 'Não contribuinte'),
)
IE_DESTINATARIO = INDICADOR_IE_DESTINATARIO

INDICADOR_IE_DESTINATARIO_CONTRIBUINTE = '1'
INDICADOR_IE_DESTINATARIO_ISENTO = '2'
INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE = '9'

VIA_TRANSPORTE_IMPORTACAO = (
    ('1', 'Marítima'),
    ('1', 'Fluvial'),
    ('1', 'Lacustre'),
    ('1', 'Aérea'),
    ('1', 'Postal'),
    ('1', 'Ferroviária'),
    ('1', 'Rodoviária'),
    ('1', 'Rede de transmissão'),
    ('1', 'Meios próprios'),
    ('1', 'Entrada/saída fictícia'),
)

INTERMEDIACAO_IMPORTACAO = (
    ('1', 'Por conta própria'),
    ('2', 'Por conta e ordem'),
    ('3', 'Por encomenda'),
)

PROVEDOR_NFSE = (
    ('BETHA', 'Betha'),
    ('IPM', 'IPM'),
    ('PRODAM', 'PRODAM'),
    ('BARUERI', 'Barueri'),
    ('JOINVILLE', 'Joinville'),
    ('BOANOTA', 'BoaNota Curitiba'),
    ('PUBLICA', 'Publica'),
    ('JOAO_PESSOA', 'João Pessoa'),
    ('ABRASF', 'ABRASF'),
    ('GIMFES', 'GIMFES'),
    ('NEOGRID', 'NeoGrid'),
)

ALIQUOTAS_ICMS = {
   'AC': {'AC': D('17'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'AL': {'AC': D('12'),'AL': D('18'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'AM': {'AC': D('12'),'AL': D('12'),'AM': D('17'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'AP': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('18'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'BA': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('18'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'CE': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('17'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'DF': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('18'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'ES': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('17'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'GO': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('17'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'MA': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('18'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'MT': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('17'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'MS': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('17'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'MG': {'AC': D( '7'),'AL': D( '7'),'AM': D( '7'),'AP': D( '7'),'BA': D( '7'),'CE': D( '7'),'DF': D( '7'),'ES': D( '7'),'GO': D( '7'),'MA': D( '7'),'MT': D( '7'),'MS': D( '7'),'MG': D('18'),'PA': D( '7'),'PB': D( '7'),'PR': D('12'),'PE': D( '7'),'PI': D( '7'),'RN': D( '7'),'RS': D('12'),'RJ': D('12'),'RO': D( '7'),'RR': D( '7'),'SC': D('12'),'SP': D('12'),'SE': D( '7'),'TO': D( '7')},
   'PA': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('17'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'PB': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('18'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'PR': {'AC': D( '7'),'AL': D( '7'),'AM': D( '7'),'AP': D( '7'),'BA': D( '7'),'CE': D( '7'),'DF': D( '7'),'ES': D( '7'),'GO': D( '7'),'MA': D( '7'),'MT': D( '7'),'MS': D( '7'),'MG': D('12'),'PA': D( '7'),'PB': D( '7'),'PR': D('18'),'PE': D( '7'),'PI': D( '7'),'RN': D( '7'),'RS': D('12'),'RJ': D('12'),'RO': D( '7'),'RR': D( '7'),'SC': D('12'),'SP': D('12'),'SE': D( '7'),'TO': D( '7')},
   'PE': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('18'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'PI': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('17'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'RN': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('18'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'RS': {'AC': D( '7'),'AL': D( '7'),'AM': D( '7'),'AP': D( '7'),'BA': D( '7'),'CE': D( '7'),'DF': D( '7'),'ES': D( '7'),'GO': D( '7'),'MA': D( '7'),'MT': D( '7'),'MS': D( '7'),'MG': D('12'),'PA': D( '7'),'PB': D( '7'),'PR': D('12'),'PE': D( '7'),'PI': D( '7'),'RN': D( '7'),'RS': D('18'),'RJ': D('12'),'RO': D( '7'),'RR': D( '7'),'SC': D('12'),'SP': D('12'),'SE': D( '7'),'TO': D( '7')},
   'RJ': {'AC': D( '7'),'AL': D( '7'),'AM': D( '7'),'AP': D( '7'),'BA': D( '7'),'CE': D( '7'),'DF': D( '7'),'ES': D( '7'),'GO': D( '7'),'MA': D( '7'),'MT': D( '7'),'MS': D( '7'),'MG': D('12'),'PA': D( '7'),'PB': D( '7'),'PR': D('12'),'PE': D( '7'),'PI': D( '7'),'RN': D( '7'),'RS': D('12'),'RJ': D('19'),'RO': D( '7'),'RR': D( '7'),'SC': D('12'),'SP': D('12'),'SE': D( '7'),'TO': D( '7')},
   'RO': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('17.5'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'RR': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('17'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('12')},
   'SC': {'AC': D( '7'),'AL': D( '7'),'AM': D( '7'),'AP': D( '7'),'BA': D( '7'),'CE': D( '7'),'DF': D( '7'),'ES': D( '7'),'GO': D( '7'),'MA': D( '7'),'MT': D( '7'),'MS': D( '7'),'MG': D('12'),'PA': D( '7'),'PB': D( '7'),'PR': D('12'),'PE': D( '7'),'PI': D( '7'),'RN': D( '7'),'RS': D('12'),'RJ': D('12'),'RO': D( '7'),'RR': D( '7'),'SC': D('17'),'SP': D('12'),'SE': D( '7'),'TO': D( '7')},
   'SP': {'AC': D( '7'),'AL': D( '7'),'AM': D( '7'),'AP': D( '7'),'BA': D( '7'),'CE': D( '7'),'DF': D( '7'),'ES': D( '7'),'GO': D( '7'),'MA': D( '7'),'MT': D( '7'),'MS': D( '7'),'MG': D('12'),'PA': D( '7'),'PB': D( '7'),'PR': D('12'),'PE': D( '7'),'PI': D( '7'),'RN': D( '7'),'RS': D('12'),'RJ': D('12'),'RO': D( '7'),'RR': D( '7'),'SC': D('12'),'SP': D('18'),'SE': D( '7'),'TO': D( '7')},
   'SE': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('18'),'TO': D('12')},
   'TO': {'AC': D('12'),'AL': D('12'),'AM': D('12'),'AP': D('12'),'BA': D('12'),'CE': D('12'),'DF': D('12'),'ES': D('12'),'GO': D('12'),'MA': D('12'),'MT': D('12'),'MS': D('12'),'MG': D('12'),'PA': D('12'),'PB': D('12'),'PR': D('12'),'PE': D('12'),'PI': D('12'),'RN': D('12'),'RS': D('12'),'RJ': D('12'),'RO': D('12'),'RR': D('12'),'SC': D('12'),'SP': D('12'),'SE': D('12'),'TO': D('18')},
}

#
# TABELA DE NATUREZA JURÍDICA 2014
#
NATUREZA_JURIDICA = (
       ('2011', 'Empresa pública'),
       ('2038', 'Sociedade de economia mista'),
       ('2046', 'Sociedade anônima aberta'),
       ('2054', 'Sociedade anônima fechada'),
       ('2062', 'Sociedade empresária limitada'),
       ('2070', 'Sociedade empresária em nome coletivo'),
       ('2089', 'Sociedade empresária em comandita simples'),
       ('2097', 'Sociedade empresária em comandita por ações'),
       ('2127', 'Sociedade em conta de participação'),
       ('2135', 'Empresário (individual)'),
       ('2143', 'Cooperativa'),
       ('2151', 'Consórcio de sociedades'),
       ('2160', 'Grupo de sociedades'),
       ('2178', 'Estabelecimento, no Brasil, de sociedade estrangeira'),
       ('2194', 'Estabelecimento, no Brasil, de empresa binacional Argentino-Brasileira'),
       ('2216', 'Empresa domiciliada no exterior'),
       ('2224', 'Clube/fundo de investimento'),
       ('2232', 'Sociedade simples pura'),
       ('2240', 'Sociedade simples limitada'),
       ('2259', 'Sociedade simples em nome coletivo'),
       ('2267', 'Sociedade simples em comandita simples'),
       ('2275', 'Empresa binacional'),
       ('2283', 'Consórcio de empregadores'),
       ('2291', 'Consórcio simples'),
       ('2305', 'Empresa individual de responsabilidade limitada (de natureza empresária)'),
       ('2313', 'Empresa individual de responsabilidade limitada (de natureza simples)'),
)


CFOPS_COMPRA_INDUSTRIALIZACAO = [
    '1101', '1111', '1116', '1120', '1122',         '1401', '1651',
    '2101', '2111', '2116', '2120', '2122',         '2401', '2651',
    '3101',                                 '3127',         '3651'
]

CFOPS_COMPRA_COMERCIALIZACAO = [
    '1102', '1113', '1117', '1118', '1121', '1403', '1652',
    '2102', '2113', '2117', '2118', '2121', '2403', '2652',
    '3102',                                         '3652'
]

CFOPS_COMPRA_ATIVO = [
    '1406', '1551',
    '2406', '2551',
            '3551',
]

CFOPS_USO_CONSUMO = [
    '1407', '1556',
    '2407', '2556',
            '3551',
]

CFOPS_COMPRA_SERVICO = [
    '1933', '1949',
    '2933', '2949',
            '3949',
]

CFOPS_COMPRA = CFOPS_COMPRA_INDUSTRIALIZACAO +  CFOPS_COMPRA_COMERCIALIZACAO + CFOPS_COMPRA_ATIVO + CFOPS_USO_CONSUMO + CFOPS_COMPRA_SERVICO
CFOPS_COMPRA_CUSTO_VENDA = CFOPS_COMPRA_INDUSTRIALIZACAO +  CFOPS_COMPRA_COMERCIALIZACAO + CFOPS_COMPRA_SERVICO



CFOPS_VENDA_MERCADORIA = [
    '5101', '5102', '5103', '5104', '5105', '5106', '5109', '5110', '5111', '5112', '5113', '5114', '5115', '5116', '5117', '5118', '5119', '5120', '5122', '5123', '5251', '5252', '5253', '5254', '5255', '5256', '5257', '5258', '5401', '5402', '5403', '5405', '5651', '5652', '5653', '5654', '5655', '5656', '5667',
    '6102', '6103', '6104', '6105', '6106', '6107', '6108', '6109', '6110', '6111', '6112', '6113', '6114', '6115', '6116', '6117', '6118', '6119', '6120', '6122', '6123', '6251', '6252', '6253', '6254', '6255', '6256', '6257', '6258', '6401', '6402', '6403', '6404', '6651', '6652', '6653', '6654', '6655', '6656', '6667', '6101',
    '7101', '7102', '7105', '7106', '7127', '7251', '7651', '7654', '7667',
]

CFOPS_VENDA_ATIVO = [
    '5551',
    '6551',
    '7551',
]

CFOPS_DEVOLUCAO_VENDA = [
    '1201', '1202', '1203', '1204', '1410', '1411', '1503', '1504', '1553', '1660', '1661', '1662',
    '2201', '2202', '2203', '2204', '2410', '2411', '2503', '2504', '2553', '2660', '2661', '2662',
    '3201', '3202', '3211',
]


CFOPS_CUSTO_ESTOQUE_VENDA_DEVOLUCAO = CFOPS_VENDA_MERCADORIA + CFOPS_VENDA_ATIVO + CFOPS_DEVOLUCAO_VENDA
#CFOPS_CUSTO_ESTOQUE_VENDA_DEVOLUCAO = CFOPS_VENDA_MERCADORIA + CFOPS_DEVOLUCAO_VENDA

CFOPS_DEVOLUCAO_COMPRA = [
    '5201', '5202', '5208', '5209', '5210', '5410', '5411', '5412', '5413', '5503', '5553', '5555', '5556', '5660', '5661', '5662', '5918', '5919', '5921',
    '6201', '6202', '6208', '6209', '6210', '6410', '6411', '6412', '6413', '6503', '6553', '6555', '6556', '6660', '6661', '6662', '6918', '6919', '6921',
    '7201', '7202', '7210', '7211', '7553', '7556', '7930',
]

CFOPS_VENDA_SERVICO = [
    '5933', '5949',
    '6933', '6949',
            '7949',
]
CFOPS_CALCULA_SIMPLES_CSLL_IRPJ = CFOPS_VENDA_MERCADORIA + CFOPS_VENDA_ATIVO + CFOPS_DEVOLUCAO_VENDA + CFOPS_VENDA_SERVICO

#
# Tabelas do SIMPLES
#
SIMPLES_NACIONAL_ANEXOS = (
    ('1'        , 'Anexo 1 - Comércio'),
    ('2'        , 'Anexo 2 - Indústria'),
    ('3'        , 'Anexo 3 - Serviços'),
    ('4'        , 'Anexo 4 - Serviços'),
    ('6'        , 'Anexo 6 - Serviços'),
    ('5_ate_10' , 'Anexo 5 - Serviços - Folha < 10%'),
    ('5_ate_15' , 'Anexo 5 - Serviços - Folha < 15%'),
    ('5_ate_20' , 'Anexo 5 - Serviços - Folha < 20%'),
    ('5_ate_25' , 'Anexo 5 - Serviços - Folha < 25%'),
    ('5_ate_30' , 'Anexo 5 - Serviços - Folha < 30%'),
    ('5_ate_35' , 'Anexo 5 - Serviços - Folha < 35%'),
    ('5_ate_40' , 'Anexo 5 - Serviços - Folha < 40%'),
    ('5_mais_40', 'Anexo 5 - Serviços - Folha >= 40%'),
)

SIMPLES_NACIONAL_TETO_01 = '180000'
SIMPLES_NACIONAL_TETO_02 = '360000'
SIMPLES_NACIONAL_TETO_03 = '540000'
SIMPLES_NACIONAL_TETO_04 = '720000'
SIMPLES_NACIONAL_TETO_05 = '900000'
SIMPLES_NACIONAL_TETO_06 = '1080000'
SIMPLES_NACIONAL_TETO_07 = '1260000'
SIMPLES_NACIONAL_TETO_08 = '1440000'
SIMPLES_NACIONAL_TETO_09 = '1620000'
SIMPLES_NACIONAL_TETO_10 = '1800000'
SIMPLES_NACIONAL_TETO_11 = '1980000'
SIMPLES_NACIONAL_TETO_12 = '2610000'
SIMPLES_NACIONAL_TETO_13 = '2340000'
SIMPLES_NACIONAL_TETO_14 = '2520000'
SIMPLES_NACIONAL_TETO_15 = '2700000'
SIMPLES_NACIONAL_TETO_16 = '2880000'
SIMPLES_NACIONAL_TETO_17 = '3060000'
SIMPLES_NACIONAL_TETO_18 = '3240000'
SIMPLES_NACIONAL_TETO_19 = '3420000'
SIMPLES_NACIONAL_TETO_20 = '3600000'


SIMPLES_NACIONAL_TETOS = (
    (SIMPLES_NACIONAL_TETO_01, 'De R$ 0,00 a R$ 180.000,00'),
    (SIMPLES_NACIONAL_TETO_02, 'De R$ 180.000,01 a R$ 360.000,00'),
    (SIMPLES_NACIONAL_TETO_03, 'De R$ 360.000,01 a R$ 540.000,00'),
    (SIMPLES_NACIONAL_TETO_04, 'De R$ 540.000,01 a R$ 720.000,00'),
    (SIMPLES_NACIONAL_TETO_05, 'De R$ 720.000,01 a R$ 900.000,00'),
    (SIMPLES_NACIONAL_TETO_06, 'De R$ 900.000,01 a R$ 1.080.000,00'),
    (SIMPLES_NACIONAL_TETO_07, 'De R$ 1.080.000,01 a R$ 1.260.000,00'),
    (SIMPLES_NACIONAL_TETO_08, 'De R$ 1.260.000,01 a R$ 1.440.000,00'),
    (SIMPLES_NACIONAL_TETO_09, 'De R$ 1.440.000,01 a R$ 1.620.000,00'),
    (SIMPLES_NACIONAL_TETO_10, 'De R$ 1.620.000,01 a R$ 1.800.000,00'),
    (SIMPLES_NACIONAL_TETO_11, 'De R$ 1.800.000,01 a R$ 1.980.000,00'),
    (SIMPLES_NACIONAL_TETO_12, 'De R$ 1.980.000,01 a R$ 2.160.000,00'),
    (SIMPLES_NACIONAL_TETO_13, 'De R$ 2.160.000,01 a R$ 2.340.000,00'),
    (SIMPLES_NACIONAL_TETO_14, 'De R$ 2.340.000,01 a R$ 2.520.000,00'),
    (SIMPLES_NACIONAL_TETO_15, 'De R$ 2.520.000,01 a R$ 2.700.000,00'),
    (SIMPLES_NACIONAL_TETO_16, 'De R$ 2.700.000,01 a R$ 2.880.000,00'),
    (SIMPLES_NACIONAL_TETO_17, 'De R$ 2.880.000,01 a R$ 3.060.000,00'),
    (SIMPLES_NACIONAL_TETO_18, 'De R$ 3.060.000,01 a R$ 3.240.000,00'),
    (SIMPLES_NACIONAL_TETO_19, 'De R$ 3.240.000,01 a R$ 3.420.000,00'),
    (SIMPLES_NACIONAL_TETO_20, 'De R$ 3.420.000,01 a R$ 3.600.000,00'),
)

SIMPLES_NACIONAL_ANEXO_01 = {
    SIMPLES_NACIONAL_TETO_01: {'al_simples':  D('4.00'), 'al_irpj': D('0.00'), 'al_csll': D('0.00'), 'al_cofins': D('0.00'), 'al_pis': D('0.00'), 'al_cpp': D('2.75'), 'al_icms': D('1.25'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_02: {'al_simples':  D('5.47'), 'al_irpj': D('0.00'), 'al_csll': D('0.00'), 'al_cofins': D('0.86'), 'al_pis': D('0.00'), 'al_cpp': D('2.75'), 'al_icms': D('1.86'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_03: {'al_simples':  D('6.84'), 'al_irpj': D('0.27'), 'al_csll': D('0.31'), 'al_cofins': D('0.95'), 'al_pis': D('0.23'), 'al_cpp': D('2.75'), 'al_icms': D('2.33'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_04: {'al_simples':  D('7.54'), 'al_irpj': D('0.35'), 'al_csll': D('0.35'), 'al_cofins': D('1.04'), 'al_pis': D('0.25'), 'al_cpp': D('2.99'), 'al_icms': D('2.56'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_05: {'al_simples':  D('7.60'), 'al_irpj': D('0.35'), 'al_csll': D('0.35'), 'al_cofins': D('1.05'), 'al_pis': D('0.25'), 'al_cpp': D('3.02'), 'al_icms': D('2.58'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_06: {'al_simples':  D('8.28'), 'al_irpj': D('0.38'), 'al_csll': D('0.38'), 'al_cofins': D('1.15'), 'al_pis': D('0.27'), 'al_cpp': D('3.28'), 'al_icms': D('2.82'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_07: {'al_simples':  D('8.36'), 'al_irpj': D('0.39'), 'al_csll': D('0.39'), 'al_cofins': D('1.16'), 'al_pis': D('0.28'), 'al_cpp': D('3.30'), 'al_icms': D('2.84'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_08: {'al_simples':  D('8.45'), 'al_irpj': D('0.39'), 'al_csll': D('0.39'), 'al_cofins': D('1.17'), 'al_pis': D('0.28'), 'al_cpp': D('3.35'), 'al_icms': D('2.87'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_09: {'al_simples':  D('9.03'), 'al_irpj': D('0.42'), 'al_csll': D('0.42'), 'al_cofins': D('1.25'), 'al_pis': D('0.30'), 'al_cpp': D('3.57'), 'al_icms': D('3.07'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_10: {'al_simples':  D('9.12'), 'al_irpj': D('0.43'), 'al_csll': D('0.43'), 'al_cofins': D('1.26'), 'al_pis': D('0.30'), 'al_cpp': D('3.60'), 'al_icms': D('3.10'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_11: {'al_simples':  D('9.95'), 'al_irpj': D('0.46'), 'al_csll': D('0.46'), 'al_cofins': D('1.38'), 'al_pis': D('0.33'), 'al_cpp': D('3.94'), 'al_icms': D('3.38'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_12: {'al_simples': D('10.04'), 'al_irpj': D('0.46'), 'al_csll': D('0.46'), 'al_cofins': D('1.39'), 'al_pis': D('0.33'), 'al_cpp': D('3.99'), 'al_icms': D('3.41'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_13: {'al_simples': D('10.13'), 'al_irpj': D('0.47'), 'al_csll': D('0.47'), 'al_cofins': D('1.40'), 'al_pis': D('0.33'), 'al_cpp': D('4.01'), 'al_icms': D('3.45'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_14: {'al_simples': D('10.23'), 'al_irpj': D('0.47'), 'al_csll': D('0.47'), 'al_cofins': D('1.42'), 'al_pis': D('0.34'), 'al_cpp': D('4.05'), 'al_icms': D('3.48'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_15: {'al_simples': D('10.32'), 'al_irpj': D('0.48'), 'al_csll': D('0.48'), 'al_cofins': D('1.43'), 'al_pis': D('0.34'), 'al_cpp': D('4.08'), 'al_icms': D('3.51'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_16: {'al_simples': D('11.23'), 'al_irpj': D('0.52'), 'al_csll': D('0.52'), 'al_cofins': D('1.56'), 'al_pis': D('0.37'), 'al_cpp': D('4.44'), 'al_icms': D('3.82'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_17: {'al_simples': D('11.32'), 'al_irpj': D('0.52'), 'al_csll': D('0.52'), 'al_cofins': D('1.57'), 'al_pis': D('0.37'), 'al_cpp': D('4.49'), 'al_icms': D('3.85'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_18: {'al_simples': D('11.42'), 'al_irpj': D('0.53'), 'al_csll': D('0.53'), 'al_cofins': D('1.58'), 'al_pis': D('0.38'), 'al_cpp': D('4.52'), 'al_icms': D('3.88'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_19: {'al_simples': D('11.51'), 'al_irpj': D('0.53'), 'al_csll': D('0.53'), 'al_cofins': D('1.60'), 'al_pis': D('0.38'), 'al_cpp': D('4.56'), 'al_icms': D('3.91'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_20: {'al_simples': D('11.61'), 'al_irpj': D('0.54'), 'al_csll': D('0.54'), 'al_cofins': D('1.60'), 'al_pis': D('0.38'), 'al_cpp': D('4.60'), 'al_icms': D('3.95'), 'al_iss': D('0.00')},
}

SIMPLES_NACIONAL_ANEXO_02 = {
    SIMPLES_NACIONAL_TETO_01: {'al_simples':  D('4.50'), 'al_irpj': D('0.00'), 'al_csll': D('0.00'), 'al_cofins': D('0.00'), 'al_pis': D('0.00'), 'al_cpp': D('2.75'), 'al_icms': D('1.25'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_02: {'al_simples':  D('5.97'), 'al_irpj': D('0.00'), 'al_csll': D('0.00'), 'al_cofins': D('0.86'), 'al_pis': D('0.00'), 'al_cpp': D('2.75'), 'al_icms': D('1.86'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_03: {'al_simples':  D('7.34'), 'al_irpj': D('0.27'), 'al_csll': D('0.31'), 'al_cofins': D('0.95'), 'al_pis': D('0.23'), 'al_cpp': D('2.75'), 'al_icms': D('2.33'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_04: {'al_simples':  D('8.04'), 'al_irpj': D('0.35'), 'al_csll': D('0.35'), 'al_cofins': D('1.04'), 'al_pis': D('0.25'), 'al_cpp': D('2.99'), 'al_icms': D('2.56'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_05: {'al_simples':  D('8.10'), 'al_irpj': D('0.35'), 'al_csll': D('0.35'), 'al_cofins': D('1.05'), 'al_pis': D('0.25'), 'al_cpp': D('3.02'), 'al_icms': D('2.58'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_06: {'al_simples':  D('8.78'), 'al_irpj': D('0.38'), 'al_csll': D('0.38'), 'al_cofins': D('1.15'), 'al_pis': D('0.27'), 'al_cpp': D('3.28'), 'al_icms': D('2.82'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_07: {'al_simples':  D('8.86'), 'al_irpj': D('0.39'), 'al_csll': D('0.39'), 'al_cofins': D('1.16'), 'al_pis': D('0.28'), 'al_cpp': D('3.30'), 'al_icms': D('2.84'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_08: {'al_simples':  D('8.95'), 'al_irpj': D('0.39'), 'al_csll': D('0.39'), 'al_cofins': D('1.17'), 'al_pis': D('0.28'), 'al_cpp': D('3.35'), 'al_icms': D('2.87'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_09: {'al_simples':  D('9.53'), 'al_irpj': D('0.42'), 'al_csll': D('0.42'), 'al_cofins': D('1.25'), 'al_pis': D('0.30'), 'al_cpp': D('3.57'), 'al_icms': D('3.07'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_10: {'al_simples':  D('9.62'), 'al_irpj': D('0.42'), 'al_csll': D('0.42'), 'al_cofins': D('1.26'), 'al_pis': D('0.30'), 'al_cpp': D('3.62'), 'al_icms': D('3.10'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_11: {'al_simples': D('10.45'), 'al_irpj': D('0.46'), 'al_csll': D('0.46'), 'al_cofins': D('1.38'), 'al_pis': D('0.33'), 'al_cpp': D('3.94'), 'al_icms': D('3.38'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_12: {'al_simples': D('10.54'), 'al_irpj': D('0.46'), 'al_csll': D('0.46'), 'al_cofins': D('1.39'), 'al_pis': D('0.33'), 'al_cpp': D('3.99'), 'al_icms': D('3.41'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_13: {'al_simples': D('10.63'), 'al_irpj': D('0.47'), 'al_csll': D('0.47'), 'al_cofins': D('1.40'), 'al_pis': D('0.33'), 'al_cpp': D('4.01'), 'al_icms': D('3.45'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_14: {'al_simples': D('10.73'), 'al_irpj': D('0.47'), 'al_csll': D('0.47'), 'al_cofins': D('1.42'), 'al_pis': D('0.34'), 'al_cpp': D('4.05'), 'al_icms': D('3.48'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_15: {'al_simples': D('10.82'), 'al_irpj': D('0.48'), 'al_csll': D('0.48'), 'al_cofins': D('1.43'), 'al_pis': D('0.34'), 'al_cpp': D('4.08'), 'al_icms': D('3.51'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_16: {'al_simples': D('11.73'), 'al_irpj': D('0.52'), 'al_csll': D('0.52'), 'al_cofins': D('1.56'), 'al_pis': D('0.37'), 'al_cpp': D('4.44'), 'al_icms': D('3.82'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_17: {'al_simples': D('11.82'), 'al_irpj': D('0.52'), 'al_csll': D('0.52'), 'al_cofins': D('1.57'), 'al_pis': D('0.37'), 'al_cpp': D('4.49'), 'al_icms': D('3.85'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_18: {'al_simples': D('11.92'), 'al_irpj': D('0.53'), 'al_csll': D('0.53'), 'al_cofins': D('1.58'), 'al_pis': D('0.38'), 'al_cpp': D('4.52'), 'al_icms': D('3.88'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_19: {'al_simples': D('12.01'), 'al_irpj': D('0.53'), 'al_csll': D('0.53'), 'al_cofins': D('1.60'), 'al_pis': D('0.38'), 'al_cpp': D('4.56'), 'al_icms': D('3.91'), 'al_iss': D('0.50')},
    SIMPLES_NACIONAL_TETO_20: {'al_simples': D('12.11'), 'al_irpj': D('0.54'), 'al_csll': D('0.54'), 'al_cofins': D('1.60'), 'al_pis': D('0.38'), 'al_cpp': D('4.60'), 'al_icms': D('3.95'), 'al_iss': D('0.50')},
}

SIMPLES_NACIONAL_ANEXO_03 = {
    SIMPLES_NACIONAL_TETO_01: {'al_simples':  D('6.00'), 'al_irpj': D('0.00'), 'al_csll': D('0.00'), 'al_cofins': D('0.00'), 'al_pis': D('0.00'), 'al_cpp': D('4.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_02: {'al_simples':  D('8.21'), 'al_irpj': D('0.00'), 'al_csll': D('0.00'), 'al_cofins': D('1.42'), 'al_pis': D('0.00'), 'al_cpp': D('4.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_03: {'al_simples': D('10.26'), 'al_irpj': D('0.48'), 'al_csll': D('0.43'), 'al_cofins': D('1.43'), 'al_pis': D('0.35'), 'al_cpp': D('4.07'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_04: {'al_simples': D('11.31'), 'al_irpj': D('0.53'), 'al_csll': D('0.53'), 'al_cofins': D('1.56'), 'al_pis': D('0.38'), 'al_cpp': D('4.47'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_05: {'al_simples': D('11.40'), 'al_irpj': D('0.53'), 'al_csll': D('0.52'), 'al_cofins': D('1.58'), 'al_pis': D('0.38'), 'al_cpp': D('4.52'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_06: {'al_simples': D('12.42'), 'al_irpj': D('0.57'), 'al_csll': D('0.57'), 'al_cofins': D('1.73'), 'al_pis': D('0.40'), 'al_cpp': D('4.92'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_07: {'al_simples': D('12.54'), 'al_irpj': D('0.59'), 'al_csll': D('0.56'), 'al_cofins': D('1.74'), 'al_pis': D('0.42'), 'al_cpp': D('4.97'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_08: {'al_simples': D('12.68'), 'al_irpj': D('0.59'), 'al_csll': D('0.57'), 'al_cofins': D('1.76'), 'al_pis': D('0.42'), 'al_cpp': D('5.03'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_09: {'al_simples': D('13.55'), 'al_irpj': D('0.63'), 'al_csll': D('0.61'), 'al_cofins': D('1.88'), 'al_pis': D('0.45'), 'al_cpp': D('5.37'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_10: {'al_simples': D('13.68'), 'al_irpj': D('0.63'), 'al_csll': D('0.64'), 'al_cofins': D('1.89'), 'al_pis': D('0.45'), 'al_cpp': D('5.42'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_11: {'al_simples': D('14.93'), 'al_irpj': D('0.69'), 'al_csll': D('0.69'), 'al_cofins': D('2.07'), 'al_pis': D('0.50'), 'al_cpp': D('5.98'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_12: {'al_simples': D('15.06'), 'al_irpj': D('0.69'), 'al_csll': D('0.69'), 'al_cofins': D('2.09'), 'al_pis': D('0.50'), 'al_cpp': D('6.09'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_13: {'al_simples': D('15.20'), 'al_irpj': D('0.71'), 'al_csll': D('0.70'), 'al_cofins': D('2.10'), 'al_pis': D('0.50'), 'al_cpp': D('6.19'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_14: {'al_simples': D('15.35'), 'al_irpj': D('0.71'), 'al_csll': D('0.70'), 'al_cofins': D('2.13'), 'al_pis': D('0.51'), 'al_cpp': D('6.30'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_15: {'al_simples': D('15.48'), 'al_irpj': D('0.72'), 'al_csll': D('0.70'), 'al_cofins': D('2.15'), 'al_pis': D('0.51'), 'al_cpp': D('6.40'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_16: {'al_simples': D('16.85'), 'al_irpj': D('0.78'), 'al_csll': D('0.76'), 'al_cofins': D('2.34'), 'al_pis': D('0.56'), 'al_cpp': D('7.41'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_17: {'al_simples': D('16.98'), 'al_irpj': D('0.78'), 'al_csll': D('0.78'), 'al_cofins': D('2.36'), 'al_pis': D('0.56'), 'al_cpp': D('7.50'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_18: {'al_simples': D('17.13'), 'al_irpj': D('0.80'), 'al_csll': D('0.79'), 'al_cofins': D('2.37'), 'al_pis': D('0.57'), 'al_cpp': D('7.60'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_19: {'al_simples': D('17.27'), 'al_irpj': D('0.80'), 'al_csll': D('0.79'), 'al_cofins': D('2.40'), 'al_pis': D('0.57'), 'al_cpp': D('7.71'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_20: {'al_simples': D('17.42'), 'al_irpj': D('0.81'), 'al_csll': D('0.79'), 'al_cofins': D('2.42'), 'al_pis': D('0.57'), 'al_cpp': D('7.83'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
}

SIMPLES_NACIONAL_ANEXO_04 = {
    SIMPLES_NACIONAL_TETO_01: {'al_simples':  D('4.50'), 'al_irpj': D('0.00'), 'al_csll': D('1.22'), 'al_cofins': D('1.28'), 'al_pis': D('0.00'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_02: {'al_simples':  D('6.54'), 'al_irpj': D('0.00'), 'al_csll': D('1.84'), 'al_cofins': D('1.91'), 'al_pis': D('0.00'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_03: {'al_simples':  D('7.70'), 'al_irpj': D('0.16'), 'al_csll': D('1.85'), 'al_cofins': D('1.95'), 'al_pis': D('0.24'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_04: {'al_simples':  D('8.49'), 'al_irpj': D('0.52'), 'al_csll': D('1.87'), 'al_cofins': D('1.99'), 'al_pis': D('0.27'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_05: {'al_simples':  D('8.97'), 'al_irpj': D('0.89'), 'al_csll': D('1.89'), 'al_cofins': D('2.03'), 'al_pis': D('0.29'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_06: {'al_simples':  D('9.78'), 'al_irpj': D('1.25'), 'al_csll': D('1.91'), 'al_cofins': D('2.07'), 'al_pis': D('0.32'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_07: {'al_simples': D('10.26'), 'al_irpj': D('1.62'), 'al_csll': D('1.93'), 'al_cofins': D('2.11'), 'al_pis': D('0.34'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_08: {'al_simples': D('10.76'), 'al_irpj': D('2.00'), 'al_csll': D('1.95'), 'al_cofins': D('2.15'), 'al_pis': D('0.35'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_09: {'al_simples': D('11.51'), 'al_irpj': D('2.37'), 'al_csll': D('1.97'), 'al_cofins': D('2.19'), 'al_pis': D('0.37'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_10: {'al_simples': D('12.00'), 'al_irpj': D('2.74'), 'al_csll': D('2.00'), 'al_cofins': D('2.23'), 'al_pis': D('0.38'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_11: {'al_simples': D('12.80'), 'al_irpj': D('3.12'), 'al_csll': D('2.01'), 'al_cofins': D('2.27'), 'al_pis': D('0.40'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_12: {'al_simples': D('13.25'), 'al_irpj': D('3.49'), 'al_csll': D('2.03'), 'al_cofins': D('2.31'), 'al_pis': D('0.42'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_13: {'al_simples': D('13.70'), 'al_irpj': D('3.86'), 'al_csll': D('2.05'), 'al_cofins': D('2.35'), 'al_pis': D('0.44'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_14: {'al_simples': D('14.15'), 'al_irpj': D('4.23'), 'al_csll': D('2.07'), 'al_cofins': D('2.39'), 'al_pis': D('0.46'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_15: {'al_simples': D('14.60'), 'al_irpj': D('4.60'), 'al_csll': D('2.10'), 'al_cofins': D('2.43'), 'al_pis': D('0.47'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_16: {'al_simples': D('15.05'), 'al_irpj': D('4.90'), 'al_csll': D('2.19'), 'al_cofins': D('2.47'), 'al_pis': D('0.49'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_17: {'al_simples': D('15.50'), 'al_irpj': D('5.21'), 'al_csll': D('2.27'), 'al_cofins': D('2.51'), 'al_pis': D('0.51'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_18: {'al_simples': D('15.95'), 'al_irpj': D('5.51'), 'al_csll': D('2.36'), 'al_cofins': D('2.55'), 'al_pis': D('0.53'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_19: {'al_simples': D('16.40'), 'al_irpj': D('5.81'), 'al_csll': D('2.45'), 'al_cofins': D('2.59'), 'al_pis': D('0.55'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_20: {'al_simples': D('16.85'), 'al_irpj': D('6.12'), 'al_csll': D('2.53'), 'al_cofins': D('2.63'), 'al_pis': D('0.57'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
}

SIMPLES_NACIONAL_ANEXO_06 = {
    SIMPLES_NACIONAL_TETO_01: {'al_simples': D('16.93'), 'al_irpj': D('7.71'), 'al_csll': D('3.19'), 'al_cofins': D('3.31'), 'al_pis': D('0.72'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_02: {'al_simples': D('17.72'), 'al_irpj': D('7.71'), 'al_csll': D('3.19'), 'al_cofins': D('3.31'), 'al_pis': D('0.72'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_03: {'al_simples': D('18.43'), 'al_irpj': D('7.71'), 'al_csll': D('3.19'), 'al_cofins': D('3.31'), 'al_pis': D('0.72'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_04: {'al_simples': D('18.77'), 'al_irpj': D('7.71'), 'al_csll': D('3.19'), 'al_cofins': D('3.31'), 'al_pis': D('0.72'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_05: {'al_simples': D('19.04'), 'al_irpj': D('7.83'), 'al_csll': D('3.24'), 'al_cofins': D('3.37'), 'al_pis': D('0.73'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_06: {'al_simples': D('19.94'), 'al_irpj': D('8.11'), 'al_csll': D('3.35'), 'al_cofins': D('3.49'), 'al_pis': D('0.76'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_07: {'al_simples': D('20.34'), 'al_irpj': D('8.31'), 'al_csll': D('3.43'), 'al_cofins': D('3.57'), 'al_pis': D('0.77'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_08: {'al_simples': D('20.66'), 'al_irpj': D('8.44'), 'al_csll': D('3.49'), 'al_cofins': D('3.63'), 'al_pis': D('0.79'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_09: {'al_simples': D('21.17'), 'al_irpj': D('8.54'), 'al_csll': D('3.54'), 'al_cofins': D('3.68'), 'al_pis': D('0.80'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_10: {'al_simples': D('21.38'), 'al_irpj': D('8.65'), 'al_csll': D('3.57'), 'al_cofins': D('3.71'), 'al_pis': D('0.80'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_11: {'al_simples': D('21.86'), 'al_irpj': D('8.71'), 'al_csll': D('3.60'), 'al_cofins': D('3.74'), 'al_pis': D('0.81'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_12: {'al_simples': D('21.97'), 'al_irpj': D('8.76'), 'al_csll': D('3.62'), 'al_cofins': D('3.77'), 'al_pis': D('0.82'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_13: {'al_simples': D('22.06'), 'al_irpj': D('8.81'), 'al_csll': D('3.64'), 'al_cofins': D('3.79'), 'al_pis': D('0.82'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_14: {'al_simples': D('22.14'), 'al_irpj': D('8.86'), 'al_csll': D('3.66'), 'al_cofins': D('3.80'), 'al_pis': D('0.82'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_15: {'al_simples': D('22.21'), 'al_irpj': D('8.89'), 'al_csll': D('3.67'), 'al_cofins': D('3.82'), 'al_pis': D('0.83'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_16: {'al_simples': D('22.21'), 'al_irpj': D('8.89'), 'al_csll': D('3.67'), 'al_cofins': D('3.82'), 'al_pis': D('0.83'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_17: {'al_simples': D('22.32'), 'al_irpj': D('8.95'), 'al_csll': D('3.70'), 'al_cofins': D('3.84'), 'al_pis': D('0.83'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_18: {'al_simples': D('22.37'), 'al_irpj': D('8.96'), 'al_csll': D('3.71'), 'al_cofins': D('3.86'), 'al_pis': D('0.84'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_19: {'al_simples': D('22.41'), 'al_irpj': D('8.99'), 'al_csll': D('3.72'), 'al_cofins': D('3.86'), 'al_pis': D('0.84'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_20: {'al_simples': D('22.45'), 'al_irpj': D('9.01'), 'al_csll': D('3.73'), 'al_cofins': D('3.87'), 'al_pis': D('0.84'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
}

SIMPLES_NACIONAL_ANEXO_05_ATE_10 = {
    SIMPLES_NACIONAL_TETO_01: {'al_simples': D('17.50'), 'al_irpj': D('8.01'), 'al_csll': D('3.31'), 'al_cofins': D('3.44'), 'al_pis': D('0.75'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_02: {'al_simples': D('17.52'), 'al_irpj': D('7.61'), 'al_csll': D('3.14'), 'al_cofins': D('3.27'), 'al_pis': D('0.71'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_03: {'al_simples': D('17.55'), 'al_irpj': D('7.26'), 'al_csll': D('3.00'), 'al_cofins': D('3.12'), 'al_pis': D('0.68'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_04: {'al_simples': D('17.95'), 'al_irpj': D('7.29'), 'al_csll': D('3.01'), 'al_cofins': D('3.13'), 'al_pis': D('0.68'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_05: {'al_simples': D('18.15'), 'al_irpj': D('7.37'), 'al_csll': D('3.05'), 'al_cofins': D('3.17'), 'al_pis': D('0.69'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_06: {'al_simples': D('18.45'), 'al_irpj': D('7.34'), 'al_csll': D('3.04'), 'al_cofins': D('3.16'), 'al_pis': D('0.68'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_07: {'al_simples': D('18.55'), 'al_irpj': D('7.39'), 'al_csll': D('3.05'), 'al_cofins': D('3.17'), 'al_pis': D('0.69'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_08: {'al_simples': D('18.62'), 'al_irpj': D('7.39'), 'al_csll': D('3.06'), 'al_cofins': D('3.18'), 'al_pis': D('0.69'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_09: {'al_simples': D('18.72'), 'al_irpj': D('7.28'), 'al_csll': D('3.01'), 'al_cofins': D('3.13'), 'al_pis': D('0.68'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_10: {'al_simples': D('18.86'), 'al_irpj': D('7.35'), 'al_csll': D('3.03'), 'al_cofins': D('3.15'), 'al_pis': D('0.68'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_11: {'al_simples': D('18.96'), 'al_irpj': D('7.21'), 'al_csll': D('2.98'), 'al_cofins': D('3.10'), 'al_pis': D('0.67'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_12: {'al_simples': D('19.06'), 'al_irpj': D('7.26'), 'al_csll': D('3.00'), 'al_cofins': D('3.12'), 'al_pis': D('0.68'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_13: {'al_simples': D('19.26'), 'al_irpj': D('7.36'), 'al_csll': D('3.04'), 'al_cofins': D('3.16'), 'al_pis': D('0.69'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_14: {'al_simples': D('19.56'), 'al_irpj': D('7.53'), 'al_csll': D('3.11'), 'al_cofins': D('3.23'), 'al_pis': D('0.70'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_15: {'al_simples': D('20.70'), 'al_irpj': D('8.11'), 'al_csll': D('3.35'), 'al_cofins': D('3.48'), 'al_pis': D('0.76'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_16: {'al_simples': D('21.20'), 'al_irpj': D('8.37'), 'al_csll': D('3.46'), 'al_cofins': D('3.60'), 'al_pis': D('0.78'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_17: {'al_simples': D('21.70'), 'al_irpj': D('8.62'), 'al_csll': D('3.57'), 'al_cofins': D('3.71'), 'al_pis': D('0.80'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_18: {'al_simples': D('22.20'), 'al_irpj': D('8.87'), 'al_csll': D('3.67'), 'al_cofins': D('3.82'), 'al_pis': D('0.83'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_19: {'al_simples': D('22.50'), 'al_irpj': D('9.04'), 'al_csll': D('3.74'), 'al_cofins': D('3.88'), 'al_pis': D('0.84'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_20: {'al_simples': D('22.90'), 'al_irpj': D('9.24'), 'al_csll': D('3.82'), 'al_cofins': D('3.97'), 'al_pis': D('0.86'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
}

SIMPLES_NACIONAL_ANEXO_05_ATE_15 = {
    SIMPLES_NACIONAL_TETO_01: {'al_simples': D('15.70'), 'al_irpj': D('7.08'), 'al_csll': D('2.92'), 'al_cofins': D('3.04'), 'al_pis': D('0.66'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_02: {'al_simples': D('15.75'), 'al_irpj': D('6.69'), 'al_csll': D('2.77'), 'al_cofins': D('2.88'), 'al_pis': D('0.62'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_03: {'al_simples': D('15.95'), 'al_irpj': D('6.43'), 'al_csll': D('2.66'), 'al_cofins': D('2.76'), 'al_pis': D('0.60'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_04: {'al_simples': D('16.70'), 'al_irpj': D('6.64'), 'al_csll': D('2.75'), 'al_cofins': D('2.85'), 'al_pis': D('0.62'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_05: {'al_simples': D('16.95'), 'al_irpj': D('6.76'), 'al_csll': D('2.79'), 'al_cofins': D('2.90'), 'al_pis': D('0.63'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_06: {'al_simples': D('17.20'), 'al_irpj': D('6.70'), 'al_csll': D('2.77'), 'al_cofins': D('2.88'), 'al_pis': D('0.62'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_07: {'al_simples': D('17.30'), 'al_irpj': D('6.74'), 'al_csll': D('2.78'), 'al_cofins': D('2.89'), 'al_pis': D('0.63'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_08: {'al_simples': D('17.32'), 'al_irpj': D('6.72'), 'al_csll': D('2.78'), 'al_cofins': D('2.89'), 'al_pis': D('0.63'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_09: {'al_simples': D('17.42'), 'al_irpj': D('6.61'), 'al_csll': D('2.73'), 'al_cofins': D('2.84'), 'al_pis': D('0.62'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_10: {'al_simples': D('17.56'), 'al_irpj': D('6.68'), 'al_csll': D('2.76'), 'al_cofins': D('2.87'), 'al_pis': D('0.62'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_11: {'al_simples': D('17.66'), 'al_irpj': D('6.54'), 'al_csll': D('2.70'), 'al_cofins': D('2.81'), 'al_pis': D('0.61'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_12: {'al_simples': D('17.76'), 'al_irpj': D('6.59'), 'al_csll': D('2.72'), 'al_cofins': D('2.83'), 'al_pis': D('0.61'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_13: {'al_simples': D('17.96'), 'al_irpj': D('6.69'), 'al_csll': D('2.77'), 'al_cofins': D('2.88'), 'al_pis': D('0.62'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_14: {'al_simples': D('18.30'), 'al_irpj': D('6.88'), 'al_csll': D('2.84'), 'al_cofins': D('2.95'), 'al_pis': D('0.64'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_15: {'al_simples': D('19.30'), 'al_irpj': D('7.39'), 'al_csll': D('3.05'), 'al_cofins': D('3.17'), 'al_pis': D('0.69'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_16: {'al_simples': D('20.00'), 'al_irpj': D('7.75'), 'al_csll': D('3.20'), 'al_cofins': D('3.33'), 'al_pis': D('0.72'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_17: {'al_simples': D('20.50'), 'al_irpj': D('8.01'), 'al_csll': D('3.31'), 'al_cofins': D('3.44'), 'al_pis': D('0.75'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_18: {'al_simples': D('20.90'), 'al_irpj': D('8.20'), 'al_csll': D('3.39'), 'al_cofins': D('3.53'), 'al_pis': D('0.76'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_19: {'al_simples': D('21.30'), 'al_irpj': D('8.42'), 'al_csll': D('3.48'), 'al_cofins': D('3.62'), 'al_pis': D('0.78'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_20: {'al_simples': D('21.80'), 'al_irpj': D('8.68'), 'al_csll': D('3.59'), 'al_cofins': D('3.73'), 'al_pis': D('0.81'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
}

SIMPLES_NACIONAL_ANEXO_05_ATE_20 = {
    SIMPLES_NACIONAL_TETO_01: {'al_simples': D('13.70'), 'al_irpj': D('6.04'), 'al_csll': D('2.50'), 'al_cofins': D('2.60'), 'al_pis': D('0.56'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_02: {'al_simples': D('13.90'), 'al_irpj': D('5.74'), 'al_csll': D('2.37'), 'al_cofins': D('2.47'), 'al_pis': D('0.53'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_03: {'al_simples': D('14.20'), 'al_irpj': D('5.53'), 'al_csll': D('2.28'), 'al_cofins': D('2.37'), 'al_pis': D('0.51'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_04: {'al_simples': D('15.00'), 'al_irpj': D('5.76'), 'al_csll': D('2.38'), 'al_cofins': D('2.48'), 'al_pis': D('0.54'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_05: {'al_simples': D('15.30'), 'al_irpj': D('5.90'), 'al_csll': D('2.44'), 'al_cofins': D('2.54'), 'al_pis': D('0.55'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_06: {'al_simples': D('15.40'), 'al_irpj': D('5.77'), 'al_csll': D('2.38'), 'al_cofins': D('2.48'), 'al_pis': D('0.54'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_07: {'al_simples': D('15.50'), 'al_irpj': D('5.81'), 'al_csll': D('2.40'), 'al_cofins': D('2.49'), 'al_pis': D('0.54'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_08: {'al_simples': D('15.60'), 'al_irpj': D('5.83'), 'al_csll': D('2.41'), 'al_cofins': D('2.51'), 'al_pis': D('0.54'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_09: {'al_simples': D('15.70'), 'al_irpj': D('5.72'), 'al_csll': D('2.37'), 'al_cofins': D('2.46'), 'al_pis': D('0.53'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_10: {'al_simples': D('15.80'), 'al_irpj': D('5.77'), 'al_csll': D('2.38'), 'al_cofins': D('2.47'), 'al_pis': D('0.54'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_11: {'al_simples': D('15.90'), 'al_irpj': D('5.63'), 'al_csll': D('2.33'), 'al_cofins': D('2.42'), 'al_pis': D('0.52'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_12: {'al_simples': D('16.00'), 'al_irpj': D('5.68'), 'al_csll': D('2.35'), 'al_cofins': D('2.44'), 'al_pis': D('0.53'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_13: {'al_simples': D('16.20'), 'al_irpj': D('5.78'), 'al_csll': D('2.39'), 'al_cofins': D('2.49'), 'al_pis': D('0.54'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_14: {'al_simples': D('16.50'), 'al_irpj': D('5.95'), 'al_csll': D('2.46'), 'al_cofins': D('2.55'), 'al_pis': D('0.55'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_15: {'al_simples': D('17.45'), 'al_irpj': D('6.43'), 'al_csll': D('2.66'), 'al_cofins': D('2.76'), 'al_pis': D('0.60'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_16: {'al_simples': D('18.20'), 'al_irpj': D('6.82'), 'al_csll': D('2.82'), 'al_cofins': D('2.93'), 'al_pis': D('0.63'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_17: {'al_simples': D('18.70'), 'al_irpj': D('7.08'), 'al_csll': D('2.92'), 'al_cofins': D('3.04'), 'al_pis': D('0.66'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_18: {'al_simples': D('19.10'), 'al_irpj': D('7.27'), 'al_csll': D('3.01'), 'al_cofins': D('3.13'), 'al_pis': D('0.68'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_19: {'al_simples': D('19.50'), 'al_irpj': D('7.49'), 'al_csll': D('3.10'), 'al_cofins': D('3.22'), 'al_pis': D('0.70'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_20: {'al_simples': D('20.00'), 'al_irpj': D('7.75'), 'al_csll': D('3.20'), 'al_cofins': D('3.33'), 'al_pis': D('0.72'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
}

SIMPLES_NACIONAL_ANEXO_05_ATE_25 = {
    SIMPLES_NACIONAL_TETO_01: {'al_simples': D('11.82'), 'al_irpj': D('5.07'), 'al_csll': D('2.10'), 'al_cofins': D('2.18'), 'al_pis': D('0.47'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_02: {'al_simples': D('12.60'), 'al_irpj': D('5.07'), 'al_csll': D('2.09'), 'al_cofins': D('2.18'), 'al_pis': D('0.47'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_03: {'al_simples': D('12.90'), 'al_irpj': D('4.85'), 'al_csll': D('2.01'), 'al_cofins': D('2.09'), 'al_pis': D('0.45'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_04: {'al_simples': D('13.70'), 'al_irpj': D('5.09'), 'al_csll': D('2.11'), 'al_cofins': D('2.19'), 'al_pis': D('0.47'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_05: {'al_simples': D('14.03'), 'al_irpj': D('5.25'), 'al_csll': D('2.17'), 'al_cofins': D('2.25'), 'al_pis': D('0.49'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_06: {'al_simples': D('14.10'), 'al_irpj': D('5.10'), 'al_csll': D('2.11'), 'al_cofins': D('2.19'), 'al_pis': D('0.47'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_07: {'al_simples': D('14.11'), 'al_irpj': D('5.10'), 'al_csll': D('2.10'), 'al_cofins': D('2.19'), 'al_pis': D('0.47'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_08: {'al_simples': D('14.12'), 'al_irpj': D('5.07'), 'al_csll': D('2.09'), 'al_cofins': D('2.18'), 'al_pis': D('0.47'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_09: {'al_simples': D('14.13'), 'al_irpj': D('4.91'), 'al_csll': D('2.03'), 'al_cofins': D('2.11'), 'al_pis': D('0.46'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_10: {'al_simples': D('14.14'), 'al_irpj': D('4.91'), 'al_csll': D('2.03'), 'al_cofins': D('2.11'), 'al_pis': D('0.46'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_11: {'al_simples': D('14.49'), 'al_irpj': D('4.90'), 'al_csll': D('2.03'), 'al_cofins': D('2.11'), 'al_pis': D('0.46'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_12: {'al_simples': D('14.67'), 'al_irpj': D('4.99'), 'al_csll': D('2.06'), 'al_cofins': D('2.15'), 'al_pis': D('0.47'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_13: {'al_simples': D('14.86'), 'al_irpj': D('5.09'), 'al_csll': D('2.11'), 'al_cofins': D('2.19'), 'al_pis': D('0.47'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_14: {'al_simples': D('15.46'), 'al_irpj': D('5.41'), 'al_csll': D('2.23'), 'al_cofins': D('2.32'), 'al_pis': D('0.50'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_15: {'al_simples': D('16.24'), 'al_irpj': D('5.80'), 'al_csll': D('2.40'), 'al_cofins': D('2.49'), 'al_pis': D('0.54'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_16: {'al_simples': D('16.91'), 'al_irpj': D('6.15'), 'al_csll': D('2.54'), 'al_cofins': D('2.64'), 'al_pis': D('0.57'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_17: {'al_simples': D('17.40'), 'al_irpj': D('6.40'), 'al_csll': D('2.65'), 'al_cofins': D('2.75'), 'al_pis': D('0.60'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_18: {'al_simples': D('17.80'), 'al_irpj': D('6.60'), 'al_csll': D('2.73'), 'al_cofins': D('2.84'), 'al_pis': D('0.62'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_19: {'al_simples': D('18.20'), 'al_irpj': D('6.82'), 'al_csll': D('2.82'), 'al_cofins': D('2.93'), 'al_pis': D('0.63'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_20: {'al_simples': D('18.60'), 'al_irpj': D('7.02'), 'al_csll': D('2.90'), 'al_cofins': D('3.02'), 'al_pis': D('0.65'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
}

SIMPLES_NACIONAL_ANEXO_05_ATE_30 = {
    SIMPLES_NACIONAL_TETO_01: {'al_simples': D('10.47'), 'al_irpj': D('4.37'), 'al_csll': D('1.81'), 'al_cofins': D('1.88'), 'al_pis': D('0.41'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_02: {'al_simples': D('12.33'), 'al_irpj': D('4.93'), 'al_csll': D('2.04'), 'al_cofins': D('2.12'), 'al_pis': D('0.46'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_03: {'al_simples': D('12.64'), 'al_irpj': D('4.72'), 'al_csll': D('1.95'), 'al_cofins': D('2.03'), 'al_pis': D('0.44'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_04: {'al_simples': D('13.45'), 'al_irpj': D('4.96'), 'al_csll': D('2.05'), 'al_cofins': D('2.13'), 'al_pis': D('0.46'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_05: {'al_simples': D('13.53'), 'al_irpj': D('4.99'), 'al_csll': D('2.06'), 'al_cofins': D('2.14'), 'al_pis': D('0.46'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_06: {'al_simples': D('13.60'), 'al_irpj': D('4.84'), 'al_csll': D('2.00'), 'al_cofins': D('2.08'), 'al_pis': D('0.45'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_07: {'al_simples': D('13.68'), 'al_irpj': D('4.88'), 'al_csll': D('2.01'), 'al_cofins': D('2.09'), 'al_pis': D('0.45'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_08: {'al_simples': D('13.69'), 'al_irpj': D('4.84'), 'al_csll': D('2.00'), 'al_cofins': D('2.08'), 'al_pis': D('0.45'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_09: {'al_simples': D('14.08'), 'al_irpj': D('4.88'), 'al_csll': D('2.02'), 'al_cofins': D('2.10'), 'al_pis': D('0.46'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_10: {'al_simples': D('14.09'), 'al_irpj': D('4.89'), 'al_csll': D('2.02'), 'al_cofins': D('2.10'), 'al_pis': D('0.45'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_11: {'al_simples': D('14.45'), 'al_irpj': D('4.88'), 'al_csll': D('2.02'), 'al_cofins': D('2.10'), 'al_pis': D('0.45'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_12: {'al_simples': D('14.64'), 'al_irpj': D('4.98'), 'al_csll': D('2.06'), 'al_cofins': D('2.14'), 'al_pis': D('0.46'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_13: {'al_simples': D('14.82'), 'al_irpj': D('5.07'), 'al_csll': D('2.10'), 'al_cofins': D('2.18'), 'al_pis': D('0.47'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_14: {'al_simples': D('15.18'), 'al_irpj': D('5.27'), 'al_csll': D('2.17'), 'al_cofins': D('2.26'), 'al_pis': D('0.49'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_15: {'al_simples': D('16.00'), 'al_irpj': D('5.68'), 'al_csll': D('2.35'), 'al_cofins': D('2.44'), 'al_pis': D('0.53'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_16: {'al_simples': D('16.72'), 'al_irpj': D('6.05'), 'al_csll': D('2.50'), 'al_cofins': D('2.60'), 'al_pis': D('0.56'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_17: {'al_simples': D('17.13'), 'al_irpj': D('6.26'), 'al_csll': D('2.59'), 'al_cofins': D('2.69'), 'al_pis': D('0.58'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_18: {'al_simples': D('17.55'), 'al_irpj': D('6.47'), 'al_csll': D('2.68'), 'al_cofins': D('2.79'), 'al_pis': D('0.60'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_19: {'al_simples': D('17.97'), 'al_irpj': D('6.70'), 'al_csll': D('2.77'), 'al_cofins': D('2.88'), 'al_pis': D('0.62'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_20: {'al_simples': D('18.40'), 'al_irpj': D('6.92'), 'al_csll': D('2.86'), 'al_cofins': D('2.97'), 'al_pis': D('0.64'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
}

SIMPLES_NACIONAL_ANEXO_05_ATE_35 = {
    SIMPLES_NACIONAL_TETO_01: {'al_simples': D('9.97'), 'al_irpj': D('4.12'), 'al_csll': D('1.70'), 'al_cofins': D('1.77'), 'al_pis': D('0.38'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_02: {'al_simples': D('10.72'), 'al_irpj': D('4.10'), 'al_csll': D('1.69'), 'al_cofins': D('1.76'), 'al_pis': D('0.38'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_03: {'al_simples': D('11.11'), 'al_irpj': D('3.93'), 'al_csll': D('1.62'), 'al_cofins': D('1.69'), 'al_pis': D('0.37'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_04: {'al_simples': D('12.00'), 'al_irpj': D('4.21'), 'al_csll': D('1.74'), 'al_cofins': D('1.81'), 'al_pis': D('0.39'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_05: {'al_simples': D('12.40'), 'al_irpj': D('4.41'), 'al_csll': D('1.82'), 'al_cofins': D('1.89'), 'al_pis': D('0.41'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_06: {'al_simples': D('12.60'), 'al_irpj': D('4.32'), 'al_csll': D('1.79'), 'al_cofins': D('1.86'), 'al_pis': D('0.40'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_07: {'al_simples': D('12.68'), 'al_irpj': D('4.36'), 'al_csll': D('1.80'), 'al_cofins': D('1.87'), 'al_pis': D('0.41'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_08: {'al_simples': D('12.69'), 'al_irpj': D('4.33'), 'al_csll': D('1.79'), 'al_cofins': D('1.86'), 'al_pis': D('0.40'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_09: {'al_simples': D('13.08'), 'al_irpj': D('4.36'), 'al_csll': D('1.81'), 'al_cofins': D('1.88'), 'al_pis': D('0.41'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_10: {'al_simples': D('13.09'), 'al_irpj': D('4.37'), 'al_csll': D('1.80'), 'al_cofins': D('1.87'), 'al_pis': D('0.41'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_11: {'al_simples': D('13.61'), 'al_irpj': D('4.45'), 'al_csll': D('1.84'), 'al_cofins': D('1.91'), 'al_pis': D('0.41'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_12: {'al_simples': D('13.81'), 'al_irpj': D('4.55'), 'al_csll': D('1.88'), 'al_cofins': D('1.96'), 'al_pis': D('0.42'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_13: {'al_simples': D('14.17'), 'al_irpj': D('4.74'), 'al_csll': D('1.96'), 'al_cofins': D('2.04'), 'al_pis': D('0.44'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_14: {'al_simples': D('14.61'), 'al_irpj': D('4.97'), 'al_csll': D('2.05'), 'al_cofins': D('2.13'), 'al_pis': D('0.46'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_15: {'al_simples': D('15.52'), 'al_irpj': D('5.43'), 'al_csll': D('2.25'), 'al_cofins': D('2.33'), 'al_pis': D('0.51'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_16: {'al_simples': D('16.32'), 'al_irpj': D('5.85'), 'al_csll': D('2.42'), 'al_cofins': D('2.51'), 'al_pis': D('0.54'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_17: {'al_simples': D('16.82'), 'al_irpj': D('6.10'), 'al_csll': D('2.52'), 'al_cofins': D('2.62'), 'al_pis': D('0.57'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_18: {'al_simples': D('17.22'), 'al_irpj': D('6.30'), 'al_csll': D('2.61'), 'al_cofins': D('2.71'), 'al_pis': D('0.59'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_19: {'al_simples': D('17.44'), 'al_irpj': D('6.42'), 'al_csll': D('2.66'), 'al_cofins': D('2.76'), 'al_pis': D('0.60'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_20: {'al_simples': D('17.85'), 'al_irpj': D('6.64'), 'al_csll': D('2.74'), 'al_cofins': D('2.85'), 'al_pis': D('0.62'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
}

SIMPLES_NACIONAL_ANEXO_05_ATE_40 = {
    SIMPLES_NACIONAL_TETO_01: {'al_simples': D('8.80'), 'al_irpj': D('3.51'), 'al_csll': D('1.45'), 'al_cofins': D('1.51'), 'al_pis': D('0.33'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_02: {'al_simples': D('9.10'), 'al_irpj': D('3.26'), 'al_csll': D('1.35'), 'al_cofins': D('1.40'), 'al_pis': D('0.30'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_03: {'al_simples': D('9.58'), 'al_irpj': D('3.14'), 'al_csll': D('1.30'), 'al_cofins': D('1.35'), 'al_pis': D('0.29'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_04: {'al_simples': D('10.56'), 'al_irpj': D('3.47'), 'al_csll': D('1.43'), 'al_cofins': D('1.49'), 'al_pis': D('0.32'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_05: {'al_simples': D('11.04'), 'al_irpj': D('3.70'), 'al_csll': D('1.53'), 'al_cofins': D('1.59'), 'al_pis': D('0.34'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_06: {'al_simples': D('11.60'), 'al_irpj': D('3.81'), 'al_csll': D('1.57'), 'al_cofins': D('1.64'), 'al_pis': D('0.35'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_07: {'al_simples': D('11.68'), 'al_irpj': D('3.84'), 'al_csll': D('1.58'), 'al_cofins': D('1.65'), 'al_pis': D('0.36'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_08: {'al_simples': D('11.69'), 'al_irpj': D('3.81'), 'al_csll': D('1.58'), 'al_cofins': D('1.64'), 'al_pis': D('0.35'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_09: {'al_simples': D('12.08'), 'al_irpj': D('3.85'), 'al_csll': D('1.59'), 'al_cofins': D('1.66'), 'al_pis': D('0.36'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_10: {'al_simples': D('12.09'), 'al_irpj': D('3.85'), 'al_csll': D('1.59'), 'al_cofins': D('1.65'), 'al_pis': D('0.36'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_11: {'al_simples': D('12.78'), 'al_irpj': D('4.02'), 'al_csll': D('1.66'), 'al_cofins': D('1.73'), 'al_pis': D('0.37'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_12: {'al_simples': D('13.15'), 'al_irpj': D('4.21'), 'al_csll': D('1.74'), 'al_cofins': D('1.81'), 'al_pis': D('0.39'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_13: {'al_simples': D('13.51'), 'al_irpj': D('4.40'), 'al_csll': D('1.82'), 'al_cofins': D('1.89'), 'al_pis': D('0.41'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_14: {'al_simples': D('14.04'), 'al_irpj': D('4.68'), 'al_csll': D('1.93'), 'al_cofins': D('2.01'), 'al_pis': D('0.43'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_15: {'al_simples': D('15.03'), 'al_irpj': D('5.18'), 'al_csll': D('2.14'), 'al_cofins': D('2.23'), 'al_pis': D('0.48'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_16: {'al_simples': D('15.93'), 'al_irpj': D('5.64'), 'al_csll': D('2.33'), 'al_cofins': D('2.43'), 'al_pis': D('0.53'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_17: {'al_simples': D('16.38'), 'al_irpj': D('5.88'), 'al_csll': D('2.43'), 'al_cofins': D('2.53'), 'al_pis': D('0.55'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_18: {'al_simples': D('16.82'), 'al_irpj': D('6.09'), 'al_csll': D('2.52'), 'al_cofins': D('2.62'), 'al_pis': D('0.57'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_19: {'al_simples': D('17.21'), 'al_irpj': D('6.31'), 'al_csll': D('2.61'), 'al_cofins': D('2.71'), 'al_pis': D('0.59'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_20: {'al_simples': D('17.60'), 'al_irpj': D('6.51'), 'al_csll': D('2.69'), 'al_cofins': D('2.80'), 'al_pis': D('0.61'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
}

SIMPLES_NACIONAL_ANEXO_05_MAIS_40 = {
    SIMPLES_NACIONAL_TETO_01: {'al_simples': D('8.00'), 'al_irpj': D('3.10'), 'al_csll': D('1.28'), 'al_cofins': D('1.33'), 'al_pis': D('0.29'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_02: {'al_simples': D('8.48'), 'al_irpj': D('2.94'), 'al_csll': D('1.21'), 'al_cofins': D('1.26'), 'al_pis': D('0.27'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_03: {'al_simples': D('9.03'), 'al_irpj': D('2.86'), 'al_csll': D('1.18'), 'al_cofins': D('1.23'), 'al_pis': D('0.27'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_04: {'al_simples': D('9.34'), 'al_irpj': D('2.84'), 'al_csll': D('1.17'), 'al_cofins': D('1.22'), 'al_pis': D('0.26'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_05: {'al_simples': D('10.06'), 'al_irpj': D('3.20'), 'al_csll': D('1.32'), 'al_cofins': D('1.37'), 'al_pis': D('0.30'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_06: {'al_simples': D('10.60'), 'al_irpj': D('3.29'), 'al_csll': D('1.36'), 'al_cofins': D('1.41'), 'al_pis': D('0.31'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_07: {'al_simples': D('10.68'), 'al_irpj': D('3.33'), 'al_csll': D('1.37'), 'al_cofins': D('1.42'), 'al_pis': D('0.31'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_08: {'al_simples': D('10.69'), 'al_irpj': D('3.29'), 'al_csll': D('1.36'), 'al_cofins': D('1.42'), 'al_pis': D('0.31'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_09: {'al_simples': D('11.08'), 'al_irpj': D('3.33'), 'al_csll': D('1.38'), 'al_cofins': D('1.44'), 'al_pis': D('0.31'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_10: {'al_simples': D('11.09'), 'al_irpj': D('3.34'), 'al_csll': D('1.37'), 'al_cofins': D('1.43'), 'al_pis': D('0.31'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_11: {'al_simples': D('11.87'), 'al_irpj': D('3.55'), 'al_csll': D('1.47'), 'al_cofins': D('1.52'), 'al_pis': D('0.33'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_12: {'al_simples': D('12.28'), 'al_irpj': D('3.76'), 'al_csll': D('1.55'), 'al_cofins': D('1.62'), 'al_pis': D('0.35'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_13: {'al_simples': D('12.68'), 'al_irpj': D('3.97'), 'al_csll': D('1.64'), 'al_cofins': D('1.70'), 'al_pis': D('0.37'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_14: {'al_simples': D('13.26'), 'al_irpj': D('4.28'), 'al_csll': D('1.76'), 'al_cofins': D('1.83'), 'al_pis': D('0.40'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_15: {'al_simples': D('14.29'), 'al_irpj': D('4.80'), 'al_csll': D('1.98'), 'al_cofins': D('2.06'), 'al_pis': D('0.45'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_16: {'al_simples': D('15.23'), 'al_irpj': D('5.28'), 'al_csll': D('2.18'), 'al_cofins': D('2.27'), 'al_pis': D('0.49'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_17: {'al_simples': D('16.17'), 'al_irpj': D('5.77'), 'al_csll': D('2.38'), 'al_cofins': D('2.48'), 'al_pis': D('0.54'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_18: {'al_simples': D('16.51'), 'al_irpj': D('5.93'), 'al_csll': D('2.46'), 'al_cofins': D('2.55'), 'al_pis': D('0.55'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_19: {'al_simples': D('16.94'), 'al_irpj': D('6.17'), 'al_csll': D('2.55'), 'al_cofins': D('2.65'), 'al_pis': D('0.57'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
    SIMPLES_NACIONAL_TETO_20: {'al_simples': D('17.18'), 'al_irpj': D('6.29'), 'al_csll': D('2.60'), 'al_cofins': D('2.70'), 'al_pis': D('0.59'), 'al_cpp': D('0.00'), 'al_icms': D('0.00'), 'al_iss': D('0.00')},
}

SIMPLES_NACIONAL_TABELAS = {
    '1': SIMPLES_NACIONAL_ANEXO_01,
    '2': SIMPLES_NACIONAL_ANEXO_02,
    '3': SIMPLES_NACIONAL_ANEXO_03,
    '4': SIMPLES_NACIONAL_ANEXO_04,
    '6': SIMPLES_NACIONAL_ANEXO_06,
    '5_ate_10': SIMPLES_NACIONAL_ANEXO_05_ATE_10,
    '5_ate_15': SIMPLES_NACIONAL_ANEXO_05_ATE_15,
    '5_ate_20': SIMPLES_NACIONAL_ANEXO_05_ATE_20,
    '5_ate_25': SIMPLES_NACIONAL_ANEXO_05_ATE_25,
    '5_ate_30': SIMPLES_NACIONAL_ANEXO_05_ATE_30,
    '5_ate_35': SIMPLES_NACIONAL_ANEXO_05_ATE_35,
    '5_ate_40': SIMPLES_NACIONAL_ANEXO_05_ATE_40,
    '5_mais_40': SIMPLES_NACIONAL_ANEXO_05_MAIS_40,
}


POSICAO_CFOP = (
    ('E', 'Estadual'),
    ('I', 'Interestadual'),
    ('X', 'Estrangeiro'),
)
POSICAO_CFOP_DICT = dict(POSICAO_CFOP)

POSICAO_CFOP_ESTADUAL = 'E'
POSICAO_CFOP_INTERESTADUAL = 'I'
POSICAO_CFOP_ESTRANGEIRO = 'X'


TIPO_CERTIFICADO = (
    ('A1', 'A1 - arquivo'),
    ('A3', 'A3 - token ou cartão'),
)
TIPO_CERTIFICADO_A1 = 'A1'
TIPO_CERTIFICADO_A3 = 'A3'

TIPO_PESSOA = (
    ('F', 'Física'),
    ('J', 'Jurídica'),
    ('E', 'Estrangeiro'),
    ('I', 'Indeterminado'),
)

TIPO_PESSOA_FISICA = 'F'
TIPO_PESSOA_JURIDICA = 'J'
TIPO_PESSOA_ESTRANGEIRO = 'E'
TIPO_PESSOA_INDETERMINADO = 'I'
