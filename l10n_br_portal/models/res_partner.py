# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = [_name, "l10n_br_base.party.mixin"]

    def can_edit_vat(self):
        can_edit_vat = super().can_edit_vat()
        if not can_edit_vat:
            return can_edit_vat
        return not self.vat
