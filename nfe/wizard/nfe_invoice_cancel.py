# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2014  Rafael da Silva Lima - KMEE, www.kmee.com.br               #
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

from openerp.osv import osv, fields
#from nfe.sped.nfe.processing.xml import cancel
# TODO: Encontrar o método de cancelamento no processing

class NfeInvoiceCancel(osv.osv_memory):
    _name='nfe.invoice_cancel'
    
    _columns = {
        'justificativa': fields.text('Justificativa', size=255, required=True),
    }
    
    def _check_name(self, cr, uid, ids):  
        for nfe in self.browse(cr, uid, ids):
            if not (len(nfe.justificativa) >= 15):
                return False
        return True
    
    _constraints = [(_check_name, 'Tamanho de justificativa inválida !', ['justificativa'])]
    
    def action_enviar_cancelamento(self, cr, uid, ids, context=None):
        
        data = {}
        data['ids'] = context.get('active_ids', [])
        
        if context is None:
            context = {}
            
        justificativa = self.browse(cr, uid, ids)[0].justificativa
        
        obj_invoice = self.pool.get('account.invoice')
        obj_invoice.cancel_invoice_online(cr, uid, data['ids'], justificativa)          
              
        return {'type': 'ir.actions.act_window_close'}     