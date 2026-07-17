# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class FiscalTaxGroup(models.Model):
    _inherit = "l10n_br_fiscal.tax.group"

    def account_tax_group(self):
        self.ensure_one()
        return self.env["account.tax.group"].search(
            [("fiscal_tax_group_id", "in", self.ids)], limit=1
        )

    def _account_tax_group_map(self):
        """Return {fiscal_tax_group_id: account.tax.group} for ``self`` in a
        single search, instead of one search per fiscal tax group."""
        result = {group.id: self.env["account.tax.group"] for group in self}
        if not self:
            return result
        account_tax_groups = self.env["account.tax.group"].search(
            [("fiscal_tax_group_id", "in", self.ids)]
        )
        for account_tax_group in account_tax_groups:
            fiscal_group_id = account_tax_group.fiscal_tax_group_id.id
            # account_tax_group() usa limit=1: preserva o primeiro encontrado.
            if not result.get(fiscal_group_id):
                result[fiscal_group_id] = account_tax_group
        return result
