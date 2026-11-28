# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class Tax(models.Model):
    _inherit = "l10n_br_fiscal.tax"

    def compute_taxes(self, **kwargs):
        manual_values = self.env.context.get("l10n_br_manual_tax_values")
        if manual_values:
            kwargs = {**manual_values, **kwargs}
        return super().compute_taxes(**kwargs)

    @api.model
    def _compute_tax_base(self, tax, tax_dict, **kwargs):
        # Applied here, and not in _compute_tax, so that the tax value is
        # computed from the manual base.
        tax_dict = super()._compute_tax_base(tax, tax_dict, **kwargs)
        base_manual = kwargs.get(f"{tax.tax_domain}_base_manual")
        if base_manual:
            tax_dict["base"] = base_manual
        return tax_dict

    @api.model
    def _compute_tax(self, tax, taxes_dict, **kwargs):
        tax_dict = super()._compute_tax(tax, taxes_dict, **kwargs)
        value_manual = kwargs.get(f"{tax.tax_domain}_value_manual")
        if value_manual:
            tax_dict["tax_value"] = value_manual
        return tax_dict

    @api.model
    def _compute_icmsst(self, tax, taxes_dict, **kwargs):
        # The core deducts the line's own ICMS from the ICMS ST value after
        # _compute_tax, which would alter a manually informed value.
        tax_dict = super()._compute_icmsst(tax, taxes_dict, **kwargs)
        value_manual = kwargs.get(f"{tax.tax_domain}_value_manual")
        if value_manual:
            tax_dict["tax_value"] = value_manual
        return tax_dict
