# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


# pylint: disable=consider-merging-classes-inherited
class TaxDefinitionPartnerProfile(models.Model):
    _inherit = "l10n_br_fiscal.tax.definition"

    fiscal_profile_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.partner.profile", string="Partner Profile"
    )

    @api.constrains("fiscal_profile_id")
    def _check_fiscal_profile_id(self):
        for record in self:
            if record.fiscal_profile_id:
                domain = [
                    ("id", "!=", record.id),
                    ("fiscal_profile_id", "=", record.fiscal_profile_id.id),
                    ("tax_group_id", "=", record.tax_group_id.id),
                    ("tax_id", "=", record.tax_id.id),
                ]

                if record.env["l10n_br_fiscal.tax.definition"].search_count(domain):
                    raise ValidationError(
                        _(
                            "Tax Definition already exists "
                            "for this Partner Profile and Tax Group !"
                        )
                    )
