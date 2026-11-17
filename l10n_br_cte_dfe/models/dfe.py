# Copyright 2026 Engenere.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models

from ..constants.cte_dfe import CTE_EVENT_LABELS


class DFe(models.Model):
    _inherit = "l10n_br_fiscal_dfe.dfe"

    @api.depends("event_type_dfe", "fiscal_type")
    def _compute_event_type_dfe_label(self):
        super()._compute_event_type_dfe_label()
        for record in self.filtered(lambda rec: rec.fiscal_type == "cte"):
            label = CTE_EVENT_LABELS.get(record.event_type_dfe)
            if label:
                record.event_type_dfe_label = _(label)
        return
