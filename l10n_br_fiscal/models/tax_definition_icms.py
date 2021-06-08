# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TaxDefinitionICMS(models.Model):
    _inherit = "l10n_br_fiscal.tax.definition"

    icms_regulation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.icms.regulation", string="ICMS Regulation"
    )

    @api.constrains("icms_regulation_id", "state_from_id")
    def _check_icms(self):
        for record in self:
            if record.icms_regulation_id:
                domain = [
                    ("id", "!=", record.id),
                    ("icms_regulation_id", "=", record.icms_regulation_id.id),
                    ("state_from_id", "=", record.state_from_id.id),
                    ("state_to_ids", "in", record.state_to_ids.ids),
                    ("tax_group_id", "=", record.tax_group_id.id),
                    ("tax_id", "=", record.tax_id.id),
                ]

                if record.env["l10n_br_fiscal.tax.definition"].search_count(domain):
                    raise ValidationError(
                        _(
                            "Tax Definition already exists "
                            "for this ICMS and Tax Group !"
                        )
                    )
