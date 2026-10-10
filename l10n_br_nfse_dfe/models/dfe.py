# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..constants.nfse_dfe import NFSE_EVENT_LABELS


class DFe(models.Model):
    _inherit = "l10n_br_fiscal_dfe.dfe"

    fiscal_type = fields.Selection(
        selection_add=[("nfse", "NFS-e")],
        ondelete={"nfse": "cascade"},
    )

    @api.depends("event_type_dfe", "fiscal_type")
    def _compute_event_type_dfe_label(self):
        super()._compute_event_type_dfe_label()
        for record in self.filtered(lambda rec: rec.fiscal_type == "nfse"):
            code = record.event_type_dfe
            if not code:
                continue
            label = NFSE_EVENT_LABELS.get(code)
            if not label and code[:1] in "eE":
                label = NFSE_EVENT_LABELS.get(code[1:])
            if label:
                record.event_type_dfe_label = self.env._(label)
        return
