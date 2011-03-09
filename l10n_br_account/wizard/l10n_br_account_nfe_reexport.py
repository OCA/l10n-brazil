# -*- coding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2011  Renato Lima - Akretion                                    #
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
from tools.translate import _

class l10n_br_account_nfe_reexport(osv.osv_memory):
    """ Exportar Nota Fiscal Eletrônica """

    _name = "l10n_br_account.nfe.reexport"
    _description = "Reexportação de Nota Fiscal Eletrônica"
    
    def view_init(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        res = super(l10n_br_account_nfe_reexport, self).view_init(cr, uid, fields_list, context=context)
        inv_obj = self.pool.get('account.invoice')
        count = 0
        active_ids = context.get('active_ids',[])
        for inv in inv_obj.browse(cr, uid, active_ids, context=context):
            if inv.state != 'sefaz_export' and inv.own_invoice:
                count += 1
        if len(active_ids) == 1 and count:
            raise osv.except_osv(_('Warning !'), _('This invoice can not be reexport.'))
        if len(active_ids) == count:
            raise osv.except_osv(_('Warning !'), _('None of these invoices can not be reexport.'))
        return res
    
    def nfe_reexport(self, cr, uid, ids, context=None):
        
        data = self.read(cr, uid, ids, [], context=context)[0]
        
        inv_obj = self.pool.get('account.invoice')
        inv_ids = inv_obj.search(cr, uid, [('state','=','sefaz_export'),('id','in',ids),('own_invoice','=',True)])
        active_id = context.get('active_id', False)
        
        inv_obj.write(cr, uid, [active_id], {'nfe_export_date': False, 'nfe_access_key': False, 'nfe_status': False, 'nfe_date': False })
        
        for inv in inv_obj.browse(cr, uid, [active_id], context=context):
            message = _("The Invoice Id '%s', Internal Number '%s' has been set to be reexport.") %(inv.id, inv.internal_number,)
            inv_obj.log(cr, uid, inv.id, message)
        
        return {'type': 'ir.actions.act_window_close'}

l10n_br_account_nfe_reexport()