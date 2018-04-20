# -*- coding: utf-8 -*-
#    Copyright (C) 2012-TODAY KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo (mileo@kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError
from openerp.addons import decimal_precision as dp


class PaymentMode(models.Model):
    _inherit = 'payment.mode'

    boleto_carteira = fields.Char('Carteira', size=3)
    boleto_modalidade = fields.Char('Modalidade', size=2)
    boleto_convenio = fields.Char(u'Codigo convênio', size=10)
    boleto_variacao = fields.Char(u'Variação', size=2)
    boleto_cnab_code = fields.Char(u'Código Cnab', size=20)
    boleto_aceite = fields.Selection(
        [('S', 'Sim'), ('N', 'Não')], string='Aceite', default='N')
    boleto_type = fields.Selection([
        ('1', 'Banco do Brasil 18'),
        ('2', 'Barisul x'),
        ('3', 'Bradesco 06, 03'),
        ('4', 'Caixa Economica SR'),
        ('5', 'HSBC CNR CSB'),
        ('6', 'Itau 157'),
        ('7', 'Itau 175, 174, 178, 104, 109'),
        ('8', 'Real 57'),
        ('9', 'Santander 102'),
        ('10', 'Santander 101, 201'),
        ('11', 'Caixa Sigcb'),
        ('12', 'Sicredi')
    ], string="Boleto")
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
        string=u"Percentual de Juros de Mora",
        digits=dp.get_precision('Account')
    )
    instrucao_boleto_perc_mora = fields.Text(
        u'Instrução Juros Mora',
        help=u'Juros de mora - é o percentual ao'
             u' mês sobre o valor principal.',
        default=u'Após vencimento cobrar juros de mora de'
    )
    boleto_perc_multa = fields.Float(
        string=u"Percentual de Multa",
        digits=dp.get_precision('Account')
    )
    instrucao_boleto_perc_multa = fields.Text(
        u'Instrução Multa por Atraso',
        help=u' Multa por atraso - é o valor percentual acrescido uma única'
             u' vez sobre o valor do principal. ',
        default=u'Após vencimento cobrar multa de'
    )

    @api.constrains(
        'boleto_type', 'boleto_carteira', 'boleto_modalidade',
        'boleto_convenio', 'boleto_variacao', 'boleto_aceite',
    )
    def boleto_restriction(self):
        for record in self:

            if record.boleto_type == '6' and record.boleto_especie == '01':
                if not record.boleto_carteira:
                    raise UserError(_(u'Carteira no banco Itaú é obrigatória'))
                if len(record.boleto_convenio) < 6:
                    raise UserError(_(
                        u'O Convenio no banco Itaú deve ser'
                        u' igual ou menor que cinco digitos.'
                    ))
            if record.boleto_type == '4' and record.boleto_especie == '01':
                if (not record.boleto_carteira or
                        len(record.boleto_carteira) > 1):
                    raise UserError(_(
                        u'O campo Carteira no banco Caixa Economica é'
                        u' obrigatório e não pode ter mais de um caracter.'
                    ))
                if len(record.boleto_convenio) > 6:
                    raise UserError(_(
                        u'O cógido de Convenio da Caixa Economica'
                        u' não pode ser maior que seis caracteres.'
                    ))
            if (record.boleto_type in ('9', '10')
                    and record.boleto_especie == '01'):
                if len(record.boleto_convenio) > 7:
                    raise UserError(_(
                        u'O cógido de Convenio do Standander'
                        u' não pode ser maior que sete caracteres.'
                    ))
            if (record.boleto_type == '12'
                    and record.boleto_especie == '01'):
                if len(record.boleto_convenio) > 5:
                    raise UserError(_(
                        u'O cógido de Convenio do Sicredi'
                        u' não pode ser maior que cinco caracteres.'
                    ))

    @api.constrains('boleto_perc_mora', 'boleto_perc_multa')
    def _check_boleto_percent(self):
        for record in self:
            self.check_percent_field(record.boleto_perc_mora)
            self.check_percent_field(record.boleto_perc_multa)

    @api.multi
    def check_percent_field(self, value):
        if value > 100 or value < 0:
            raise UserError(
                _('O percentual deve ser um valor entre 0 a 100.'))
