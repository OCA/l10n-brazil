# Copyright (C) 2025-Today - Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from io import BytesIO

from brazilfiscalreport.danfe import Danfe

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccessKey(models.Model):
    _name = "l10n_br_fiscal.dfe_access_key"
    _description = ""

    key = fields.Char(size=44, required=True)

    dfe_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.dfe",
        inverse_name="dfe_access_key_id",
        string="DFe",
    )

    emitter = fields.Char(related="dfe_ids.emitter")

    vat = fields.Char(related="dfe_ids.vat")

    document_amount = fields.Float(
        string="Document Total Value", digits=(18, 2), related="dfe_ids.document_amount"
    )

    document_state = fields.Selection(related="dfe_ids.document_state")

    document_number = fields.Float(related="dfe_ids.document_number")

    serie = fields.Char(related="dfe_ids.serie")

    dfe_monitor_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.dfe_monitor",
        string="Monitor de DFe",
    )

    _sql_constraints = [
        (
            "unique_key",
            "UNIQUE(key)",
            "The access key already exists",
        ),
    ]

    color_status = fields.Selection(
        [
            ("green", "NF-e Completa"),
            ("blue", "Resumo da NF-e"),
            ("normal", "Evento da NF-e"),
        ],
        compute="_compute_color_status",
    )

    manifestation_status = fields.Selection(
        selection=[
            ("ciente", "Ciente da Operação"),
            ("confirmado", "Confirmada operação"),
            ("desconhecido", "Desconhecimento"),
            ("nao_realizado", "Não realizado"),
            ("sem_manifestacao", "Sem manifestação"),
        ],
        default="sem_manifestacao",
    )

    @api.depends("dfe_ids.dfe_nfe_document_type")
    def _compute_color_status(self):
        for record in self:
            types = record.dfe_ids.mapped("dfe_nfe_document_type")
            if "dfe_nfe_complete" in types:
                record.color_status = "green"
            elif "dfe_nfe_summary" in types:
                record.color_status = "blue"
            else:
                record.color_status = "normal"

    def name_get(self):
        return [(record.id, record.key) for record in self]

    def action_download_xml(self):
        complete_dfe_ids = self.dfe_ids.filtered(
            lambda dfe: dfe.dfe_nfe_document_type == "dfe_nfe_complete"
        )
        if complete_dfe_ids:
            return complete_dfe_ids.action_download_xml()
        raise UserError(
            _("It is only possible to download XML when DF-e is completed.")
        )

    def make_pdf(self):
        complete_dfe_ids = self.dfe_ids.filtered(
            lambda dfe: dfe.dfe_nfe_document_type == "dfe_nfe_complete"
        )

        if not complete_dfe_ids:
            raise UserError(_("No DF-e with 'DF-e complete' type found."))

        complete_dfe = complete_dfe_ids[0]
        attachment = complete_dfe.attachment_id
        nfe_xml = base64.b64decode(attachment.datas)
        danfe = Danfe(xml=nfe_xml)

        tmpDanfe = BytesIO()
        danfe.output(tmpDanfe)
        danfe_file = tmpDanfe.getvalue()
        tmpDanfe.close()

        pdf_attachment = self.env["ir.attachment"].create(
            {
                "name": f"DANFE{complete_dfe.key}.pdf",
                "type": "binary",
                "datas": base64.b64encode(danfe_file),
                "res_model": self._name,
                "res_id": complete_dfe.id,
                "mimetype": "application/pdf",
            }
        )

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{pdf_attachment.id}?download=true",
            "target": "self",
        }

    def create_mde_action(self):
        return {
            "name": _("Manifestação do Destinatário"),
            "type": "ir.actions.act_window",
            "res_model": "nfe_recipient_manifestation_event.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_dfe_access_key_id": self.id,
            },
        }

    def import_document(self):
        complete_dfe_ids = self.dfe_ids.filtered(
            lambda dfe: dfe.dfe_nfe_document_type == "dfe_nfe_complete"
        )
        if complete_dfe_ids:
            return complete_dfe_ids.import_document()
        raise UserError(_("You can only import the NF-e when the DF-e is completed."))

    @api.model
    def update_manifestation_status(self):
        EVENT_TYPE_MAP = {
            "210200": "Confirmada operação",
            "210210": "Ciente da Operação",
            "210220": "Desconhecimento da Operação",
            "210240": "Operação não realizada",
        }

        dfe_events = self.env["l10n_br_fiscal.dfe"].search(
            [("dfe_nfe_document_type", "=", "dfe_nfe_event")],
            order="emission_datetime desc",
        )

        latest_events = {}

        for dfe in dfe_events:
            if dfe.key not in latest_events:
                latest_events[dfe.key] = dfe.event_type_dfe

        for key, event_code in latest_events.items():
            event_desc = EVENT_TYPE_MAP.get(event_code, "sem_manifestacao")

            access_key = self.search([("key", "=", key)], limit=1)
            if access_key:
                access_key.write({"manifestation_status": event_desc})
        return True
