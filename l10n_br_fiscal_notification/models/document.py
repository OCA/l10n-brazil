# Copyright (C) 2019  KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import SITUACAO_EDOC_AUTORIZADA


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _get_email_template(self, state):
        self.ensure_one()
        return self.document_type_id.document_email_ids.search(
            [
                "|",
                ("state_edoc", "=", False),
                ("state_edoc", "=", state),
                ("issuer", "=", self.issuer),
                "|",
                ("document_type_id", "=", False),
                ("document_type_id", "=", self.document_type_id.id),
            ],
            limit=1,
            order="state_edoc, document_type_id",
        ).mapped("email_template_id")

    def send_email(self, state):
        self.ensure_one()
        email_template = self._get_email_template(state)
        if email_template:
            email_template.with_context(
                default_attachment_ids=self._get_mail_attachment()
            ).send_mail(self.id)

    def _after_change_state(self, old_state, new_state):
        self.ensure_one()
        result = super()._after_change_state(old_state, new_state)
        self.send_email(new_state)
        return result

    def _get_mail_attachment(self):
        self.ensure_one()
        attachment_ids = []
        if self.state_edoc == SITUACAO_EDOC_AUTORIZADA:
            if self.file_report_id:
                attachment_ids.append(self.file_report_id.id)
            if self.authorization_file_id:
                attachment_ids.append(self.authorization_file_id.id)
        return attachment_ids

    def action_send_email(self):
        """Open a window to compose an email, with the fiscal document_type
        template message loaded by default
        """
        self.ensure_one()
        template = self._get_email_template(self.state)
        compose_form = self.env.ref("mail.email_compose_message_wizard_form", False)
        lang = self.env.context.get("lang")
        if template and template.lang:
            lang = template._render_template(template.lang, self._name, [self.id])
        self = self.with_context(lang=lang)
        ctx = dict(
            default_model="l10n_br_fiscal.document",
            default_res_id=self.id,
            default_use_template=bool(template),
            default_attachment_ids=self._get_mail_attachment(),
            default_template_id=template and template.id or False,
            default_composition_mode="comment",
            model_description=self.document_type_id.name or self._name,
            force_email=True,
        )
        return {
            "name": _("Send Fiscal Document Email Notification"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }
