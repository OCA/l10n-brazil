# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models, _

from ..febraban.boleto.document import getBoletoSelection

boleto_selection = getBoletoSelection()


class PaymentMode(models.Model):

    _inherit = 'payment.mode'

    boleto_carteira = fields.Char('Carteira', size=3)
    boleto_modalidade = fields.Char('Modalidade', size=2)
    boleto_convenio = fields.Char('Codigo convênio', size=10)
    boleto_variacao = fields.Char('Variação', size=2)
    boleto_cnab_code = fields.Char('Código Cnab', size=20)
    boleto_aceite = fields.Selection(
        [('S', 'Sim'), ('N', 'Não')], string='Aceite', default='N')
    boleto_type = fields.Selection(
        boleto_selection, string="Boleto")
    boleto_especie = fields.Selection([
        ('01', 'DUPLICATA MERCANTIL'),
        ('02', 'NOTA PROMISSÓRIA'),
        ('03', 'NOTA DE SEGURO'),
        ('04', 'MENSALIDADE ESCOLAR'),
        ('05', 'RECIBO'),
        ('06', 'CONTRATO'),
        ('07', 'COSSEGUROS'),
        ('08', 'DUPLICATA DE SERVIÇO'),
        ('09', 'LETRA DE CÂMBIO'),
        ('13', 'NOTA DE DÉBITOS'),
        ('15', 'DOCUMENTO DE DÍVIDA'),
        ('16', 'ENCARGOS CONDOMINIAIS'),
        ('17', 'CONTA DE PRESTAÇÃO DE SERVIÇOS'),
        ('99', 'DIVERSOS'),
    ], string='Espécie do Título', default='01')
    boleto_protesto = fields.Selection([
        ('0', 'Sem instrução'),
        ('1', 'Protestar (Dias Corridos)'),
        ('2', 'Protestar (Dias Úteis)'),
        ('3', 'Não protestar'),
        ('7', 'Negativar (Dias Corridos)'),
        ('8', 'Não Negativar')
    ], string='Códigos de Protesto', default='0')
    boleto_protesto_prazo = fields.Char('Prazo protesto', size=2)
