# Copyright (C) 2019  Renato Lima - Akretion
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# Copyright (C) 2023  Antônio S. Pereira Neto - Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..constants.fiscal import TAX_FRAMEWORK_SIMPLES


class SimplifiedTax(models.Model):
    _name = "l10n_br_fiscal.simplified.tax"
    _description = "National Simplified Tax"

    name = fields.Char(required=True)

    cnae_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.cnae",
        domain="[('internal_type', '=', 'normal')]",
        string="CNAEs",
    )

    simplified_tax_range_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.simplified.tax.range",
        inverse_name="simplified_tax_id",
        string="Simplified Tax Range",
        copy=False,
    )

    coefficient_r = fields.Boolean(
        readonly=True,
    )

    def _get_range(self, revenue):
        """Range of the annex a gross revenue of the last 12 months falls into."""
        return self.simplified_tax_range_ids.filtered(
            lambda tax_range: tax_range.inital_revenue
            <= revenue
            <= tax_range.final_revenue
        )[:1]

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override the create method to update the effective tax lines in all companies
        """
        simplified_taxes = super().create(vals_list)
        self.env["res.company"].sudo().search(
            [("tax_framework", "=", TAX_FRAMEWORK_SIMPLES)]
        )._update_effective_tax_lines()
        return simplified_taxes
