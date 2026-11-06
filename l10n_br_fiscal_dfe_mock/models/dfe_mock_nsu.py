# Copyright 2026 Engenere (<https://engenere.one>)
# Copyright 2026 - TODAY Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
import gzip
import re
from io import BytesIO

from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import UserError

# Supplier cancellation registered at the ADN (e101101). The note row stays
# as it was distributed; the event is a later NSU on the same feed.
NFSE_MOCK_CANCEL_EVENT_CODE = "101101"
_NFSE_EVENT_NS = "http://www.sped.fazenda.gov.br/nfse"
# Supplier cancellation registered at SEFAZ. The procNFe stays authorized;
# the connector only stores this event on the inbox document.
NFE_MOCK_CANCEL_EVENT_CODE = "110111"
_NFE_EVENT_NS = "http://www.portalfiscal.inf.br/nfe"
_NFE_NOTE_SCHEMAS = ("resNFe", "procNFe")


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
            ("EVENTO", "EVENTO"),
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

    @api.model
    def _next_mock_nsu(self, company, fiscal_type):
        last = self.search(
            [
                ("company_id", "=", company.id),
                ("fiscal_type", "=", fiscal_type),
            ],
            order="nsu desc",
            limit=1,
        )
        if not last:
            return 1
        return int(last.nsu) + 1

    def _next_nfse_nsu(self, company):
        return self._next_mock_nsu(company, "nfse")

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
        return self._cancellation_notification(
            self.env._("NFS-e cancellation"),
            self.env._(
                "Queued %(count)s cancellation event(s). Run the NFS-e "
                "distribution to update the inbox.",
                count=len(created),
            ),
        )

    def _nfe_cancellation_event(self):
        """Return the pooled supplier-cancellation event of this NF-e."""
        self.ensure_one()
        marker = f"<tpEvento>{NFE_MOCK_CANCEL_EVENT_CODE}</tpEvento>"
        return self.search(
            [
                ("company_id", "=", self.company_id.id),
                ("fiscal_type", "=", "nfe"),
                ("schema_type", "=", "procEventoNFe"),
                ("access_key", "=", self.access_key),
            ]
        ).filtered(lambda rec: marker in (rec.xml_content or ""))[:1]

    def _nfe_event_datetime(self):
        local = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        offset = local.strftime("%z") or "+0000"
        return f"{local.strftime('%Y-%m-%dT%H:%M:%S')}{offset[:3]}:{offset[3:]}"

    def _nfe_cancellation_event_xml(self):
        """Registered NF-e cancellation (``procEventoNFe``, ``tpEvento`` 110111).

        SEFAZ distributes this as a later NSU. The authorized proc stays as
        it was. The connector files the event and marks the inbox cancelled.
        """
        self.ensure_one()
        access_key = re.sub(r"\D", "", self.access_key or "")
        code = NFE_MOCK_CANCEL_EVENT_CODE
        when = self._nfe_event_datetime()
        ident = f"ID{code}{access_key}01"
        return (
            f'<procEventoNFe xmlns="{_NFE_EVENT_NS}" versao="1.00">'
            '<evento versao="1.00">'
            f'<infEvento Id="{ident}">'
            f"<cOrgao>{access_key[:2]}</cOrgao><tpAmb>2</tpAmb>"
            f"<CNPJ>{access_key[6:20]}</CNPJ>"
            f"<chNFe>{access_key}</chNFe>"
            f"<dhEvento>{when}</dhEvento>"
            f"<tpEvento>{code}</tpEvento>"
            "<nSeqEvento>1</nSeqEvento>"
            "<verEvento>1.00</verEvento>"
            '<detEvento versao="1.00">'
            "<descEvento>Cancelamento</descEvento>"
            "<nProt>135260000000001</nProt>"
            "<xJust>Cancellation registered by the supplier</xJust>"
            "</detEvento>"
            "</infEvento></evento>"
            '<retEvento versao="1.00"><infEvento>'
            "<tpAmb>2</tpAmb><verAplic>1.0</verAplic>"
            f"<cOrgao>{access_key[:2]}</cOrgao><cStat>135</cStat>"
            "<xMotivo>Evento registrado e vinculado a NF-e</xMotivo>"
            f"<chNFe>{access_key}</chNFe>"
            f"<tpEvento>{code}</tpEvento>"
            f"<dhRegEvento>{when}</dhRegEvento>"
            "<nProt>135260000000001</nProt>"
            "</infEvento></retEvento>"
            "</procEventoNFe>"
        )

    def action_register_nfe_cancellation(self):
        """Queue a supplier cancellation for the selected NF-e summaries or procs.

        Does not rewrite the note. The next NF-e distribution stores the
        event on the inbox document and leaves its situation authorized.
        """
        if self.filtered(
            lambda rec: rec.fiscal_type != "nfe"
            or rec.schema_type not in _NFE_NOTE_SCHEMAS
        ):
            raise UserError(
                self.env._(
                    "Select the NF-e summary or the complete NF-e. The "
                    "cancellation is a new event in the feed, not a change "
                    "of this row."
                )
            )
        created = self.browse()
        for company in self.company_id:
            current = self._next_mock_nsu(company, "nfe")
            notes = self.filtered(
                lambda rec, company=company: rec.company_id == company
            )
            seen = set()
            for note in notes:
                access_key = re.sub(r"\D", "", note.access_key or "")
                if access_key in seen:
                    continue
                seen.add(access_key)
                if note._nfe_cancellation_event():
                    continue
                if len(access_key) != 44:
                    raise UserError(
                        self.env._("This NF-e note has no access key to cancel.")
                    )
                created |= self.create(
                    {
                        "nsu": str(current).zfill(15),
                        "fiscal_type": "nfe",
                        "schema_type": "procEventoNFe",
                        "xml_content": note._nfe_cancellation_event_xml(),
                        "access_key": access_key,
                        "company_id": company.id,
                    }
                )
                current += 1
        if not created:
            raise UserError(
                self.env._(
                    "This NF-e already has a cancellation event in the mock pool."
                )
            )
        return self._cancellation_notification(
            self.env._("NF-e cancellation"),
            self.env._(
                "Queued %(count)s cancellation event(s). Run the NF-e "
                "distribution to store the event. The note stays authorized.",
                count=len(created),
            ),
        )

    def _cancellation_notification(self, title, message):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
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
