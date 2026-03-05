# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import binascii
import logging
from io import BytesIO

from lxml import objectify
from lxml.etree import XMLSyntaxError

from odoo import _, api, fields, models
from odoo.exceptions import UserError

try:
    from brazilfiscalreport.danfe import Danfe
except ImportError:
    Danfe = None

_logger = logging.getLogger(__name__)


class L10nBrFiscalDfeDocument(models.Model):
    _inherit = "l10n_br_fiscal_dfe.document"

    cfop_ids = fields.Many2many("l10n_br_fiscal.cfop", compute="_compute_nfe_cfop_ids")
    manifestations_ids = fields.One2many("l10n_br_nfe.md_event", "dfe_document_id")

    manifestation_status = fields.Selection(
        selection=[
            ("ciente", "Ciente da Operação"),
            ("confirmado", "Confirmada operação"),
            ("desconhecido", "Desconhecimento"),
            ("nao_realizado", "Não realizado"),
            ("sem_manifestacao", "Sem manifestação"),
        ],
        compute="_compute_manifestation_status",
    )

    @api.depends("manifestations_ids.state")
    def _compute_manifestation_status(self):
        """Compute manifestation status efficiently with batched queries."""
        if not self:
            return

        access_keys = tuple(self.mapped("access_key"))

        # Batch query: get latest event per access key in a single query
        self.env.cr.execute(
            """
            SELECT DISTINCT ON (access_key) access_key, event_type
            FROM l10n_br_nfe_md_event
            WHERE access_key IN %s AND state = 'done'
            ORDER BY access_key, id DESC
            """,
            (access_keys,),
        )
        latest_events = dict(self.env.cr.fetchall())

        for record in self:
            record.manifestation_status = latest_events.get(
                record.access_key, "sem_manifestacao"
            )

    def create_nfe_md_action(self):
        self.ensure_one()
        return {
            "name": _("Manifestação do Destinatário"),
            "type": "ir.actions.act_window",
            "res_model": "nfe_recipient_manifestation_event.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_access_key": self.access_key,
            },
        }

    @api.depends("dfe_ids.attachment_id")
    def _compute_nfe_cfop_ids(self):
        Cfop = self.env["l10n_br_fiscal.cfop"]
        for rec in self:
            rec.cfop_ids = Cfop
            if rec.fiscal_type != "nfe":
                continue
            complete = rec.dfe_ids.filtered(lambda d: d.document_type_dfe == "complete")
            if complete and complete.attachment_id:
                try:
                    xml_bytes = base64.b64decode(complete.attachment_id.datas)
                    root = objectify.fromstring(xml_bytes)
                    codes = {str(det.prod.CFOP) for det in root.NFe.infNFe.det}
                    rec.cfop_ids = Cfop.search([("code", "in", list(codes))])
                except (
                    binascii.Error,
                    XMLSyntaxError,
                    AttributeError,
                    ValueError,
                ) as e:
                    _logger.warning("Error computing CFOP IDs: %s", e)

    def import_document(self):
        if self.fiscal_type != "nfe":
            return super().import_document()
        complete = self._get_complete_dfe()
        if not complete:
            raise UserError(_("Can only import Complete NF-e."))
        xml_bytes = base64.b64decode(complete.attachment_id.datas)
        return self.company_id.parse_procNFe(BytesIO(xml_bytes))

    def make_pdf(self):
        if self.fiscal_type != "nfe":
            return super().make_pdf()
        complete = self._get_complete_dfe()
        if not complete:
            raise UserError(_("No complete DF-e found."))

        xml_bytes = base64.b64decode(complete.attachment_id.datas)
        danfe = Danfe(xml=xml_bytes)
        buf = BytesIO()
        danfe.output(buf)

        pdf_att = self.env["ir.attachment"].create(
            {
                "name": f"DANFE_{complete.access_key}.pdf",
                "datas": base64.b64encode(buf.getvalue()),
                "mimetype": "application/pdf",
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{pdf_att.id}?download=true",
            "target": "self",
        }
