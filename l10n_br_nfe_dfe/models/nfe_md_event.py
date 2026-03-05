# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.l10n_br_fiscal_dfe.constants.dfe import (
    CSTAT_CONSUMO_INDEVIDO,
    DFE_INTERVAL_SUCCESS,
)


class NfeRecipientManifestationEvent(models.Model):
    _inherit = "l10n_br_nfe.md_event"

    # This is the missing inverse field causing the KeyError
    dfe_document_id = fields.Many2one(
        string="DF-e Document",
        comodel_name="l10n_br_fiscal_dfe.document",
        index=True,
    )

    def action_confirm(self):
        """
        When a manifestation (like Ciência) is confirmed, we should
        schedule a new DF-e query soon to get the full XML.
        """
        result = super().action_confirm()
        for record in self.filtered(lambda r: r.event_type == "ciente"):
            company = record.company_id
            # Never break 656 cooldown (would restart the 1h block timer)
            if getattr(company, "dfe_last_status_code", "") == CSTAT_CONSUMO_INDEVIDO:
                continue

            # Reset the schedule to query soon
            company.nfe_dfe_next_query = fields.Datetime.now() + DFE_INTERVAL_SUCCESS
        return result
