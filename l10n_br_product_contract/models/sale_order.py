# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.multi
    def _prepare_contract_value(self, contract_template):
        values = super()._prepare_contract_value(contract_template)
        values.update(self._prepare_br_fiscal_dict())
        return values
