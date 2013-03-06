# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             # 
# Copyright (C) 2011  Renato Lima - Akretion                                  #
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

import re
import string

from openerp.osv import osv, fields


    
class l10n_br_data_zip_search(osv.TransientModel):

    _name = 'l10n_br_data.zip.search'

    _description = 'Zipcode Search'

    _columns = {
        'code': fields.char('CEP', size=8),
        'street': fields.char('Logradouro', size=72),
        'district': fields.char('Bairro', size=72),
        'country_id': fields.many2one('res.country', 'Country'),
        'state_id': fields.many2one(
            "res.country.state", 'Estado',
            domain="[('country_id','=',country_id)]"),
        'l10n_br_city_id': fields.many2one(
            'l10n_br_base.city', 'Cidade',
            domain="[('state_id','=',state_id)]"),

        'zip_ids': fields.many2many('l10n_br_data.zip.result','zip_search',
                                    'zip_id', 'zip_search_id', 'CEP',
                                    readonly=False),
        
        'state':fields.selection([('init','init'),
                                  ('done','done')], 'state', readonly=True),
        'address_id': fields.integer('Id do objeto', invisible=True),
        'object_name': fields.char('Nome do bjeto', size=100, invisible=True),
    }
    
    _defaults = {
        'state': 'init'}

    def create(self, cr, uid, vals, context):
        
        result = super(l10n_br_data_zip_search, self).create(cr, uid, vals, context)
        
        context.update({'search_id': result})
        
        return result
        
    def default_get(self, cr, uid, fields_list, context=None):
        
        if context is None:
            context = {}
        
        data = super(l10n_br_data_zip_search, self).default_get(
            cr, uid, fields_list, context)
        
        data['code'] = context.get('zip', False)
        data['street'] = context.get('street', False)
        data['district'] = context.get('district', False)
        data['country_id'] = context.get('country_id', False)
        data['state_id'] = context.get('state_id', False)
        data['l10n_br_city_id'] = context.get('l10n_br_city_id', False)
        data['address_id'] = context.get('address_id', False)
        data['object_name'] = context.get('object_name', False)
        
        return data
    
    def zip_search(self, cr, uid, ids, context=None):

        data = self.read(cr, uid, ids, [], context=context)[0]

        obj_zip = self.pool.get('l10n_br_data.zip')
        
        obj_zip_result = self.pool.get('l10n_br_data.zip.result')

        domain = obj_zip.set_domain(country_id = data['country_id'][0], \
                                    state_id = data['state_id'][0], \
                                    l10n_br_city_id = data['l10n_br_city_id'][0],\
                                    district = data['district'], \
                                    street = data['street'], \
                                    zip = data['code'])
        
        # Search zip_ids
        zip_ids = obj_zip.search(cr, uid, domain)
        
        #TODO: MAP zip to zip.search.result
        zip_result_ids = obj_zip_result.map_to_zip_result(cr, uid, ids, context, data['id'], zip_ids)
        
        self.write(cr, uid, ids, 
                   {'state': 'done',
                    'zip_ids': [[6, 0, zip_result_ids]]}, context=context)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_br_data.zip.search',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': data['id'],
            'views': [(False, 'form')],
            'target': 'new',
            'nodestroy': True,
        } 
    
    def zip_new_search(self, cr, uid, ids, context=None):
        
        data = self.read(cr, uid, ids, [], context=context)[0]
        
        self.write(cr, uid, ids, 
                   {'state': 'init',
                    'zip_ids': [[6, 0, []]]}, context=context)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_br_data.zip.search',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': data['id'],
            'views': [(False, 'form')],
            'target': 'new',
            'nodestroy': True
        } 

    def zip_search_end(self, cr, uid, ids, context=None):

        data = self.read(cr, uid, ids, [], context=context)[0]
        
        address_id = data['address_id']
            
        object_name = data['object_name']
        
        zip_id = False
                
        if address_id and object_name:
            
            obj_zip_result = self.pool.get('l10n_br_data.zip.result')
            
            for zip_id_aux in data['zip_ids']:
            
                zip_result_data = obj_zip_result.read(cr, uid, zip_id_aux, [], context=context)
                
                if zip_result_data['selected'] ==  True:
                    
                    zip_id = zip_result_data['zip_id'][0]
                    
                    break
        
        if not zip_id == False:
                  
            obj = self.pool.get(object_name)

            obj_zip = self.pool.get('l10n_br_data.zip')

            result = obj_zip.set_result(cr, uid, ids, context, zip_id)
                
            obj.write(cr, uid, address_id, result, context=context)
  
        return {'type': 'ir.actions.act_window_close'}
    
    
class l10n_br_data_zip_result(osv.TransientModel):

    _name = 'l10n_br_data.zip.result'

    _description = 'Zipcode result'
    
    _columns = {
        'zip_id': fields.many2one('l10n_br_data.zip', 'Zipcode', readonly=True, invisible=True),
        'search_id': fields.many2one('l10n_br_data.zip.search', 'Search', readonly=True, invisible=True),
        'selected': fields.boolean('Selecionado', readonly=True),
        #ZIPCODE data to be shown
        'code': fields.char('CEP', size=9, readonly=True),
        'street': fields.char('Logradouro', size=72, readonly=True),
        'district': fields.char('Bairro', size=72, readonly=True),
        'country_id': fields.many2one('res.country', 'Country', readonly=True),
        'state_id': fields.many2one('res.country.state', 'Estado',
                                    domain="[('country_id','=',country_id)]", readonly=True),
        'l10n_br_city_id': fields.many2one(
            'l10n_br_base.city', 'Cidade',
            required=True, domain="[('state_id','=',state_id)]", readonly=True),        
        }


    def map_to_zip_result(self, cr, uid, ids, context, search_id, zip_ids):
        
        obj_zip = self.pool.get('l10n_br_data.zip')
      
        result = []
        
        for zip_id in zip_ids:
            
            zip_data = obj_zip.set_result(cr, uid, ids, context, zip_id)
            
            zip_result_data = {
                'selected': False,
                'zip_id': False,
                'code': False,
                'street': False,
                'district': False,
                'country_id': False,
                'state_id': False,
                'l10n_br_city_id': False,
                }
                    
            zip_result_data['zip_id'] = zip_id
            zip_result_data['search_id'] = search_id
            zip_result_data['code'] = zip_data['zip']
            zip_result_data['street'] = zip_data['street']
            zip_result_data['district'] = zip_data['district']
            zip_result_data['country_id'] = zip_data['country_id']
            zip_result_data['state_id'] = zip_data['state_id']
            zip_result_data['l10n_br_city_id'] = zip_data['l10n_br_city_id']
            
            
            zip_result_id = self.create(cr, uid, zip_result_data, context=context)
            
            result.append(zip_result_id)
        
        return result
    
    def zip_select(self, cr, uid, ids, context=None):
        # Alternar facilmente entre selecao em 1 ou 2 passos
        return self.zip_select_one_step(cr, uid, ids, context)
        
    def zip_select_one_step(self, cr, uid, ids, context=None):
        
        data = self.read(cr, uid, ids, [], context=context)[0]
        
        obj_search = self.pool.get('l10n_br_data.zip.search')
        
        search_id = data['search_id'][0]
        
        self.write(cr, uid, ids, {'selected': True})
        
        return obj_search.zip_search_end(cr, uid, [search_id], context)
        
    def zip_select_two_step(self, cr, uid, ids, context=None):
        
        data = self.read(cr, uid, ids, [], context=context)[0]
        
        obj_search = self.pool.get('l10n_br_data.zip.search')
        
        search_id = data['search_id'][0]
               
        zip_ids = obj_search.read(cr, uid, search_id, ['zip_ids'], context=context)
                                        
        # Marca a linha selecionada e desmarca as demais
        for zip_id in zip_ids['zip_ids']:
            
            zip_id_aux = self.read(cr, uid, zip_id, ['zip_id'], context=context)
            
            if zip_id_aux['zip_id'][0] == data['zip_id'][0]:
                
                self.write(cr, uid, zip_id, {'selected': True})
            
            else:
                
                self.write(cr, uid, zip_id, {'selected': False})
            
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_br_data.zip.search',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': search_id,
            'views': [(False, 'form')],
            'target': 'new',
            'nodestroy': True,
        } 
        

