# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2012  Renato Lima - Akretion                                  #
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

from osv import fields, osv


class crm_lead(osv.Model):
    """ CRM Lead Case """
    _inherit = "crm.lead"
    _columns = {
        'l10n_br_city_id': fields.many2one(
            'l10n_br_base.city', 'Municipio',
            domain="[('state_id','=',state_id)]"),
        'district': fields.char('Bairro', size=32),
        'number': fields.char('Número', size=10)
    }

    def _create_lead_partner(self, cr, uid, lead, context=None):
        partner_id = super(crm_lead, self)._create_lead_partner(cr, uid, lead, context)
        self.pool.get('res.partner').write(cr, uid, [partner_id],
        {
            'number': lead.number,
            'district': lead.district,
            'l10n_br_city_id': lead.l10n_br_city_id.id
        })
        return partner_id
