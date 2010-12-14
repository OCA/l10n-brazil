# -*- coding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion                                    #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU General Public License as published by           #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU General Public License for more details.                                   #
#                                                                               #
#You should have received a copy of the GNU General Public License              #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

from osv import osv, fields
import base64

class l10n_br_account_nfe_export(osv.osv_memory):
    """ Exportar Nota Fiscal Eletrônica """

    _name = "l10n_br_account.nfe_export"
    _description = "Update Module"
    _inherit = "ir.wizard.screen"

    _columns = {
        'file': fields.binary('Arquivo', readonly=True),
        'file_type': fields.selection([('xml','XML'),('txt','TXT')], 'Tipo do Arquivo'),
        'import_status_draft': fields.boolean('Importar NFs com status em rascunho'),
        'state':fields.selection([('init','init'),('done','done')], 'state', readonly=True),
    }

    _defaults = {
        'state': 'init',
        'file_type': 'txt',
        'import_status_draft': False,
    }

    def nfe_export(self, cr, uid, ids, context=None):
        
        inv_obj = self.pool.get('account.invoice')
        inv_ids = inv_obj.search(cr, uid, [('state','=','sefaz_export')])

        #for inv in inv_obj.browse(cr, uid, inv_ids):
        data = self.read(cr, uid, ids, [], context=context)[0]
        if data['file_type'] == 'xml':
            file = inv_obj.nfe_export_xml(cr, uid, inv_ids)
        else:
            file = inv_obj.nfe_export_txt(cr, uid, inv_ids)
        file_total = file
            
        self.write(cr, uid, ids, {'file': base64.b64encode(file_total), 'state': 'done'}, context=context)
        return False

    #def action_module_open(self, cr, uid, ids, context):
    #    res = {
    #        'domain': str([]),
    #        'name': 'Modules',
    #        'view_type': 'form',
    #        'view_mode': 'tree,form',
    #        'res_model': 'ir.module.module',
    #        'view_id': False,
    #        'type': 'ir.actions.act_window',
    #    }
    #    return res

l10n_br_account_nfe_export()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: