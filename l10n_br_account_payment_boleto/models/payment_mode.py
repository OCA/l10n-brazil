# -*- coding: utf-8 -*-
#    Copyright (C) 2012-TODAY KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo (mileo@kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from openerp.addons import decimal_precision as dp

from ..boleto.document import getBoletoSelection

selection = getBoletoSelection()


class PaymentMode(models.Model):
    _inherit = 'payment.mode'

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
    boleto_perc_mora = fields.Float(
        string=u"Percentual de Mora",
        digits=dp.get_precision('Account')
    )

    @api.constrains('boleto_type', 'boleto_carteira',
                    'boleto_modalidade', 'boleto_convenio',
                    'boleto_variacao', 'boleto_aceite')
    def boleto_restriction(self):
        if self.boleto_type == '6' and not self.boleto_carteira:
            raise ValidationError(u'Carteira no banco Itaú é obrigatória')

    @api.constrains('boleto_perc_mora')
    def _check_boleto_perc_mora(self):
        for record in self:
            if record.boleto_perc_mora > 2 or record.boleto_perc_mora < 0:
                raise ValidationError(
                    _('O percentual de Mora deve ser um valor entre 0 a 2.'))
