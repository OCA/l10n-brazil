# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import binascii
import logging

from lxml import etree
from lxml.etree import XMLSyntaxError

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DFe(models.Model):
    _name = "l10n_br_fiscal_dfe.dfe"
    _description = "DF-e Abstract Record"
    _order = "id desc"

    dfe_document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal_dfe.document", string="DF-e Document"
    )
    access_key = fields.Char(size=44, index=True)
    nsu = fields.Char(string="NSU", size=25, index=True)
    fiscal_type = fields.Selection(
        selection=[("nfe", "NF-e"), ("cte", "CT-e")],
        required=True,
    )
    schema_type = fields.Char(
        help="Type of the DF-e document according to the XML schema."
    )
    operation_type = fields.Char()
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        readonly=True,
    )

    # Replaces dfe_nfe_document_type to be agnostic
    document_type_dfe = fields.Selection(
        selection=[
            ("complete", "Complete XML (proc)"),
            ("summary", "Summary (res)"),
            ("event", "Event"),
        ],
        string="DF-e Document Type",
    )
    attachment_id = fields.Many2one(comodel_name="ir.attachment")
    xml_pretty = fields.Text(string="XML Pretty", compute="_compute_xml_pretty")
    event_type_dfe = fields.Char(string="Event Type")

    def name_get(self):
        result = []
        for rec in self:
            doc_type = dict(rec._fields["document_type_dfe"].selection).get(
                rec.document_type_dfe
            )
            result.append((rec.id, f"{rec.access_key} - {doc_type}"))
        return result

    def create_xml_attachment(self, xml):
        self.sudo().attachment_id = self.env["ir.attachment"].create(
            {
                "name": f"{self.schema_type}_{self.access_key}.xml",
                "datas": base64.b64encode(xml),
                "res_model": self._name,
                "res_id": self.id,
            }
        )

    def action_download_xml(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": (
                f"/web/content/{self.attachment_id.id}"
                f"/{self.attachment_id.name}?download=true"
            ),
            "target": "self",
        }

    @api.depends("attachment_id")
    def _compute_xml_pretty(self):
        for rec in self:
            rec.xml_pretty = ""
            if not rec.attachment_id:
                continue
            data = rec.attachment_id.with_context(bin_size=False).datas
            if data:
                try:
                    root = etree.fromstring(base64.b64decode(data))
                    rec.xml_pretty = etree.tostring(
                        root, pretty_print=True, encoding="unicode"
                    )
                except (binascii.Error, XMLSyntaxError) as e:
                    _logger.warning("Error parsing XML: %s", e)
