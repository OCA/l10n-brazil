# Copyright 2026 - TODAY, Cristiano Mafra Junior - Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class NfeRecipientManifestationEventWizard(models.TransientModel):
    _inherit = "nfe_recipient_manifestation_event.wizard"

    dfe_document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal_dfe.document",
    )

    def action_create_nfe_md_event(self):
        mde = self.env["l10n_br_nfe.md_event"].create(
            {
                "access_key": self.access_key,
                "event_type": self.event_type,
                "company_id": self.env.company.id,
                "document_type": "nfe",
                "state": "draft",
                "dfe_document_id": self.dfe_document_id.id,
            }
        )

        mde.action_confirm()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": _("Recipient Manifestation created successfully"),
                "type": "success",
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
