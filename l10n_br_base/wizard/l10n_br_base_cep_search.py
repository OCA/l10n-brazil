# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion                                    #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU Affero General Public License as published by    #
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

class l10n_br_base_cep_search(osv.osv_memory):
    _name = 'l10n_br_base.cep.search'
    _description = 'Zipcode Search'
    _inherit = "ir.wizard.screen"
    
    _columns = {
        'code': fields.char('CEP', size=8, required=True),
        #'street_type': fields.char('Tipo', size=26),
        'street': fields.char('Logradouro', size=72),
        'district': fields.char('Bairro', size=72),
        'state_id': fields.many2one('res.country.state', 'Estado', required=True),
        'l10n_br_city_id': fields.many2one('l10n_br_base.city', 'Cidade', required=True, domain="[('state_id','=',state_id)]"),
        #'cep_ids': fields.one2many('l10n_br_base.city', 'Cidade', required=True, domain="[('state_id','=',state_id)]"),
        'state':fields.selection([('init','init'),('done','done')], 'state', readonly=True),
    }
    
    _defaults = {
        'state': 'init'
    }
    
    def cep_search(self, cr, uid, ids, context=None):
        
        data = self.read(cr, uid, ids, [], context=context)[0]
        
        obj_cep = self.pool.get('l10n_br_base.cep')
        cep_ids = inv_obj.search(cr, uid, [
                                           '|',('code','=',data['code']),('code','=',False),
                                           '|',('street','=',data['street']),('street','=',False),
                                           '|',('district','=',data['district']),('district','=',False),
                                           '|',('state_id','=',data['state_id']),('state_id','=',False),
                                           '|',('l10n_br_city_id','=',data['l10n_br_city_id']),('l10n_br_city_id','=',False)])
         
        return False
    
l10n_br_base_cep_search()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
