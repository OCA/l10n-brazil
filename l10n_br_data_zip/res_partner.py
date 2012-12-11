# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2010-2012  Renato Lima (Akretion)                             #
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
from osv import osv


class res_partner(osv.Model):
    _inherit = 'res.partner'

    #TODO migrate
    def zip_search(self, cr, uid, ids, context=None):

        result = {
                  'street': False,
                  'l10n_br_city_id': False,
                  'city': False,
                  'state_id': False,
                  'country_id': False,
                  'zip': False
                  }

        obj_zip = self.pool.get('l10n_br_data.zip')

        for res_partner_address in self.browse(cr, uid, ids):

            domain = []
            if res_partner_address.zip:
                zip = re.sub('[^0-9]', '', res_partner_address.zip or '')
                domain.append(('code', '=', zip))
            else:
                domain.append(('street', '=', res_partner_address.street))
                domain.append(('district', '=', res_partner_address.district))
                domain.append(('country_id', '=', \
                               res_partner_address.country_id.id))
                domain.append(('state_id', '=', \
                               res_partner_address.state_id.id))
                domain.append(('l10n_br_city_id', '=', \
                               res_partner_address.l10n_br_city_id.id))

            zip_id = obj_zip.search(cr, uid, domain)

            if not len(zip_id) == 1:

                context.update({
                                'zip': res_partner_address.zip,
                                'street': res_partner_address.street,
                                'district': res_partner_address.district,
                                'country_id': \
                                res_partner_address.country_id.id,
                                'state_id': res_partner_address.state_id.id,
                                'l10n_br_city_id': \
                                res_partner_address.l10n_br_city_id.id,
                                'address_id': ids,
                                'object_name': self._name,
                                })

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

            zip_read = obj_zip.read(cr, uid, zip_id, [
                                                      'street_type',
                                                      'street', 'district',
                                                      'code',
                                                      'l10n_br_city_id',
                                                      'city', 'state_id',
                                                      'country_id'
                                                      ],
                                    context=context)[0]

            zip = re.sub('[^0-9]', '', zip_read['code'] or '')
            if len(zip) == 8:
                zip = '%s-%s' % (zip[0:5], zip[5:8])

            result['street'] = ((zip_read['street_type'] or '') + ' ' \
                                + (zip_read['street'] or ''))
            result['district'] = zip_read['district']
            result['zip'] = zip
            result['l10n_br_city_id'] = zip_read['l10n_br_city_id'] \
            and zip_read['l10n_br_city_id'][0] or False
            result['city'] = zip_read['l10n_br_city_id'] \
            and zip_read['l10n_br_city_id'][1] or ''
            result['state_id'] = zip_read['state_id'] \
            and zip_read['state_id'][0] or False
            result['country_id'] = zip_read['country_id'] \
            and zip_read['country_id'][0] or False
            self.write(cr, uid, res_partner_address.id, result)
            return False
