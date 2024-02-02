# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


# pylint: disable=consider-merging-classes-inherited
class TaxDefinitionICMS(models.Model):
    _inherit = "l10n_br_fiscal.tax.definition"

    icms_regulation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.icms.regulation", string="ICMS Regulation"
    )

    def _get_search_domain(self, tax_definition):
        """Create domain to be used in contraints methods"""
        domain = super()._get_search_domain(tax_definition)
        if tax_definition.icms_regulation_id:
            domain.append(
                ("icms_regulation_id", "=", tax_definition.icms_regulation_id.id),
            )
        return domain

    @api.constrains("icms_regulation_id", "state_from_id")
    def _check_icms(self):
        for record in self:
            if record.icms_regulation_id:
                domain = self._get_search_domain(record)
                if record.env["l10n_br_fiscal.tax.definition"].search_count(domain):
                    raise ValidationError(
                        _(
                            "Tax Definition already exists "
                            "for this ICMS and Tax Group !"
                        )
                    )
