# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2011  Vinicius Dittgen - PROGE, Leonardo Santagada - PROGE      #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU Affero General Public License as published by    #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU Affero General Public License for more details.                            #
#                                                                               #
#You should have received a copy of the GNU Affero General Public License       #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

from osv import fields, osv
from tools.translate import _
import base64


class nfe_export_from_invoice(osv.osv_memory):
    """ Export fiscal eletronic file from invoice"""

    _name = "l10n_br_account.nfe_export_from_invoice"
    _description = "Export fiscal eletronic file from invoice"
    _inherit = "ir.wizard.screen"
    _columns = {
        'file': fields.binary('Arquivo', readonly=True),
        'company_id': fields.many2one('res.company', 'Company'),
        'file_type': fields.selection([('xml', 'XML'),
                               ('txt', ' TXT')], 'Tipo do Arquivo'),
        'state': fields.selection([('init', 'init'),
                               ('done', 'done')], 'state', readonly=True),
        }
    _defaults = {
        'state': 'init',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=c),
        'file_type': 'txt',
        }

    def nfe_export_from_invoice(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, [], context=context)[0]
        inv_obj = self.pool.get('account.invoice')
        active_ids = context.get('active_ids', [])
        export_inv_ids = []
        err_msg = ''

        for inv in inv_obj.browse(cr, uid, active_ids, context=context):
            if inv.state not in ('sefaz_export', 'open', 'paid'):
                err_msg += u'A Fatura %s não pode ser exportada pois ainda não foi confirmada ou foi cancelada.\n' % inv.internal_number
            elif not inv.own_invoice:
                err_msg += u'A Fatura %s é do tipo externa e não pode ser exportada para a receita.\n' % inv.internal_number
            else:
                inv_obj.write(cr, uid, [inv.id], {'nfe_export_date': False, 'nfe_access_key': False, 'nfe_status': False, 'nfe_date': False})
                message = 'A fatura %s foi exportada.' % inv.internal_number
                inv_obj.log(cr, uid, inv.id, message)
                export_inv_ids.append(inv.id)

        if export_inv_ids:
            if data['file_type'] == 'xml':
                nfe_file = inv_obj.nfe_export_xml(cr, uid, export_inv_ids)
            else:
                nfe_file = inv_obj.nfe_export_txt(cr, uid, export_inv_ids)
            self.write(cr, uid, ids, {'file': base64.b64encode(nfe_file), 'state': 'done'}, context=context)

        if err_msg:
            raise osv.except_osv(_('Error !'), _("'%s'") % (err_msg, ))

        return False

nfe_export_from_invoice()

