# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models

from ..constants.dfe import (
    CSTAT_CONSUMO_INDEVIDO,
    DFE_INTERVAL_SUCCESS,
)


class NfeRecipientManifestationEvent(models.Model):
    _inherit = "l10n_br_nfe.md_event"

    dfe_document_id = fields.Many2one(
        string="Fiscal Document", comodel_name="l10n_br_fiscal_dfe.document"
    )

    def action_confirm(self):
        result = super().action_confirm()
        for record in self.filtered(lambda r: r.event_type == "ciente"):
            company = record.company_id
            # Never break 656 cooldown (would restart the 1h block timer)
            if company.dfe_last_status_code == CSTAT_CONSUMO_INDEVIDO:
                continue
            company.dfe_next_query = fields.Datetime.now() + DFE_INTERVAL_SUCCESS
            company._dfe_sync_cron_nextcall()
        return result
