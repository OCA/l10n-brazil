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
        relation="fiscal_simplified_tax_cnae_rel",
        column1="simplified_tax_id",
        column2="cnae_id",
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

    @api.model
    def create(self, vals):
        """Override create for update effective tax lines in all companys"""
        record = super().create(vals)
        companies = self.env["res.company"].search(
            [("tax_framework", "=", TAX_FRAMEWORK_SIMPLES)]
        )
        for company in companies:
            company.update_effective_tax_lines()
        return record
