# Copyright 2025 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _existing_accounting(self) -> bool:
        has_accounting = super()._existing_accounting()
        demo_main_company = self.env.ref("base.main_company", raise_if_not_found=False)
        if has_accounting and demo_main_company and self.ids == [demo_main_company.id]:
            return False
        return has_accounting
