# Copyright 2025-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models
from odoo.exceptions import UserError


class Company(models.Model):
    _inherit = "res.company"

    def write(self, values):
        """
        Overriden so we can change the currency_id of base.main_company during tests
        """
        try:
            result = super().write(values)
        except UserError as e:
            demo_main_company = self.env.ref(
                "base.main_company", raise_if_not_found=False
            )
            if (
                demo_main_company
                and self.ids == [demo_main_company.id]
                and values.get("currency_id")
                in (self.env.ref("base.BRL").id, self.env.ref("base.USD").id)
            ):
                result = models.Model.write(self, values)
            else:
                raise e

        return result
