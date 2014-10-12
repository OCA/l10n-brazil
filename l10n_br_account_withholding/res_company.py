# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Mileo <mileo@kmee.com.br>
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

from openerp.osv import orm, fields
from openerp.addons import decimal_precision as dp

COMPANY_WITHHOLDING_TYPE = [
    ('1', 'Regime de Caixa'),
    ('2', u'Regime de Competência'),
]

class ResCompany(orm.Model):

    _inherit = 'res.company'
    _columns = {
        'wh_type': fields.selection(COMPANY_WITHHOLDING_TYPE,
            u'Forma de Retenção',  help=u"Regime de Caixa: A retenção é aplicada caso soma dos vencimentos\
            mensais utrapasse os limites; Regime de Competência: A retenção é aplicada caso a soma do valor faturado \
              ultrapasse os limites"),
        'wh_on_nfe_limit': fields.boolean(
            u'Retenção sempre que ultrapassar o valor da NF?'),
        'irrf_wh_percent': fields.float(
            u'Alícota de IRRF (%)',
            digits_compute=dp.get_precision('Account')),
        'irrf_wh_value': fields.float(
            u'Valor mínimo IRRF',
            digits_compute=dp.get_precision('Account')),
        'cofins_wh_value': fields.float(
            u'Valor mínimo COFINS',
            digits_compute=dp.get_precision('Account')),
        'pis_wh_value': fields.float(
            u'Valor mínimo PIS',
            digits_compute=dp.get_precision('Account')),
        'csll_wh_value': fields.float(
            u'Valor mínimo CSLL',
            digits_compute=dp.get_precision('Account')),
        'issqn_wh': fields.boolean(
            u'Retém ISSQN'),
        'inss_wh': fields.boolean(
            u'Retém INSS'),
        'pis_wh': fields.boolean(
            u'Retém PIS'),
        'cofins_wh': fields.boolean(
            u'Retém COFINS'),
        'csll_wh': fields.boolean(
            u'Retém CSLL'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: