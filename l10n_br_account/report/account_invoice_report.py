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

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        'Fiscal Category', readonly=True)
    state = fields.Selection(
        selection_add=[
            ('sefaz_export', u'Enviar para Receita'),
            ('sefaz_exception', u'Erro de autorização da Receita'),
            ('sefaz_cancelled', u'Cancelado no Sefaz'),
            ('sefaz_denied', u'Denegada no Sefaz'),
        ])

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + \
            ", sub.fiscal_category_id as fiscal_category_id"

    def _sub_select(self):
        return super(AccountInvoiceReport, self)._sub_select() + \
            ", ail.fiscal_category_id as fiscal_category_id"

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + \
            ", ail.fiscal_category_id"
