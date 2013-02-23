# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2012  Renato Lima (Akretion)                                  #
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
from osv import osv, fields


class l10n_br_data_zip(osv.Model):
    """ Este objeto persiste todos os códigos postais que podem ser
    utilizados para pesquisar e auxiliar o preenchimento dos endereços.
    """
    _name = 'l10n_br_data.zip'
    _description = 'CEP'
    _rec_name = 'code'
    _columns = {
        'code': fields.char('CEP', size=8, required=True),
        'street_type': fields.char('Tipo', size=26),
        'street': fields.char('Logradouro', size=72),
        'district': fields.char('Bairro', size=72),
        'country_id': fields.many2one('res.country', 'Country'),
        'state_id': fields.many2one('res.country.state', 'Estado',
                                    domain="[('country_id','=',country_id)]"),
        'l10n_br_city_id': fields.many2one(
            'l10n_br_base.city', 'Cidade',
            required=True, domain="[('state_id','=',state_id)]"),
    }

    def set_domain(self, country_id=False, state_id=False, l10n_br_city_id=False, district=False, street=False, zip=False):
        
        domain = []
        
        if zip:
            new_zip = re.sub('[^0-9]', '', zip or '')
            domain.append(('code', '=', new_zip))
        else:
            
            if country_id:
               domain.append(('country_id', '=', country_id))
            
            if state_id:
                domain.append(('state_id', '=', state_id))
            
            if l10n_br_city_id:
                domain.append(('l10n_br_city_id', '=', l10n_br_city_id))

            if district:
                domain.append(('district', 'like', district))

            if street:
                domain.append(('street', 'like', street))
        
        return domain
    
    def set_result(self, cr, uid, ids, context, zip_id=None):

        result = {
            'country_id': False,
            'state_id': False,
            'l10n_br_city_id': False,
            'district': False,
            'street': False,
            'zip': False
        }
        
        if zip_id != None:        
        
            zip_read = self.read(cr, uid, zip_id, [
                                                      'street_type',
                                                      'street', 
                                                      'district',
                                                      'code',
                                                      'l10n_br_city_id',
                                                      'state_id',
                                                      'country_id'
                                                      ],
                                    context=context)[0]

            zip = zip_read['code']
            
            if len(zip) == 8:
                zip = '%s-%s' % (zip[0:5], zip[5:8])
            
            result = {
                'country_id': zip_read['country_id'] and zip_read['country_id'][0] or False,
                'state_id': zip_read['state_id'] and zip_read['state_id'][0] or False,
                'l10n_br_city_id': zip_read['l10n_br_city_id'] and zip_read['l10n_br_city_id'][0] or False,
                'district': (zip_read['district'] or ''),
                'street': ((zip_read['street_type'] or '') + ' ' + (zip_read['street'] or '')),
                'zip': zip,
            }
        
        return result
            
                
    def zip_search(self, cr, uid, ids, context, country_id=False, state_id=False, l10n_br_city_id=False, district=False, street=False, zip=False):
        
        result = self.set_result(cr, uid, ids, context)
         
        domain = self.set_domain(country_id = country_id, 
                                 state_id = state_id, 
                                 l10n_br_city_id = l10n_br_city_id,
                                 district = district,
                                 street = street,
                                 zip = zip)
        
        zip_id = self.search(cr, uid, domain)
        
        if len(zip_id) == 1:
            
            result = self.set_result(cr, uid, ids, context, zip_id)
            
            return result
                    
        else:
            
            return False
    
    def create_wizard(self, cr, uid, ids, context, object_name, country_id=False, state_id=False, l10n_br_city_id=False, district=False, street=False, zip=False):

        context.update({'zip': zip,
                        'street': street,
                        'district': district,
                        'country_id': country_id,
                        'state_id': state_id,
                        'l10n_br_city_id': l10n_br_city_id,
                        'address_id': ids,
                        'object_name': object_name})

        result = {
                    'name': 'Zip Search',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'l10n_br_data.zip.search',
                    'view_id': False,
                    'context': context,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'nodestroy': True,
                    }
             
        return result

class l10n_br_data_zip_result(osv.osv_memory):
    _name = 'l10n_br_data.zip.result'
    _description = 'Zipcode result'
    
    _columns = {
        'selected': fields.boolean('Selecionar'),
        'zip_id': fields.many2one('l10n_br_data.zip', 'Zipcode', readonly=True, invisible=True),
        #ZIPCODE data to be shown
        'code': fields.char('CEP', size=8, readonly=True),
        'street': fields.char('Logradouro', size=72, readonly=True),
        'district': fields.char('Bairro', size=72, readonly=True),
        'country_id': fields.many2one('res.country', 'Country', readonly=True),
        'state_id': fields.many2one('res.country.state', 'Estado',
                                    domain="[('country_id','=',country_id)]", readonly=True),
        'l10n_br_city_id': fields.many2one(
            'l10n_br_base.city', 'Cidade',
            required=True, domain="[('state_id','=',state_id)]", readonly=True),        
        }


    def map_to_zip_result(self, cr, uid, ids, context, zip_ids):
        
        obj_zip = self.pool.get('l10n_br_data.zip')
      
        result = []
        
        for zip_id in zip_ids:
            
            zip_data = obj_zip.set_result(cr, uid, ids, context, [zip_id])
            
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
            zip_result_data['code'] = zip_data['zip']
            zip_result_data['street'] = zip_data['street']
            zip_result_data['district'] = zip_data['district']
            zip_result_data['country_id'] = zip_data['country_id']
            zip_result_data['state_id'] = zip_data['state_id']
            zip_result_data['l10n_br_city_id'] = zip_data['l10n_br_city_id']
            
            
            zip_result_id = self.create(cr, uid, zip_result_data, context=context)
            
            result.append(zip_result_id)
        
        return result
    
      
l10n_br_data_zip_result()