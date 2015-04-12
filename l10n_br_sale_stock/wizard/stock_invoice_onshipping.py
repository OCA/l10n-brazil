# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2014  Luis Felipe Mileo - KMEE                                #
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

from openerp import models

class StockInvoiceOnShipping(models.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    def get_picking_jornal_id(self, picking):
        """
        Retorna o diário da categoria fiscal definida na categoria da operação,
        TODO: Este metodo deve ser sobrecrito pelo sale_stock!
        :param picking:
        :return:
        """
        sale = picking.sale_id
        if picking.sale_id:
            return sale.fiscal_category_id.property_journal.id
        else:
            return super(StockInvoiceOnShipping, self).get_picking_jornal_id(picking)