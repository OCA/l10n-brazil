# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2011  Renato Lima - Akretion
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


class sale_report(models.Model):
    _inherit = "sale.report"
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        'Fiscal Category',
        readonly=True),
    fiscal_position = fields.Many2one(
        'account.fiscal.position',
        'Fiscal Position',
        readonly=True)

    def _select(self):
        return super(sale_report, self)._select() + \
            ", l.fiscal_category_id as fiscal_category_id, " \
            "l.fiscal_position as fiscal_position"

    def _group_by(self):
        return super(sale_report, self)._group_by() + \
            ", l.fiscal_category_id, l.fiscal_position"
