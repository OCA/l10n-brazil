# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2016  Magno Costa - Akretion
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

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
