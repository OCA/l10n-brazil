# Copyright (C) 2021  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class FormatAddressMixin(models.AbstractModel):
    _inherit = "format.address.mixin"

    def _view_get_address(self, arch):
        # By default, the functionality to dynamically alter the view of address fields
        # only works for the `res.partner`. This workaround clears the model
        # reference in the view, enabling any model that extends the abstract
        # 'format.address.mixin' to have its address view dynamically modified as well.
        address_view_id = self.env.company.country_id.address_view_id.sudo()
        if address_view_id.model != self._name:
            address_view_id.model = None
        return super()._view_get_address(arch)
