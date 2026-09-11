from odoo import _, fields, models


class NfeRecipientManifestationEventWizard(models.TransientModel):
    _name = "nfe_recipient_manifestation_event.wizard"
    _description = "Wizard to manifest"

    access_key = fields.Char(size=44, required=True)

    event_type = fields.Selection(
        selection=[
            ("ciente", "Ciente da Operação"),
            ("confirmado", "Confirmada operação"),
            ("desconhecido", "Desconhecimento"),
            ("nao_realizado", "Não realizado"),
        ],
        default="ciente",
        required=True,
    )

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        access_key = self.env.context.get("default_access_key")
        res.update({"access_key": access_key})
        return res

    def action_create_nfe_md_event(self):
        mde = self.env["l10n_br_nfe.md_event"].create(
            {
                "access_key": self.access_key,
                "event_type": self.event_type,
                "company_id": self.env.company.id,
                "document_type": "nfe",
                "state": "draft",
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
