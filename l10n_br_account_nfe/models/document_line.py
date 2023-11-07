# Copyright (C) 2023 - TODAY Renan Hiroki Bastos - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    def reserve_map_taxes_ids(self):
        for line in self:
            line.icms_tax_id = self.env["l10n_br_fiscal.tax"].search(
                [
                    ("tax_group_id.name", "=", "ICMS"),
                    ("percent_amount", "=", line.icms_percent),
                    ("cst_in_id", "=", line.icms_cst_id.id),
                ],
                limit=1,
            )
            line.ipi_tax_id = self.env["l10n_br_fiscal.tax"].search(
                [
                    ("tax_group_id.name", "=", "IPI"),
                    ("percent_amount", "=", line.ipi_percent),
                ],
                limit=1,
            )
            line.pis_tax_id = self.env["l10n_br_fiscal.tax"].search(
                [
                    ("tax_group_id.name", "=", "PIS"),
                    ("percent_amount", "=", line.pis_percent),
                ],
                limit=1,
            )
            line.cofins_tax_id = self.env["l10n_br_fiscal.tax"].search(
                [
                    ("tax_group_id.name", "=", "COFINS"),
                    ("percent_amount", "=", line.cofins_percent),
                ],
                limit=1,
            )
            line._update_fiscal_tax_ids(line._get_all_tax_id_fields())
            line._update_taxes()

    @api.model_create_multi
    def create(self, vals_list):
        if self._context.get("create_from_move_line") and self._context.get(
            "create_from_document"
        ):
            return []
        else:
            documents = super().create(vals_list)
        return documents
