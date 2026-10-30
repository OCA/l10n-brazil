# Copyright 2026 - TODAY Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# Copyright 2026 Engenere (<https://engenere.one>)
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
import gzip
from io import BytesIO

from odoo import api, fields, models
from odoo.exceptions import UserError

# Supplier cancellation registered at the ADN (e101101). The note row stays
# as it was distributed; the event is a later NSU on the same feed.
NFSE_MOCK_CANCEL_EVENT_CODE = "101101"
_NFSE_EVENT_NS = "http://www.sped.fazenda.gov.br/nfse"


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
            ("EVENTO", "EVENTO"),
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

    @api.model
    def _next_nfse_nsu(self, company):
        last = self.search(
            [
                ("company_id", "=", company.id),
                ("fiscal_type", "=", "nfse"),
            ],
            order="nsu desc",
            limit=1,
        )
        if not last:
            return 1
        return int(last.nsu) + 1

    def _nfse_cancellation_event(self):
        """Return the pooled supplier-cancellation event of this note."""
        self.ensure_one()
        return self.search(
            [
                ("company_id", "=", self.company_id.id),
                ("fiscal_type", "=", "nfse"),
                ("schema_type", "=", "EVENTO"),
                ("access_key", "=", self.access_key),
            ],
            limit=1,
        )

    def _nfse_cancellation_event_xml(self):
        """National event the ADN distributes after the supplier cancels.

        The code is the ``e101101`` child of ``infPedReg``. The note XML is
        left authorized; the connector derives the cancelled state from this
        event.
        """
        self.ensure_one()
        access_key = self.access_key
        code = NFSE_MOCK_CANCEL_EVENT_CODE
        ident = f"PRE{access_key}{code}001"
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<evento xmlns="{_NFSE_EVENT_NS}" versao="1.00">'
            "<infEvento>"
            '<pedRegEvento versao="1.00">'
            f'<infPedReg Id="{ident}">'
            f"<chNFSe>{access_key}</chNFSe>"
            f"<e{code}>"
            "<xDesc>Cancellation</xDesc>"
            f"</e{code}>"
            "</infPedReg>"
            "</pedRegEvento>"
            "</infEvento>"
            "</evento>"
        )

    def action_register_nfse_cancellation(self):
        """Queue a supplier cancellation event for the selected NFS-e notes.

        Does not rewrite the note. The next NFS-e distribution, or a search
        by the same access key, receives the event and updates the inbox.
        """
        if self.filtered(
            lambda rec: rec.fiscal_type != "nfse" or rec.schema_type != "NFSe"
        ):
            raise UserError(
                self.env._(
                    "Select the NFS-e note. The cancellation is a new event "
                    "in the feed, not a change of this row."
                )
            )
        created = self.browse()
        for company in self.company_id:
            current = self._next_nfse_nsu(company)
            notes = self.filtered(
                lambda rec, company=company: rec.company_id == company
            )
            for note in notes:
                if note._nfse_cancellation_event():
                    continue
                if not note.access_key:
                    raise UserError(
                        self.env._("This NFS-e note has no access key to cancel.")
                    )
                created |= self.create(
                    {
                        "nsu": str(current).zfill(15),
                        "fiscal_type": "nfse",
                        "schema_type": "EVENTO",
                        "xml_content": note._nfse_cancellation_event_xml(),
                        "access_key": note.access_key,
                        "company_id": company.id,
                    }
                )
                current += 1
        if not created:
            raise UserError(
                self.env._(
                    "This NFS-e already has a cancellation event in the mock pool."
                )
            )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("NFS-e cancellation"),
                "message": self.env._(
                    "Queued %(count)s cancellation event(s). Run the NFS-e "
                    "distribution to update the inbox.",
                    count=len(created),
                ),
                "type": "success",
                "sticky": False,
            },
        }

    def _nfse_mock_lote_item(self):
        """Render this row as one ADN ``LoteDFe`` item, gzipped as the feed."""
        self.ensure_one()
        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb") as handle:
            handle.write((self.xml_content or "").encode("utf-8"))
        item = {
            "NSU": self.nsu,
            "ChaveAcesso": self.access_key or "",
            "TipoDocumento": "NFSE",
            "ArquivoXml": base64.b64encode(buffer.getvalue()).decode("ascii"),
        }
        if self.schema_type == "EVENTO":
            item["TipoDocumento"] = "EVENTO"
            item["TipoEvento"] = NFSE_MOCK_CANCEL_EVENT_CODE
        return item
