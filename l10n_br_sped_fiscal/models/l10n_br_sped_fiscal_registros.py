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

class L10nBrSpedFiscalBlocoZeroRegistro000(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro000'
    _description = u"Abertura  do  Arquivo  Digital  e " \
                   u"Identificação da Entidade"

    bloco_id = fields.Many2one('l10n_br.sped.fiscal.bloco.zero', string='Bloco')
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

_IND_MOV = [('0', 'Bloco com dados informados'),
             ('1', 'Bloco sem dados informados')]

class L10nBrSpedFiscalBlocoZeroRegistro001(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro001'
    _description = u"Abertura  do  Bloco  0"

    bloco_id = fields.Many2one('l10n_br.sped.fiscal.bloco.zero', string='Bloco')
    REG = fields.Char(string='REG', readonly=True, default='0001')
    IND_ATIV = fields.Selection(string='Tipo de atividade',
                                selection=_IND_MOV, readonly=True)


class L10nBrSpedFiscalBlocoZeroRegistro005(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro005'
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


class L10nBrSpedFiscalBlocoZeroRegistro150(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro150'
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


class L10nBrSpedFiscalBlocoZeroRegistro175(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro175'
    _description = u"Alteração  da  Tabela  de Cadastro de Participante"

    bloco_id = fields.Many2one('l10n_br.sped.fiscal.bloco.zero', string='Bloco')
    REG = fields.Char(string='REG', readonly=True, default='0175')
    DT_ALT = fields.Date(string=u'Data de alteração')
    NR_CAMPO = fields.Char(string=u'Número do campo alterado'
                                  u'(Somente campos 03 a 13, exceto 07).')
    CONT_ANT = fields.Char(string=u'Conteúdo anterior do campo')

class L10nBrSpedFiscalBlocoZeroRegistro190(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero.registro190'
    _description = u"Identificação das Unidades de Medida"

    bloco_id = fields.Many2one('l10n_br.sped.fiscal.bloco.zero', string='Bloco')
    REG = fields.Char(string='REG', readonly=True, default='0190')
    UNID = fields.Char(string=u'Código da UM')
    DESCR = fields.Char(string=u'Descrição da UM')




