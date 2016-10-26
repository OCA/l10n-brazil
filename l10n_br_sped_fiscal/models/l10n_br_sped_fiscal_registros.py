# -*- encoding: utf-8 -*-
##############################################################################
#
#    Daniel Sadamo
#    Fernando Marcato
#    Copyright (C) 2016 - KMEE INFORMATICA LTDA <Http://kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

import openerp.addons.decimal_precision as dp
from openerp import models, fields, api, exceptions, _


_IND_MOV = [('0', u'Bloco com dados informados'),
            ('1', u'Bloco sem dados informados')]

_S_N = [('S', u'Sim'),
        ('N', u'Não')]

_COD_DISP = [
    ('00', u'Formulário de Segurança (FS) ­ impressor autônomo'),
    ('01', u'FS­DA ­ Formulário de Segurança para Impressão de Danfe'),
    ('02', u'Formulário de segurança ­ NF­e'),
    ('03', u'Formulário Contínuo'),
    ('04', u'Blocos'),
    ('05', u'Jogos Soltos'),
]

_IND_OPER = [('0', u'Entrada'),
            ('1', u'Saída')]

_IND_EMIT = [('0', u'Emissão própria'),
            ('1', u'Terceiros')]

_IND_PGTO = [('0', u'À vista'),
             ('1', u'A prazo'),
             ('2', u'Outros')]

_IND_FRT = [('0', u'Por conta do emitente'),
             ('1', u'Por conta do destinatário'),
             ('2', u'Por conta de terceiros'),
             ('9', u'Sem cobrança de frete')]

_IND_MOV_C170 = [('0', u'Sim'),
            ('1', u'Não')]

_IND_APUR = [('0', u'Mensal'),
            ('1', u'Decendial')]

_COD_CONS = [
    ('01', u'Comercial'),
    ('02', u'Consumo própria'),
    ('03', u'Iluminação pública'),
    ('04', u'Industrial'),
    ('05', u'Pode Público'),
    ('06', u'Residencial'),
    ('07', u'Rural'),
    ('08', u'Serviço Público'),
]

_TP_LIGACAO = [('1', u'Monofásico'),
               ('2', u'Bifásico'),
               ('3', u'Trifásico')]

_COD_GRUPO_TENSAO = [
    ('01', u'A1 ­ Alta Tensão (230kV ou mais)'),
    ('02', u'A2 ­ Alta Tensão (88 a 138kV)'),
    ('03', u'A3 ­ Alta Tensão (69kV)'),
    ('04', u'A3a ­ Alta Tensão (30kV a 44kV)'),
    ('05', u'A4 ­ Alta Tensão (2,3kV a 25kV)'),
    ('06', u'AS ­ Alta Tensão Subterrâneo 06'),
    ('07', u'B1 ­ Residencial 07'),
    ('08', u'B1 ­ Residencial Baixa Renda 08'),
    ('09', u'B2 ­ Rural 09'),
    ('10', u'B2 ­ Cooperativa de Eletrificação Rural'),
    ('11', u'B2 ­ Serviço Público de Irrigação'),
    ('12', u'B3 ­ Demais Classes'),
    ('13', u'B4a ­ Iluminação Pública ­ rede de distribuição'),
    ('14', u'B4b ­ Iluminação Pública ­ bulbo de lâmpad'),]

_IND_OPER_D100 = [('0', u'Aquisição'),
            ('1', u'Prestação')]

_TP_ASSINANTE = [('1', u'Comercial/Industrial'),
                 ('2', u'Poder Público'),
                 ('3', u'Residencial/Pessoa Física'),
                 ('4', u'Público'),
                 ('5', u'Semi-Público'),
                 ('6', u'Outros'),]


class L10nBrSpedFiscalBlocoZeroRegistroTemplate(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro.template'
    _description = u"TEMPLATE DE REGISTRO"

    bloco_id = fields.Many2one('l10n_br.sped.fiscal.bloco.zero', string='Bloco')
    REG = fields.Char(string='REG', readonly=True)


_COD_FIN = [('0', 'Remessa do arquivo original'),
            ('1', 'Remessa do arquivo subistituto')]

_IND_PERFIL = [('A', 'Perfil A'),
               ('B', 'Perfil B'),
               ('C', 'Perfil C')]

_IND_ATIV = [('0', 'Industrial ou equiparado a industrial'),
             ('1', 'Outros')]


class L10nBrSpedFiscalBlocoZeroRegistro0000(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro0000'
    _description = u"Abertura  do  Arquivo  Digital  e " \
                   u"Identificação da Entidade"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.zero', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='0000')
    COD_VER = fields.Char(string=u'Versão do Leiaute', readonly=True)
    COD_FIN = fields.Selection(
        selection=_COD_FIN, string=u'Código da Finalidade', readonly=True)
    DT_INI = fields.Date(string=u'Data Inicial', readonly=True)
    DT_FIN = fields.Date(string=u'Data Final', readonly=True)
    NOME = fields.Char(string='nome', readonly=True)
    CNPJ = fields.Char(string='CNPJ', readonly=True)
    CPF = fields.Char(string='CPF', readonly=True)
    UF = fields.Char(string='Sigla da UF', readonly=True)
    IE = fields.Char(string='Inscr. Estadual', readonly=True)
    COD_MUN = fields.Char(string=u'Cód. Município IBGE', readonly=True)
    IM = fields.Char(string='Inscr. Municipal', readonly=True)
    SUFRAMA = fields.Char(string='SUFRAMA', readonly=True)
    IND_PERFIL = fields.Selection(string=u'Perfil de Apresentação',
                                  selection=_IND_PERFIL, readonly=True)
    IND_ATIV = fields.Selection(string='Tipo de atividade',
                                selection=_IND_ATIV, readonly=True)


class L10nBrSpedFiscalBlocoZeroRegistro0001(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro0001'
    _description = u"Abertura  do  Bloco  0"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.zero', string='Bloco')
    REG = fields.Char(string='REG', readonly=True, default='0001')
    IND_ATIV = fields.Selection(string='Tipo de atividade',
                                selection=_IND_MOV, readonly=True)


class L10nBrSpedFiscalBlocoZeroRegistro0005(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro0005'
    _description = u"Dados  Complementares  da Entidade"

    bloco_id = fields.Many2one('l10n_br.sped.fiscal.bloco.zero', string='Bloco')
    REG = fields.Char(string='REG', readonly=True, default='0005')
    FANTASIA = fields.Char(string='Nome Fantasia')
    CEP = fields.Char(string='CEP')
    END = fields.Char(string=u'Logradouro e endereço')
    NUM = fields.Char(string=u'Número')
    COMPL = fields.Char(string='Complemento')
    BAIRRO = fields.Char(string='Bairro')
    FONE = fields.Char(string='Telefone(DDD+FONE)',)
    FAX = fields.Char(string='Fax', readonly=True,)
    EMAIL = fields.Char(string='Email', )


class L10nBrSpedFiscalBlocoZeroRegistro0150(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro0150'
    _description = u"Tabela  de  cadastro  do participante"

    bloco_id = fields.Many2one('l10n_br.sped.fiscal.bloco.zero', string='Bloco')
    REG = fields.Char(string='REG', readonly=True, default='0150')
    COD_PART = fields.Char(string=u'Código de identificação')
    NOME = fields.Char(string='Nome pessoal ou empresarial')
    COD_PAIS = fields.Char(string=u'Código do país')
    CNPJ = fields.Char(string=u'CNPJ')
    CPF = fields.Char(string=u'CPF')
    IE = fields.Char(string=u'Inscrição Estadual (IE)')
    COD_MUN = fields.Char(string=u'Código do município')
    SUFRAMA = fields.Char(string='SUFRAMA',)
    END = fields.Char(string=u'Logradouro e endereço', readonly=True,)
    NUM = fields.Char(string=u'Número', )
    COMPL = fields.Char(string='Complemento', )
    BAIRRO = fields.Char(string='Bairro', )


class L10nBrSpedFiscalBlocoZeroRegistro0175(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro0175'
    _description = u"Alteração  da  Tabela  de Cadastro de Participante"

    bloco_id = fields.Many2one('l10n_br.sped.fiscal.bloco.zero', string='Bloco')
    REG = fields.Char(string='REG', readonly=True, default='0175')
    DT_ALT = fields.Date(string=u'Data de alteração')
    NR_CAMPO = fields.Char(string=u'Número do campo alterado'
                                  u'(Somente campos 03 a 13, exceto 07).')
    CONT_ANT = fields.Char(string=u'Conteúdo anterior do campo')


class L10nBrSpedFiscalBlocoZeroRegistro0190(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro0190'
    _description = u"Identificação das Unidades de Medida"

    bloco_id = fields.Many2one('l10n_br.sped.fiscal.bloco.zero', string='Bloco')
    REG = fields.Char(string='REG', readonly=True, default='0190')
    UNID = fields.Char(string=u'Código da UM')
    DESCR = fields.Char(string=u'Descrição da UM')


class L10nBrSpedFiscalBlocoZeroRegistro0200(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro0200'
    _description = u"Informar mercadorias serviços e produtos"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.zero', string=u'Bloco')
    REG = fields.Char(string=u'REG', readonly=True, default='0200')
    COD_ITEM = fields.Char(string=u'Código do item')
    DESCR_ITEM = fields.Char(string=u'Descrição do item')
    COD_BARRA = fields.Char(
        string=u'Representação alfanumérico do código de barra do produto')
    COD_ANT_ITEM = fields.Char(
        string=u'Código anterior do item com relação à última informação '
               u'apresentada')
    UNID_INV = fields.Char(
        string=u'Unidade de medida utilizada na quantificação de estoques')


class L10nBrSpedFiscalBlocoZeroRegistro0205(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro0205'
    _description = u"Alteração do item"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.zero', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='0205')
    DESCR_ANT_ITEM = fields.Char(string=u'Descrição anterior do item')
    DT_INI = fields.Char(
        string=u'Data inicial de utilização da descrição do item')
    DT_FIM = fields.Char(
        string=u'Data final de utilização da descrição do item')
    COD_ANT_ITEM = fields.Char(
        string=u'Código anterior do item com relação à última'
               u'informação apresentada')


class L10nBrSpedFiscalBlocoZeroRegistro0400(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro0400'
    _description = u"Tabela de Natureza da Operação/Prestação"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.zero', string='Bloco')
    REG = fields.Char(string=u'REG', readonly=True, default='0400')
    COD_NAT = fields.Char(string=u'Código da natureza da operação/prestação')
    DESCR_NAT = fields.Char(
        string=u'Descrição da natureza da operação/prestação')


class L10nBrSpedFiscalBlocoZeroRegistro0450(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro0450'
    _description = u"Tabela de Informação Complementar do Documento Fiscal"

    bloco_id = fields.Many2one('l10n_br.sped.fiscal.bloco.zero', string='Bloco')
    REG = fields.Char(string=u'REG', readonly=True, default='0450')
    COD_INF = fields.Char(
        string=u'Código da informação complementar do documento fiscal')
    TXT = fields.Char(string=u'Informação complementar de documento fiscal')


class L10nBrSpedFiscalBlocoZeroRegistro0990(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro0990'
    _description = u"Encerramento do Bloco 0"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.zero', string=u'Bloco')
    REG = fields.Char(string=u'REG', readonly=True, default='0990')
    QTD_LIN_0 = fields.Char(string=u'Quantidade total de linhas do Bloco 0.')


class L10nBrSpedFiscalBlocoUmRegistro1001(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.um.registro1001'
    _description = u"Abertura do Bloco 1"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.um', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='1001')
    IND_MOV = fields.Selection(
        selection=_IND_MOV, string=u'Indicador de movimento')


class L10nBrSpedFiscalBlocoUmRegistro1010(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.um.registro1010'
    _description = u"Obrigatoriedade Registros Bloco 1"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.um', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='1010')
    IND_EXP = fields.Selection(selection=_S_N, string=u'Ocorreu  averbação de exportação no período')
    IND_CCRF = fields.Selection(selection=_S_N, string=u'Existe info a cerca de crédito de ICMS')
    IND_COMB = fields.Selection(selection=_S_N, string=u'É comércio varejista de combustíveis')
    IND_USINA = fields.Selection(selection=_S_N, string=u'Usina de açúcar/álcool')
    IND_VA = fields.Selection(selection=_S_N, string=u'Existe info a ser prestada nesse registro')
    IND_EE = fields.Selection(selection=_S_N, string=u'É distribuidora de energia')
    IND_CART = fields.Selection(selection=_S_N, string=u'Realizou vendas com cartão de crédito/débito')
    IND_FORM = fields.Selection(selection=_S_N, string=u'Emitiu documento fiscal em papel em UF que exige controle')
    IND_AER = fields.Selection(selection=_S_N, string=u'Prestou serviço de transporte aéreo')


class L10nBrSpedFiscalBlocoUmRegistro1700(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.um.registro1700'
    _description = u"Documentos fiscais utilizados no período a que se refere o arquivo Sped­Fiscal"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.um', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='1700')
    COD_DISP = fields.Selection(
        selection=_COD_DISP, string=u'Código dispositivo autorizado')
    COD_MOD = fields.Char(string=u'Código do modelo do dispositivo')
    SER = fields.Char(string=u'Série do dispositivo')
    SUB = fields.Char(string=u'Subsérie do dispositivo')
    NUM_DOC_INI = fields.Char(string=u'Número do dispositivo inicial')
    NUM_DOC_FIN = fields.Char(string=u'Número do dispositivo final')
    NUM_AUT = fields.Char(string=u'Número da autorização')


class L10nBrSpedFiscalBlocoUmRegistro1990(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.um.registro1990'
    _description = u"Encerramento  do  Bloco  1"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.um', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='1990')
    QTD_LIN_1 = fields.Char(string=u'Quantidade total de linhas do Bloco 1')


# Bloco 9
class L10nBrSpedFiscalBlocoNoveRegistro9001(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.nove.registro9001'
    _description = u"Abertura do Bloco 9"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.nove', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='9001')
    IND_MOV = fields.Selection(
        selection=_IND_MOV, string=u'Indicador de movimento')


class L10nBrSpedFiscalBlocoNoveRegistro9900(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.nove.registro9900'
    _description = u"Registros  do  arquivo"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.nove', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='9900')
    REG_BLC = fields.Char(string=u'Registro Totalizado no Próximo Campo')
    QTD_REG_BLC = fields.Char(string=u'Total de registros do tipo informado no campo anterior')


class L10nBrSpedFiscalBlocoNoveRegistro9990(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.nove.registro9990'
    _description = u""

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.nove', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='9990')
    QTD_LIN_9 = fields.Char(string=u'Quantidade total de linhas do Bloco 9')


class L10nBrSpedFiscalBlocoNoveRegistro9999(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.nove.registro9999'
    _description = u""

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.nove', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='9999')
    QTD_LIN = fields.Char(string=u'Quantidade total de linhas do arquivo digital')


class L10nBrSpedFiscalBlocoCRegistroC001(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.c.registroc001'
    _description = u"Abertura do Bloco C"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.c', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='C001')
    IND_MOV = fields.Selection(
        selection=_IND_MOV, string=u'Indicador de movimento')


class L10nBrSpedFiscalBlocoCRegistroC100(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.c.registroc100'
    _description = u""

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.c', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='C100')
    IND_OPER = fields.Selection(
        selection=_IND_OPER, string=u'Indicador de operação')
    IND_EMIT = fields.Selection(
        selection=_IND_EMIT, string=u'Indicador do emitente do documento fiscal')
    COD_PART = fields.Char(string=u'Cód do participante')
    COD_MOD = fields.Char(string=u'Cód do modelo do documento fiscal')
    COD_SIT = fields.Char(string=u'Cód da situação do documento fiscal')
    SER = fields.Char(string=u'Série documento fiscal')
    NUM_DOC = fields.Char(string=u'Número documento fiscal')
    CHV_NFE = fields.Char(string=u'Chave da NF-e')
    DT_DOC = fields.Char(string=u'Data emissão documento fiscal')
    DT_E_S = fields.Char(string=u'Data de entrada ou saída')
    VL_DOC = fields.Char(string=u'Valor total documento fiscal')
    IND_PGTO = fields.Selection(
        selection=_IND_PGTO, string=u'Indicador do tipo de pagamento')
    VL_DESC = fields.Char(string=u'Valor total do desconto')
    VL_ABAT_NT = fields.Char(string=u'Abatimento não tributado e não comercial')
    VL_MERC = fields.Char(string=u'Valor total mercadorias e serviços')
    IND_FRT = fields.Selection(
        selection=_IND_FRT, string=u'Indicador do tipo de frete')
    VL_FRT = fields.Char(string=u'Valor do frete')
    VL_SEG = fields.Char(string=u'Valor do seguro')
    VL_OUT_DA = fields.Char(string=u'Valor de outras despesas acessórias')
    VL_BC_ICMS = fields.Char(string=u'Base de cálculo do ICMS')
    VL_ICMS = fields.Char(string=u'Valor do ICMS')
    VL_BC_ICMS_ST = fields.Char(string=u'Base de cálculo do ICMS ST')
    VL_ICMS_ST = fields.Char(string=u'Valor do ICMS retido por ST')
    VL_IPI = fields.Char(string=u'Valor do IPI')
    VL_PIS = fields.Char(string=u'Valor do PIS')
    VL_COFINS = fields.Char(string=u'Valor do COFINS')
    VL_PIS_ST = fields.Char(string=u'Valor do PIS retido por ST')
    VL_COFINS_ST = fields.Char(string=u'Valor do COFINS retido por ST')


class L10nBrSpedFiscalBlocoCRegistroC110(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.c.registroc110'
    _description = u"Informação complementar da Nota Fiscal"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.c', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='C110')
    COD_INF = fields.Char(string=u'Código da informação complementar do documento fiscal')
    TXT_COMPL = fields.Char(string=u'Descrição complementar do código de referência')


class L10nBrSpedFiscalBlocoCRegistroC113(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.c.registroc113'
    _description = u"Documento fiscal referenciado"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.c', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='C113')
    IND_OPER = fields.Selection(selection=_IND_OPER, string=u'Indicador de operação')
    IND_EMIT = fields.Selection(selection=_IND_EMIT, string=u'Indicador do emitente do título')
    COD_PART = fields.Char(string=u'Código do participante emitente')
    COD_MOD = fields.Char(string=u'Código do documento fiscal')
    SER = fields.Char(string=u'Série do documento fiscal')
    SUB = fields.Char(string=u'Subsérie do documento fiscal')
    NUM_DOC = fields.Char(string=u'Número do documento fiscal')
    DT_DOC = fields.Char(string=u'Data de emissão do documento fiscal')


class L10nBrSpedFiscalBlocoCRegistroC170(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.c.registroc170'
    _description = u"Itens do Documento"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.c', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='C170')
    NUM_ITEM = fields.Char(string=u'Número sequencial do item no documento fiscal')
    COD_ITEM = fields.Char(string=u'Código do item')
    DESCR_COMPL = fields.Char(string=u'Descrição complementar do item como adotado no documento fiscal')
    QTD = fields.Char(string=u'Quantidade do item')
    UNID = fields.Char(string=u'Unidade do item')
    VL_ITEM = fields.Char(string=u'Valor total do item')
    VL_DESC = fields.Char(string=u'Valor do desconto comercial')
    IND_MOV = fields.Selection(selection=_IND_MOV_C170, string=u'Movimentação física do ITEM/PRODUTO')
    CST_ICMS = fields.Char(string=u'Código da Situação Tributária (CST) referente ao ICMS')
    CFOP = fields.Char(string=u'Código Fiscal de Operação e Prestação')
    COD_NAT = fields.Char(string=u'Código da natureza da operação')
    VL_BC_ICMS = fields.Char(string=u'Valor da Base de Cálculo (BC) do ICMS')
    ALIQ_ICMS = fields.Char(string=u'Alíquota do ICMS')
    VL_ICMS = fields.Char(string=u'Valor do ICMS creditado/debitado')
    VL_BC_ICMS_ST = fields.Char(string=u'Valor da BC referente à substituição tributária')
    ALIQ_ST = fields.Char(string=u'Alíquota do ICMS da substituição tributária na Unidade da Federação (UF) de destino')
    VL_ICMS_ST = fields.Char(string=u'Valor do ICMS referente à substituição tributária')
    IND_APUR = fields.Selection(selection=_IND_APUR, string=u'Indicador de período de apuração do IPI')
    CST_IPI = fields.Char(string=u'CST referente ao IPI')
    COD_ENQ = fields.Char(string=u'Código de enquadramento legal do IPI')
    VL_BC_IPI = fields.Char(string=u'Valor da BC do IPI')
    ALIQ_IPI = fields.Char(string=u'Alíquota do IPI')
    VL_IPI = fields.Char(string=u'Valor do IPI creditado/debitado')
    CST_PIS = fields.Char(string=u'CST referente ao PIS')
    VL_BC_PIS = fields.Char(string=u'Valor da BC do PIS')
    ALIQ_PIS = fields.Char(string=u'Alíquota do PIS (em percentual)')
    QUANT_BC_PIS = fields.Char(string=u'Quantidade ­ BC PIS')
    ALIQ_PIS = fields.Char(string=u'Alíquota do PIS (em Reais)')
    VL_PIS = fields.Char(string=u'Valor do PIS')
    CST_COFINS = fields.Char(string=u'CST referente ao COFINS')
    VL_BC_COFINS = fields.Char(string=u'Valor da BC da COFINS')
    ALIQ_COFINS = fields.Char(string=u'Alíquota do COFINS (em percentual)')
    QUANT_BC_COFINS = fields.Char(string=u'Quantidade ­ BC COFINS')
    ALIQ_COFINS = fields.Char(string=u'Alíquota da COFINS (em Reais)')
    VL_COFINS = fields.Char(string=u'Valor da COFINS')
    COD_CTA = fields.Char(string=u'Código da conta analítica contábil debitada/creditada')


class L10nBrSpedFiscalBlocoCRegistroC190(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.c.registroc190'
    _description = u"Escrituração dos documentos fiscais totalizados por Código da Situação Tributária"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.c', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='C190')
    CST_ICMS = fields.Char(string=u'CST')
    CFOP = fields.Char(string=u'CFOP do agrupamento de itens')
    ALIQ_ICMS = fields.Char(string=u'Alíquota do ICMS')
    VL_OPR = fields.Char(string=u'Valor da operação na combinação de CST_ICMS, CFOP e alíquota do ICMS')
    VL_BC_ICMS = fields.Char(string=u'Parcela correspondente ao |Valor da Base de Cálculo (BC) do ICMS|')
    VL_ICMS = fields.Char(string=u'Parcela correspondente ao |Valor do ICMS|')
    VL_BC_ICMS_ST = fields.Char(string=u'Parcela correspondente ao |Valor da BC do ICMS| da ST')
    VL_ICMS_ST = fields.Char(string=u'Parcela correspondente ao valor creditado/debitado do ICMS')
    VL_RED_BC = fields.Char(string=u'Valor não tributado em função da redução da BC do ICMS')
    VL_IPI = fields.Char(string=u'Parcela correspondente ao |Valor do IPI|')
    COD_OBS = fields.Char(string=u'Código da observação do lançamento fiscal')


class L10nBrSpedFiscalBlocoCRegistroC500(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.c.registroc500'
    _description = u""

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.c', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='C500')
    IND_OPER = fields.Selection(selection=_IND_OPER, string=u'Indicador do tipo de operação')
    IND_EMIT = fields.Selection(selection=_IND_EMIT, string=u'Indicador do emitente do documento fiscal')
    COD_PART = fields.Char(string=u'Código do participante')
    COD_MOD = fields.Char(string=u'Código do modelo do documento fiscal')
    COD_SIT = fields.Char(string=u'Código da situação do documento fiscal')
    SER = fields.Char(string=u'Série do documento fiscal')
    SUB = fields.Char(string=u'Subsérie do documento fiscal')
    COD_CONS = fields.Selection(selection=_COD_CONS, string=u'Código de classe de consumo de energia elétrica ou gás')
    NUM_DOC = fields.Char(string=u'Número documento fiscal')
    DT_DOC = fields.Char(string=u'Data emissão documento fiscal')
    DT_E_S = fields.Char(string=u'Data de entrada ou saída')
    VL_DOC = fields.Char(string=u'Valor total documento fiscal')
    VL_DESC = fields.Char(string=u'Valor total do desconto')
    VL_FORN = fields.Char(string=u'Valor total fornecido/consumido')
    VL_SERV_NT = fields.Char(string=u'Valor total dos serviços não tributados pelo ICMS')
    VL_TERC = fields.Char(string=u'Valor total cobrado em nome de terceiros')
    VL_DA = fields.Char(string=u'Valor total de despesas acessórias indicadas no documento fiscal')
    VL_BC_ICMS = fields.Char(string=u'Valor acumulado da Base de Cálculo (BC) do ICMS')
    VL_ICMS = fields.Char(string=u'Valor acumulado do ICMS')
    VL_BC_ICMS_ST = fields.Char(string=u'Valor acumulado da BC do ICMS substituição tributária (ICMS­ST)')
    VL_ICMS_ST = fields.Char(string=u'Valor acumulado do ICMS­ST')
    COD_INF = fields.Char(string=u'Código da informação complementar do documento fiscal')
    VL_PIS = fields.Char(string=u'Valor do PIS/Pasep')
    VL_COFINS = fields.Char(string=u'Valor do Cofins')
    TP_LIGACAO = fields.Selection(selection=_TP_LIGACAO, string=u'Código de tipo de Ligação')
    COD_GRUPO_TENSAO = fields.Selection(selection=_COD_GRUPO_TENSAO, string=u'Código de grupo de tensão')


class L10nBrSpedFiscalBlocoCRegistroC590(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.c.registroc590'
    _description = u"totalizar por CST, CFOP e Alíquota os itens dos documentos fiscais escriturados no Registro C510"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.c', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='C590')
    CST_ICMS = fields.Char(string=u'CST')
    CFOP = fields.Char(string=u'CFOP do agrupamento de itens')
    ALIQ_ICMS = fields.Char(string=u'Alíquota do ICMS')
    VL_OPR = fields.Char(string=u'Valor da operação correspondente à combinação de "CST_ICMS", "CFOP", e alíquota do ICMS')
    VL_BC_ICMS = fields.Char(string=u'Parcela correspondente ao |Valor da Base de Cálculo (BC) do ICMS|')
    VL_ICMS = fields.Char(string=u'Parcela correspondente ao |Valor do ICMS|')
    VL_BC_ICMS_ST = fields.Char(string=u'Parcela correspondente ao |Valor da BC do ICMS|')
    VL_ICMS_ST = fields.Char(string=u'Parcela correspondente ao valor creditado/debitado do ICMS da substituição tributária')
    VL_RED_BC = fields.Char(string=u'Valor não tributado em função da redução da BC do ICMS')
    COD_OBS = fields.Char(string=u'Código da observação do lançamento fiscal')


class L10nBrSpedFiscalBlocoCRegistroC990(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.c.registroc990'
    _description = u""

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.c', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='C990')
    QTD_LIN_C = fields.Char(string=u'Quantidade total de linhas do Bloco C')


class L10nBrSpedFiscalBlocoDRegistroD001(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.d.registrod001'
    _description = u""

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.d', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='D001')
    IND_MOV = fields.Selection(
        selection=_IND_MOV, string=u'Indicador de movimento')


class L10nBrSpedFiscalBlocoDRegistroD100(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.d.registrod100'
    _description = u""

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.d', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='D100')
    IND_OPER = fields.Selection(
        selection=_IND_OPER_D100, string=u'Indicador do tipo de operação')
    IND_EMIT = fields.Selection(
        selection=_IND_EMIT, string=u'Indicador do emitente do documento fiscal')
    COD_PART = fields.Char(string=u'Código do participante')
    COD_MOD = fields.Char(string=u'Código do modelo do documento fiscal')
    COD_SIT = fields.Char(string=u'Código da situação do documento fiscal')
    SER = fields.Char(string=u'Série do documento fiscal')
    SUB = fields.Char(string=u'Subsérie do documento fiscal')
    NUM_DOC = fields.Char(string=u'Número do documento fiscal')
    CHV_CTE = fields.Char(string=u'Chave do CT­e')
    DT_DOC = fields.Char(string=u'Data emissão documento fiscal')
    DT_A_P = fields.Char(string=u'Data da aquisição ou da prestação do serviço')
    TP_CT_e = fields.Char(string=u'Tipo de CT­e')
    CHV_CTE_REF = fields.Char(string=u'Chave do CT­e')
    VL_DOC = fields.Char(string=u'Valor total do documento fiscal')
    VL_DESC = fields.Char(string=u'Valor total do desconto')
    IND_FRT = fields.Selection(
        selection=_IND_FRT, string=u'Indicador do tipo de frete')
    VL_SERV = fields.Char(string=u'Valor total da prestação de serviço')
    VL_BC_ICMS = fields.Char(string=u'Valor da Base de Cálculo (BC) do ICMS')
    VL_ICMS = fields.Char(string=u'Valor do ICMS')
    VL_NT = fields.Char(string=u'Valor não­tributado')
    COD_INF = fields.Char(string=u'Código da informação complementar')
    COD_CTA = fields.Char(string=u'Código da conta analítica contábil debitada/creditada')


class L10nBrSpedFiscalBlocoDRegistroD190(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.d.registrod190'
    _description = u"Notas Fiscais de Serviço de Transporte"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.d', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='D190')
    CST_ICMS = fields.Char(string=u'Código da Situação Tributária')
    CFOP = fields.Char(string=u'Código Fiscal de Operação e Prestação')
    ALIQ_ICMS = fields.Char(string=u'Alíquota do ICMS')
    VL_OPR = fields.Char(string=u'Valor da operação correspondente à combinação de CST_ICMS, CFOP, e alíquota do ICMS')
    VL_BC_ICMS = fields.Char(string=u'Parcela correspondente ao Valor da Base de Cálculo (BC) do ICMS')
    VL_ICMS = fields.Char(string=u'Parcela correspondente ao Valor do ICMS')
    VL_RED_BC = fields.Char(string=u'Valor não tributado em função da redução da BC do ICMS')
    COD_OBS = fields.Char(string=u'Código da observação do lançamento fiscal')


class L10nBrSpedFiscalBlocoDRegistroD500(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.d.registrod500'
    _description = u"Nota Fiscal de Serviço de Comunicação"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.d', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='D500')
    IND_OPER = fields.Selection(selection=_IND_OPER_D100, string=u'Indicador do tipo de operação')
    IND_EMIT = fields.Selection(selection=_IND_EMIT, string=u'Indicador do emitente do documento fiscal')
    COD_PART = fields.Char(string=u'Código do participante')
    COD_MOD = fields.Char(string=u'Código do modelo do documento fiscal')
    COD_SIT = fields.Char(string=u'Código da situação do documento fiscal')
    SER = fields.Char(string=u'Série do documento fiscal')
    SUB = fields.Char(string=u'Subsérie do documento fiscal')
    NUM_DOC = fields.Char(string=u'Número do documento fiscal')
    DT_DOC = fields.Char(string=u'Data da emissão do documento fiscal.')
    DT_A_P = fields.Char(string=u'Data da entrada (aquisição) ou da saída (prestação do serviço)')
    VL_DOC = fields.Char(string=u'Valor total do documento fiscal')
    VL_DESC = fields.Char(string=u'Valor total do desconto.')
    VL_SERV = fields.Char(string=u'Valor da prestação de serviços.')
    VL_SERV_NT = fields.Char(string=u'Valor total dos serviços não­tributados pelo ICMS.')
    VL_TERC = fields.Char(string=u'Valores cobrados em nome de terceiros.')
    VL_DA = fields.Char(string=u'Valor de outras despesas')
    VL_BC_ICMS = fields.Char(string=u'Valor da Base de Cálculo (BC) do ICMS')
    VL_ICMS = fields.Char(string=u'Valor do ICMS.')
    COD_INF = fields.Char(string=u'Código da informação complementar')
    VL_PIS = fields.Char(string=u'Valor do PIS/Pasep.')
    VL_COFINS = fields.Char(string=u'Valor da Cofins.')
    COD_CTA = fields.Char(string=u'Código da conta analítica contábil')
    TP_ASSINANTE = fields.Selection(selection=_TP_ASSINANTE, string=u'Código do tipo do assinante')


class L10nBrSpedFiscalBlocoDRegistroD590(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.d.registrod590'
    _description = u"Registro Analítico do Documento"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.d', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='D590')
    CST_ICMS = fields.Char(string=u'CST')
    CFOP = fields.Char(string=u'CFOP')
    ALIQ_ICMS = fields.Char(string=u'Alíquota do ICMS')
    VL_OPR = fields.Char(string=u'Valor da operação comb CST_ICMS, CFOP, e alíquota do ICMS')
    VL_BC_ICMS = fields.Char(string=u'Valor da Base de Cálculo (BC) do ICMS')
    VL_ICMS = fields.Char(string=u'Valor do ICMS.')
    VL_BC_ICMS_UF = fields.Char(string=u'Parcela correspondente ao valor da BC do ICMS de outras UFs')
    VL_ICMS_UF = fields.Char(string=u'Parcela correspondente ao valor do ICMS de outras UFs')
    VL_RED_BC = fields.Char(string=u'Valor não tributado em função da redução da BC do ICMS')
    COD_OBS = fields.Char(string=u'Código da observação')


class L10nBrSpedFiscalBlocoDRegistroD990(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.d.registrod990'
    _description = u"Encerramento do bloco D"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.d', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='D990')
    QTD_LIN_D = fields.Char(string=u'Quantidade total de linhas do Bloco D')


class L10nBrSpedFiscalBlocoERegistroE001(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.e.registroe001'
    _description = u""

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.e', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='E001')
    IND_MOV = fields.Selection(selection=_IND_MOV, string=u'Indicador de movimento')


class L10nBrSpedFiscalBlocoERegistroE990(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.e.registroe990'
    _description = u"Encerramento do Bloco E"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.e', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='E990')
    QTD_LIN_E = fields.Char(string=u'Quantidade total de linhas do Bloco E')


class L10nBrSpedFiscalBlocoGRegistroG001(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.g.registrog001'
    _description = u"Abertura do Bloco G"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.g', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='G001')
    IND_MOV = fields.Selection(selection=_IND_MOV, string=u'Indicador de movimento')


class L10nBrSpedFiscalBlocoGRegistroG990(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.g.registrog990'
    _description = u"Encerramento do Bloco G"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.g', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='G990')
    QTD_LIN_G = fields.Char(string=u'Quantidade total de linhas do Bloco G')


class L10nBrSpedFiscalBlocoHRegistroH001(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.h.registroh001'
    _description = u"Abertura do bloco H"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.h', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='H001')
    IND_MOV = fields.Selection(selection=_IND_MOV, string=u'Indicador de movimento')


class L10nBrSpedFiscalBlocoHRegistroH990(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.h.registroh990'
    _description = u"Encerramento do bloco H"

    bloco_id = fields.Many2one(
        'l10n_br.sped.fiscal.bloco.h', string=u'Bloco')
    REG = fields.Char(string='REG', readonly=True, default='H990')
    QTD_LIN_H = fields.Char(string=u'Quantidade total de linhas do Bloco H')
