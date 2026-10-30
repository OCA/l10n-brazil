# Copyright 2026 Engenere (<https://engenere.one>)
# Copyright 2026 - TODAY Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
import gzip
from io import BytesIO

from lxml import etree

from odoo import api, fields, models


def pretty_xml(value):
    """Return indented XML for display, or the original text when it is not XML.

    The stored payload stays unchanged. Indentation may rewrite whitespace
    and namespace layout, so the result is not the document the mock serves.
    """
    if not value:
        return False
    text = str(value)
    if "<" not in text:
        return text
    try:
        root = etree.fromstring(
            text.encode("utf-8"),
            etree.XMLParser(resolve_entities=False, no_network=True),
        )
    except etree.XMLSyntaxError:
        return text
    return etree.tostring(root, pretty_print=True, encoding="unicode")


class DfeMockNsu(models.Model):
    _name = "dfe.mock.nsu"
    _description = "DF-e Mock NSU"
    _order = "nsu"
    _rec_name = "nsu"

    # No index= here: the nsu_company_unique constraint below already
    # creates one with nsu as its leading column.
    nsu = fields.Char(string="NSU", size=15, required=True)
    # NF-e comes from the SEFAZ distribution service, NFS-e from the ADN,
    # each feed with its own cursor on the company.
    fiscal_type = fields.Selection(
        selection=[("nfe", "NF-e"), ("nfse", "NFS-e")],
        required=True,
        default="nfe",
        index=True,
    )
    schema_type = fields.Selection(
        selection=[
            ("resNFe", "resNFe"),
            ("procNFe", "procNFe"),
            ("resEvento", "resEvento"),
            ("procEventoNFe", "procEventoNFe"),
            ("NFSe", "NFSe"),
        ],
        required=True,
    )
    xml_content = fields.Text(required=True)
    xml_pretty = fields.Text(
        string="Indented XML",
        compute="_compute_xml_pretty",
    )
    access_key = fields.Char(size=50, help="44 digits for NF-e, 50 for NFS-e.")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    consumed = fields.Boolean(default=False)

    _sql_constraints = [
        (
            "nsu_company_unique",
            "UNIQUE(nsu, company_id, fiscal_type)",
            "NSU must be unique per company and fiscal type.",
        ),
    ]

    @api.depends("xml_content")
    def _compute_xml_pretty(self):
        for record in self:
            record.xml_pretty = pretty_xml(record.xml_content)

    def action_reset_consumed(self):
        self.write({"consumed": False})

    def _nfse_mock_lote_item(self):
        """Render this row as one ADN ``LoteDFe`` item, gzipped as the feed."""
        self.ensure_one()
        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb") as handle:
            handle.write((self.xml_content or "").encode("utf-8"))
        return {
            "NSU": self.nsu,
            "ChaveAcesso": self.access_key or "",
            "TipoDocumento": "NFSE",
            "ArquivoXml": base64.b64encode(buffer.getvalue()).decode("ascii"),
        }
