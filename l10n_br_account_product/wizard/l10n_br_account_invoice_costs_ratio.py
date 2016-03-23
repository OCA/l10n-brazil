# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Daniel Sadamo <sadamo@kmee.com.br>
#    @author Luis Felipe Mileo <mileo@kmee.com.br>
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

from openerp import models, fields, api
from openerp.addons.l10n_br_base.tools.misc import calc_price_ratio


class L10nBrAccountProductInvoiceCostsRatio(models.TransientModel):

    _name = 'l10n_br_account_product.invoice.costs_ratio'
    _description = 'Ratio costs on invoice'

    amount_freight_value = fields.Float('Frete')
    amount_insurance_value = fields.Float('Seguro')
    amount_costs_value = fields.Float('Outros Custos')

    @api.multi
    def set_invoice_costs_ratio(self):

        if not self._context.get('active_model') in 'account.invoice':
            return False
        for delivery in self:
            for invoice in self.env['account.invoice'].browse(
                    self._context.get('active_ids', [])):
                for line in invoice.invoice_line:
                    vals = {
                        'freight_value': calc_price_ratio(
                            line.price_gross,
                            delivery.amount_freight_value,
                            invoice.amount_gross),
                        'insurance_value': calc_price_ratio(
                            line.price_gross,
                            delivery.amount_insurance_value,
                            invoice.amount_gross),
                        'other_costs_value': calc_price_ratio(
                            line.price_gross,
                            delivery.amount_costs_value,
                            invoice.amount_gross),
                        }
                    line.write(vals)
                invoice.button_reset_taxes()
        return True
