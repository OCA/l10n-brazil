# -*- coding: utf-8 -*-
# © 2016 KMEE(http://www.kmee.com.br)
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models
from openerp.addons import decimal_precision as dp

COMPANY_WITHHOLDING_TYPE = [
    ('1', u'Regime de Caixa'),
    ('2', u'Regime de Competência'),
]


class ResCompany(models.Model):
    _inherit = 'res.company'

    wh_type = fields.Selection(
        COMPANY_WITHHOLDING_TYPE, u'Forma de Retenção',
        help=u"Regime de Caixa: A retenção é aplicada caso soma dos \
            vencimentos mensais utrapasse os limites; Regime de \
            Competência: A retenção é aplicada caso a soma do valor\
            faturado  ultrapasse os limites")
    wh_on_nfe_limit = fields.Boolean(
        u'Retenção sempre que ultrapassar o valor da NF?')
    cofins_csll_pis_wh_base = fields.Float(
        u'Valor mínimo COFINS/CSLL/PIS', default=0.0,
        digits_compute=dp.get_precision('Account'))
    irrf_wh_base = fields.Float(
        u'Valor mínimo IRRF', default=10.0,
        digits_compute=dp.get_precision('Account'))
    inss_wh_base = fields.Float(
        u'Valor mínimo INSS', default=10.0,
        digits_compute=dp.get_precision('Account'))
    irrf_wh_percent = fields.Float(
        u'Taxa de IR(%)',
        digits_compute=dp.get_precision('Discount'),
        default=11.0)
    irrf_wh = fields.Boolean(u'Retém IRRF')
    issqn_wh = fields.Boolean(u'Retém ISSQN')
    inss_wh = fields.Boolean(u'Retém INSS')
    pis_wh = fields.Boolean(u'Retém PIS')
    cofins_wh = fields.Boolean(u'Retém COFINS')
    csll_wh = fields.Boolean(u'Retém CSLL')
