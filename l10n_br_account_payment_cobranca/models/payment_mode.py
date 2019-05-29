# -*- coding: utf-8 -*-
# #############################################################################
#
#
#    Copyright (C) 2012 KMEE (http://www.kmee.com.br)
#    @author Fernando Marcato Rodrigues
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields
from openerp.exceptions import ValidationError
from openerp.addons import decimal_precision as dp
from ..constantes import TIPO_SERVICO, FORMA_LANCAMENTO, \
    COMPLEMENTO_TIPO_SERVICO, CODIGO_FINALIDADE_TED, AVISO_FAVORECIDO

from ..boleto.document import getBoletoSelection

selection = getBoletoSelection()


class PaymentMode(models.Model):
    _inherit = "payment.mode"

    condicao_emissao_papeleta = fields.Selection(
        [('1', 'Banco emite e Processa'),
         ('2', 'Cliente emite e banco processa'), ],
        u'Condição Emissão de Papeleta', default='1')
    cnab_percent_interest = fields.Float(string=u"Percentual de Juros",
                                         digits=dp.get_precision('Account'))
    comunicacao_2 = fields.Char("Comunicação para o sacador avalista")
    tipo_servico = fields.Selection(
        selection=TIPO_SERVICO,
        string=u'Tipo de Serviço',
        help=u'Campo G025 do CNAB'
    )
    forma_lancamento = fields.Selection(
        selection=FORMA_LANCAMENTO,
        string=u'Forma Lançamento',
        help=u'Campo G029 do CNAB'
    )
    codigo_convenio = fields.Char(
        size=20,
        string=u'Código do Convênio no Banco',
        help=u'Campo G007 do CNAB',
        default=u'0001222130126',
    )
    codigo_finalidade_doc = fields.Selection(
        selection=COMPLEMENTO_TIPO_SERVICO,
        string=u'Complemento do Tipo de Serviço',
        help=u'Campo P005 do CNAB'
    )
    codigo_finalidade_ted = fields.Selection(
        selection=CODIGO_FINALIDADE_TED,
        string=u'Código Finalidade da TED',
        help=u'Campo P011 do CNAB'
    )
    codigo_finalidade_complementar = fields.Char(
        size=2,
        string=u'Código de finalidade complementar',
        help=u'Campo P013 do CNAB',
    )
    aviso_ao_favorecido = fields.Selection(
        selection=AVISO_FAVORECIDO,
        string=u'Aviso ao Favorecido',
        help=u'Campo P006 do CNAB',
        default=0,
    )
    # A exportação CNAB não se encaixa somente nos parâmetros de
    # débito e crédito.
    boleto_carteira = fields.Char('Carteira', size=3)
    boleto_modalidade = fields.Char('Modalidade', size=2)
    boleto_convenio = fields.Char(u'Codigo convênio', size=10)
    boleto_variacao = fields.Char(u'Variação', size=2)
    boleto_cnab_code = fields.Char(u'Código Cnab', size=20)
    boleto_aceite = fields.Selection(
        [('S', 'Sim'), ('N', 'Não')], string='Aceite', default='N')
    boleto_type = fields.Selection(
        selection, string="Boleto")
    boleto_especie = fields.Selection([
        ('01', u'DUPLICATA MERCANTIL'),
        ('02', u'NOTA PROMISSÓRIA'),
        ('03', u'NOTA DE SEGURO'),
        ('04', u'MENSALIDADE ESCOLAR'),
        ('05', u'RECIBO'),
        ('06', u'CONTRATO'),
        ('07', u'COSSEGUROS'),
        ('08', u'DUPLICATA DE SERVIÇO'),
        ('09', u'LETRA DE CÂMBIO'),
        ('13', u'NOTA DE DÉBITOS'),
        ('15', u'DOCUMENTO DE DÍVIDA'),
        ('16', u'ENCARGOS CONDOMINIAIS'),
        ('17', u'CONTA DE PRESTAÇÃO DE SERVIÇOS'),
        ('99', u'DIVERSOS'),
    ], string=u'Espécie do Título', default='01')
    boleto_protesto = fields.Selection([
        ('0', u'Sem instrução'),
        ('1', u'Protestar (Dias Corridos)'),
        ('2', u'Protestar (Dias Úteis)'),
        ('3', u'Não protestar'),
        ('7', u'Negativar (Dias Corridos)'),
        ('8', u'Não Negativar')
    ], string=u'Códigos de Protesto', default='0')
    boleto_protesto_prazo = fields.Char(u'Prazo protesto', size=2)

    @api.constrains('boleto_type', 'boleto_carteira',
                    'boleto_modalidade', 'boleto_convenio',
                    'boleto_variacao', 'boleto_aceite')
    def boleto_restriction(self):
        if self.boleto_type == '6' and not self.boleto_carteira:
            raise ValidationError(u'Carteira no banco Itaú é obrigatória')
