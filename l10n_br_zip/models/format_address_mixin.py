# Copyright (C) 2010-2012  Renato Lima (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class FormatAddressMixin(models.AbstractModel):
    _inherit = "format.address.mixin"

    def zip_search(self):
        self.ensure_one()
        return self.env["l10n_br.zip"].zip_search(self)

    def _fields_view_get_address(self, arch):
        address_view_id = self.env.company.country_id.address_view_id.sudo()
        for rec in address_view_id.inherit_children_ids:
            if rec.model != self._name:
                rec.model = None
        return super()._fields_view_get_address(arch)
