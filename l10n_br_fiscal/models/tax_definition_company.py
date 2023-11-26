# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, models
from odoo.exceptions import ValidationError


# pylint: disable=consider-merging-classes-inherited
class TaxDefinitionCompany(models.Model):
    _inherit = "l10n_br_fiscal.tax.definition"

    @api.constrains("company_id")
    def _check_company_id(self):
        for record in self:
            if record.company_id:
                domain = [
                    ("id", "!=", record.id),
                    ("company_id", "=", record.company_id.id),
                    ("tax_group_id", "=", record.tax_group_id.id),
                    ("tax_id", "=", record.tax_id.id),
                ]

                if record.env["l10n_br_fiscal.tax.definition"].search_count(domain):
                    raise ValidationError(
                        _(
                            "Tax Definition already exists "
                            "for this Company and Tax Group !"
                        )
                    )
