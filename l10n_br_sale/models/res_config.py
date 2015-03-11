# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2014  Renato Lima - Akretion                                  #
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

from openerp import SUPERUSER_ID
from openerp.osv import orm, fields


class SaleConfiguration(orm.TransientModel):
    _inherit = 'sale.config.settings'
    _columns = {
        'copy_note': fields.boolean(
            u'Copiar Observações nos Documentos Fiscais'),
    }

    def _get_default_copy_note(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        result = ir_values.get_default(
            cr, uid, 'sale.order', 'copy_note', company_id=user.company_id.id)
        return result

    _defaults = {
        'copy_note': _get_default_copy_note,
    }

    def set_sale_defaults(self, cr, uid, ids, context=None):

        result = super(SaleConfiguration, self).set_sale_defaults(
            cr, uid, ids, context)
        wizard = self.browse(cr, uid, ids, context)[0]
        ir_values = self.pool.get('ir.values')

        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        ir_values.set_default(cr, SUPERUSER_ID, 'sale.order', 'copy_note',
            wizard.copy_note, company_id=user.company_id.id)
        return result
