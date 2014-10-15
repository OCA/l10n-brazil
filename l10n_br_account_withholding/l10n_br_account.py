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

class L10n_brAccountPartnerFiscalType(orm.Model):
    _inherit = 'l10n_br_account.partner.fiscal.type'

    _columns = {
        'issqn_wh': fields.boolean(u'Retém ISSQN'),
        'inss_wh': fields.boolean(u'Retém INSS'),
        'pis_wh': fields.boolean(u'Retém PIS'),
        'cofins_wh': fields.boolean(u'Retém COFINS'),
        'csll_wh': fields.boolean(u'Retém CSLL'),
        'irrf_wh': fields.boolean(u'Retém IRRF'),
        'irrf_wh_percent': fields.float(u'Retenção de IRRF (%)',
               digits_compute=dp.get_precision('Discount')),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: