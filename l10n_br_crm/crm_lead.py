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
from crm.crm import crm_case


class crm_lead(crm_case, osv.osv):
    """ CRM Lead Case """
    _inherit = "crm.lead"
    _columns = {
        'l10n_br_city_id': fields.many2one(
            'l10n_br_base.city', 'Municipio',
            domain="[('state_id','=',state_id)]"),
        'district': fields.char('Bairro', size=32),
        'number': fields.char('Número', size=10)}

crm_lead()
