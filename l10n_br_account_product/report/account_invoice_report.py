# -*- coding: utf-8 -*-
# Copyright (C) 2016  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class AccountInvoiceReport(models.Model):

    _inherit = "account.invoice.report"

    cfop_id = fields.Many2one(
        'l10n_br_account_product.cfop', 'CFOP', readonly=True)

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + \
            ", sub.cfop_id as cfop_id"

    def _sub_select(self):
        return super(AccountInvoiceReport, self)._sub_select() + \
            ", ail.cfop_id as cfop_id"

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + \
            ", ail.cfop_id"
