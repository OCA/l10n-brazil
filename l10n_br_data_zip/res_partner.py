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

from openerp.osv import orm


class res_partner(orm.Model):
    _inherit = 'res.partner'

    def zip_search(self, cr, uid, ids, context=None):
        obj_zip = self.pool.get('l10n_br_data.zip')
        for res_partner in self.browse(cr, uid, ids):
            zip_ids = obj_zip.zip_search_multi(cr, uid, ids, context,
                                        country_id = res_partner.country_id.id, \
                                        state_id = res_partner.state_id.id, \
                                        l10n_br_city_id = res_partner.l10n_br_city_id.id, \
                                        district = res_partner.district, \
                                        street = res_partner.street, \
                                        zip = res_partner.zip,
                                        )
            if len(zip_ids) == 1:
                result = obj_zip.set_result(cr, uid, ids, context, zip_ids[0])
                self.write(cr, uid, [res_partner.id], result, context)
                return True
            else:
                if len(zip_ids) > 1:
                    return obj_zip.create_wizard(cr, uid, ids, context, self._name,
                                        country_id = res_partner.country_id.id, \
                                        state_id = res_partner.state_id.id, \
                                        l10n_br_city_id = res_partner.l10n_br_city_id.id, \
                                        district = res_partner.district, \
                                        street = res_partner.street, \
                                        zip = res_partner.zip,
                                        zip_ids = zip_ids
                                        )
                else:
                    return True
