# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2010  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

import time
import netsvc
from osv import fields, osv
import decimal_precision as dp
import pooler
from tools import config
from tools.translate import _


class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _columns = {
        'carrier_id':fields.many2one("delivery.carrier", "Carrier",
                                     readonly=True,
                                     states={'draft':[('readonly',False)]}),
        'vehicle_id': fields.many2one('l10n_br_delivery.carrier.vehicle',
                                      'Veículo', readonly=True,
                                      states={'draft': [('readonly', False)]}),
        'incoterm': fields.many2one('stock.incoterms', 'Tipo do Frete',
                                    readonly=True,
                                    states={'draft': [('readonly', False)]},
                                    help="Incoterm which stands for \
                                    'International Commercial terms' implies \
                                    its a series of sales terms which are \
                                    used in the commercial transaction."),}

    def nfe_check(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).nfe_check(cr, uid, ids)
        strErro = ''
        for inv in self.browse(cr, uid, ids):
            #Carrier
            if inv.carrier_id:

                if not inv.carrier_id.partner_id.legal_name:
                    strErro = 'Transportadora - Razão Social\n'

                if not inv.carrier_id.partner_id.cnpj_cpf:
                    strErro = 'Transportadora - CNPJ/CPF\n'

            #Carrier Vehicle
            if inv.vehicle_id:

                if not inv.vehicle_id.plate:
                    strErro = 'Transportadora / Veículo - Placa\n'

                if not inv.vehicle_id.plate.state_id.code:
                    strErro = 'Transportadora / Veículo - UF da Placa\n'

                if not inv.vehicle_id.rntc_code:
                    strErro = 'Transportadora / Veículo - RNTC\n'
        if strErro:
            raise osv.except_osv(
                _('Error !'),
                _("Validação da Nota fiscal:\n '%s'") % (strErro.encode('utf-8')))

        return res

account_invoice()
