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
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.osv.osv import except_osv


class l10n_br_zip(orm.Model):
    """ Este objeto persiste todos os códigos postais que podem ser
    utilizados para pesquisar e auxiliar o preenchimento dos endereços.
    """
    _name = 'l10n_br.zip'
    _description = 'CEP'
    _rec_name = 'zip'
    _columns = {
        'zip': fields.char('CEP', size=8, required=True),
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
            domain.append(('zip', '=', new_zip))
        else:
            if state_id == False or \
               l10n_br_city_id == False or\
               len(street or '') == 0:
               raise except_osv(u'Parametros insuficientes',
                                u'Necessário informar Estado, município e logradouro') 
            
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
    
    def set_result(self, cr, uid, ids, context, zip_read=None):
        if zip_read != None:
            zip = zip_read['zip']
            if len(zip) == 8:
                zip = '%s-%s' % (zip[0:5], zip[5:8])
            print "ùùùùùùùùù", zip_read
            result = {
                'country_id': zip_read['country_id'] and zip_read['country_id'][0] or False,
                'state_id': zip_read['state_id'] and zip_read['state_id'][0] or False,
                'l10n_br_city_id': zip_read['l10n_br_city_id'] and zip_read['l10n_br_city_id'][0] or False,
                'district': (zip_read['district'] or ''),
                'street': ((zip_read['street_type'] or '') + ' ' + (zip_read['street'] or '')),
                'zip': zip,
            }
        else:
            result = {}
	print "hhhhhhhhhh", result
        return result
            
                
    def zip_search_multi(self, cr, uid, ids, context, country_id=False, state_id=False, l10n_br_city_id=False, district=False, street=False, zip=False):
        domain = self.set_domain(country_id = country_id, 
                                 state_id = state_id, 
                                 l10n_br_city_id = l10n_br_city_id,
                                 district = district,
                                 street = street,
                                 zip = zip)
        return self.search(cr, uid, domain)
    
    def zip_search(self, cr, uid, ids, context, country_id=False, state_id=False, l10n_br_city_id=False, district=False, street=False, zip=False):
        result = self.set_result(cr, uid, ids, context)
        zip_id = self.zip_search_multi(cr, uid, ids, context, 
                                       country_id,
                                       state_id,
                                       l10n_br_city_id,
                                       district,
                                       street,
                                       zip)
        if len(zip_id) == 1:
            result = self.set_result(cr, uid, ids, context, zip_id[0])
            return result
        else:
            return False
    
    def create_wizard(self, cr, uid, ids, context, object_name, country_id=False, state_id=False, l10n_br_city_id=False, district=False, street=False, zip=False, zip_ids=False):
        context.update({'zip': zip,
                        'street': street,
                        'district': district,
                        'country_id': country_id,
                        'state_id': state_id,
                        'l10n_br_city_id': l10n_br_city_id,
                        'zip_ids': zip_ids,
                        'address_id': ids[0],
                        'object_name': object_name})
        result = {
                    'name': 'Zip Search',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'l10n_br.zip.search',
                    'view_id': False,
                    'context': context,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'nodestroy': True,
                    }
        return result
