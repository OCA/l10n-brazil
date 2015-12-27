# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2015 - Luis Felipe Miléo - KMEE                               #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

import time

from openerp import models, fields, api


class AccountFiscalPositionRule(models.Model):
    _inherit = 'account.fiscal.position.rule'

    def product_fcp_map(self, product_id, to_state=None):
        result = self.env['account.tax']
        fiscal_classification_id = self.env['product.product'].browse(
            product_id).fiscal_classification_id
        fcp = self.env[
            'l10n_br_tax.fcp'].search(
            [('fiscal_classification_id', '=', fiscal_classification_id.id),
             '|', ('to_state_id', '=', False),
             ('to_state_id', '=', to_state.id)])
        if fcp:
            result |= fcp.fcp_tax_id
        else:
            result |= to_state.fcp_tax_id
        return result
