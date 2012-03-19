# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2012  Renato Lima - Akretion                                    #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU Affero General Public License as published by    #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU Affero General Public License for more details.                            #
#                                                                               #
#You should have received a copy of the GNU Affero General Public License       #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

class crm_make_sale(osv.osv_memory):
	_inherit = "crm.make.sale"

	def makeOrder(self, cr, uid, ids, context=None):
        result = super(crm_make_sale, self).makeOrder(cr, uid, ids, context)
        return result

crm_make_sale()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
