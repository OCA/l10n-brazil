# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2014  Renato Lima - Akretion
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    sale_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        u'Categoria Fiscal Padrão Compras',
        domain="[('journal_type', '=', 'sale')]")
