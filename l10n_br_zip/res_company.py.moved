# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    Thinkopen - Brasil
#    Copyright (C) Thinkopen Solutions (<http://www.thinkopensolutions.com.br>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm


class res_company(orm.Model):
    _inherit = 'res.company'

    def zip_search(self, cr, uid, ids, context=None):
        obj_zip = self.pool.get('l10n_br.zip')
        for res_company in self.browse(cr, uid, ids):
            zip_ids = obj_zip.zip_search_multi(
                cr, uid, ids, context,
                country_id=res_company.country_id.id,
                state_id=res_company.state_id.id,
                l10n_br_city_id=res_company.l10n_br_city_id.id,
                district=res_company.district,
                street=res_company.street,
                zip_code=res_company.zip,
            )

            zip_data = obj_zip.read(cr, uid, zip_ids, False, context)
            obj_zip_result = self.pool.get('l10n_br.zip.result')
            zip_ids = obj_zip_result.map_to_zip_result(
                cr, uid, 0, context, zip_data, self._name, ids[0])

            if len(zip_ids) == 1:  # FIXME
                result = obj_zip.set_result(cr, uid, ids, context, zip_data[0])
                self.write(cr, uid, [res_company.id], result, context)
                return True
            else:
                if len(zip_ids) > 1:
                    return obj_zip.create_wizard(
                        cr, uid, ids, context, self._name,
                        country_id=res_company.country_id.id,
                        state_id=res_company.state_id.id,
                        l10n_br_city_id=res_company.l10n_br_city_id.id,
                        district=res_company.district,
                        street=res_company.street,
                        zip_code=res_company.zip,
                        zip_ids=zip_ids
                    )
                else:
                    return True
