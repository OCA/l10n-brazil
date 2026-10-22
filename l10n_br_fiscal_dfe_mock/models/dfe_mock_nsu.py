# Copyright 2026 Engenere (<https://engenere.one>)
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
import gzip
from io import BytesIO

from odoo import fields, models


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
