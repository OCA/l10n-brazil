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

from osv import osv, fields


class l10n_br_base_zip_search(osv.osv_memory):
    _name = 'l10n_br_base.zip.search'
    _description = 'Zipcode Search'
    _inherit = 'ir.wizard.screen'
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
        'zip_ids': fields.many2many('l10n_br_base.zip','zip_search',
                                    'zip_id', 'zip_search_id', 'CEP',
                                    readonly=True),
        'state':fields.selection([('init','init'),
                                  ('done','done')], 'state', readonly=True)}
    
    _defaults = {
        'state': 'init'}

    def default_get(self, cr, uid, fields_list, context=None):
        
        if context is None:
            context = {}
        
        data = super(l10n_br_base_zip_search, self).default_get(
            cr, uid, fields_list, context)
        
        data['code'] = context.get('zip', False)
        data['street'] = context.get('street', False)
        data['district'] = context.get('district', False)
        data['country_id'] = context.get('country_id', False)
        data['state_id'] = context.get('state_id', False)
        data['l10n_br_city_id'] = context.get('l10n_br_city_id', False)
        
        return data

    def zip_search(self, cr, uid, ids, context=None):

        data = self.read(cr, uid, ids, [], context=context)[0]

        domain = [
                   ('country_id','=',data['country_id'][0]),
                   ('state_id','=',data['state_id'][0]),
                   ('l10n_br_city_id','=',data['l10n_br_city_id'][0]),]
        
        if data['code']:
            zip = re.sub('[^0-9]', '', data['code'] or '')
            domain.append(('code','=',zip))
        
        if data['street']:
            domain.append(('street','=',data['street']))
            
        if data['district']:
            domain.append(('district','=',data['district']))

        obj_zip = self.pool.get('l10n_br_base.zip')
        zip_ids = obj_zip.search(cr, uid, domain)
        
        self.write(cr, uid, ids, 
                   {'state': 'done',
                    'zip_ids': [[6, 0, zip_ids]]}, context=context)
        return False
    
    def zip_search_end(self, cr, uid, ids, context=None):

        result = {
                  'street': False, 
                  'l10n_br_city_id': False, 
                  'city': False, 
                  'state_id': False, 
                  'country_id': False, 
                  'zip': False
                  }

        data = self.read(cr, uid, ids, [], context=context)[0]

        if data['zip_ids']:
            address_id = context.get('address_id', False)
            object_name = context.get('object_name', False)
            if address_id and object_name:
                obj_zip = self.pool.get('l10n_br_base.zip')
                zip_read = obj_zip.read(
                    cr, uid, data['zip_ids'], ['street_type', 
                                               'street',
                                               'district', 
                                               'code',
                                               'l10n_br_city_id', 
                                               'city', 'state_id', 
                                               'country_id'], context=context)[0]

                zip = re.sub('[^0-9]', '', zip_read['code'] or '')
                if len(zip) == 8:
                    zip = '%s-%s' % (zip[0:5], zip[5:8])

                result['street'] = ((zip_read['street_type'] or '') + ' ' + (zip_read['street'] or ''))
                result['district'] = zip_read['district']
                result['zip'] = zip
                result['l10n_br_city_id'] = zip_read['l10n_br_city_id'] and zip_read['l10n_br_city_id'][0] or False
                result['city'] = zip_read['l10n_br_city_id'] and zip_read['l10n_br_city_id'][1] or ''
                result['state_id'] = zip_read['state_id'] and zip_read['state_id'][0] or False
                result['country_id'] = zip_read['country_id'] and zip_read['country_id'][0] or False

                obj_partner = self.pool.get(object_name)
                obj_partner.write(cr, uid, address_id, result, context=context)

        return {'type': 'ir.actions.act_window_close'}

l10n_br_base_zip_search()
