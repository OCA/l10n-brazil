from odoo import _, fields, models


class NfeRecipientManifestationEventWizard(models.TransientModel):
    _name = "nfe_recipient_manifestation_event.wizard"
    _description = "Wizard to manifest"

    event_type_selection = fields.Selection(
        selection=[
            ("ciente", "Ciente da Operação"),
            ("confirmado", "Confirmada operação"),
            ("desconhecido", "Desconhecimento"),
            ("nao_realizado", "Não realizado"),
        ],
        default="ciente",
        required=True,
    )

    def action_create_nfe_recipient_manifestation_event(self):
        dfe_access_key_id = self.env.context.get("default_dfe_access_key_id")
        dfe_access_key = self.env["l10n_br_fiscal.dfe_access_key"].browse(
            dfe_access_key_id
        )

        mde = self.env["l10n_br_nfe.recipient_manifestation_event"].create(
            {
                "key": dfe_access_key.key,
                "event_type": self.event_type_selection,
                "event_type_selection": self.event_type_selection,
                "company_id": self.env.company.id,
                "dfe_access_key_id": dfe_access_key.id,
                "mde_document_type": "mde_nfe",
                "status": "transmitido",
            }
        )

        mde.action_confirm_selection()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Sucesso"),
                "message": _("MDe criado com sucesso"),
                "type": "success",
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
