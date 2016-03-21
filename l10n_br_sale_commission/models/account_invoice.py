# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api
from openerp.tools.safe_eval import safe_eval


class AccountInvoiceLineAgent(models.Model):
    _inherit = 'account.invoice.line.agent'

    @api.depends('commission.commission_type', 'invoice_line.price_subtotal',
                 'commission.amount_base_type')
    def _compute_amount(self):
        for line in self:
            line.amount = 0.0
            if (line.commission.amount_base_type == 'notax' and
                not line.invoice_line.product_id.commission_free and
                    line.commission):
                subtotal = line.invoice_line.price_gross
                if line.commission.commission_type == 'fixed':
                    line.amount = subtotal * (line.commission.fix_qty / 100.0)
                else:
                    line.amount = line.commission.calculate_section(subtotal)
            else:
                return super(AccountInvoiceLineAgent, line)._compute_amount()
