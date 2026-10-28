# Copyright 2026 Engenere (<https://engenere.one>)
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import gzip
from dataclasses import dataclass, field
from io import BytesIO

from odoo import api, fields, models
from odoo.exceptions import AccessError

from odoo.addons.l10n_br_nfse_dfe.constants.nfse_dfe import (
    NFSE_LOTE_SIZE,
    NFSE_SEFIN_NFSE_PATH,
)
from odoo.addons.l10n_br_nfse_dfe.services.sefin_nfse import NfseHttpResponse

# ── Mock dataclasses imitating nfelib WrappedResponse ──────────────────


@dataclass
class MockDocZip:
    NSU: str
    schema_value: str
    schema: str
    value: bytes  # gzipped XML as raw bytes


@dataclass
class MockLoteDistDFeInt:
    docZip: list = field(default_factory=list)


@dataclass
class MockResposta:
    cStat: str
    xMotivo: str
    ultNSU: str
    maxNSU: str
    loteDistDFeInt: MockLoteDistDFeInt = field(default_factory=MockLoteDistDFeInt)


@dataclass
class MockRetorno:
    content: bytes = b""
    _content: bytes = b""


@dataclass
class MockWrappedResponse:
    resposta: MockResposta = None
    envio_xml: bytes = b"<mock/>"
    retorno: MockRetorno = field(default_factory=MockRetorno)


class MockDfeClient:
    """Stand-in for the SEFAZ SOAP client returned by ``_dfe_get_processor``.

    Exposes the same ``consultar_distribuicao(**kwargs)`` entry point the
    generic DF-e engine calls, answering from the local mock NSU pool
    instead of reaching the SEFAZ web service.
    """

    def __init__(self, company):
        self.company = company

    def consultar_distribuicao(self, **kwargs):
        return self.company._dfe_mock_build_response(**kwargs)


class ResCompany(models.Model):
    _inherit = "res.company"

    dfe_mock_mode = fields.Boolean(
        string="DF-e Mock Mode",
        help="When enabled, DF-e distribution queries are answered "
        "from the local mock NSU pool instead of SEFAZ.",
    )

    @api.model
    def _dfe_mock_check_manager(self):
        # The buttons are hidden by groups in the view, but the methods are
        # still reachable through RPC.
        if not self.env.is_superuser() and not self.env.user.has_group(
            "l10n_br_fiscal.group_manager"
        ):
            raise AccessError(
                self.env._("Only fiscal managers can change the DF-e mock settings.")
            )

    @api.model
    def action_toggle_dfe_mock_mode(self):
        self._dfe_mock_check_manager()
        company = self.env.company
        new_state = not company.dfe_mock_mode
        company.sudo().write({"dfe_mock_mode": new_state})
        label = "ON" if new_state else "OFF"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": f"DF-e Mock Mode: {label}",
                "message": f"Mock mode is now {label} for {company.name}.",
                "type": "info",
                "sticky": False,
            },
        }

    @api.model
    def dfe_get_banner_data(self, fiscal_type):
        """Add the mock state consumed by the banner template extension.

        NF-e and NFS-e are mocked, and only fiscal managers may flip the
        switch, so the controls stay hidden for anyone else.
        """
        data = super().dfe_get_banner_data(fiscal_type)
        data["mock_available"] = fiscal_type in (
            "nfe",
            "nfse",
        ) and self.env.user.has_group("l10n_br_fiscal.group_manager")
        data["mock_mode"] = bool(self.env.company.dfe_mock_mode)
        return data

    def _dfe_get_processor(self, fiscal_type):
        self.ensure_one()
        if self.dfe_mock_mode and fiscal_type == "nfe":
            return MockDfeClient(self)
        return super()._dfe_get_processor(fiscal_type)

    def action_document_distribution(self, fiscal_type):
        self.ensure_one()
        if self.dfe_mock_mode and fiscal_type in ("nfe", "nfse"):
            self._dfe_write_typed(fiscal_type, {"dfe_next_query": False})
        return super().action_document_distribution(fiscal_type)

    def _dfe_mock_build_response(self, **kwargs):
        MockNsu = self.env["dfe.mock.nsu"].sudo()
        ultimo_nsu = kwargs.get("ultimo_nsu", "000000000000000")
        chave = kwargs.get("chave")
        nsu_especifico = kwargs.get("nsu_especifico")

        domain = [("company_id", "=", self.id), ("fiscal_type", "=", "nfe")]

        if nsu_especifico:
            domain.append(("nsu", "=", nsu_especifico))
        elif chave:
            domain.append(("access_key", "=", chave))
        else:
            domain += [
                ("nsu", ">", ultimo_nsu),
                ("consumed", "=", False),
            ]

        records = MockNsu.search(domain, order="nsu asc", limit=50)

        if not records:
            max_nsu_rec = MockNsu.search(
                [("company_id", "=", self.id), ("fiscal_type", "=", "nfe")],
                order="nsu desc",
                limit=1,
            )
            max_nsu = max_nsu_rec.nsu if max_nsu_rec else ultimo_nsu
            return MockWrappedResponse(
                resposta=MockResposta(
                    cStat="137",
                    xMotivo="Nenhum documento localizado para o Contribuinte",
                    ultNSU=ultimo_nsu,
                    maxNSU=max_nsu,
                ),
            )

        doc_zips = []
        for rec in records:
            buf = BytesIO()
            with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
                gz.write(rec.xml_content.encode("utf-8"))
            gzipped = buf.getvalue()

            schema_map = {
                "resNFe": "resNFe_v1.00.xsd",
                "procNFe": "procNFe_v4.00.xsd",
                "resEvento": "resEvento_v1.00.xsd",
                "procEventoNFe": "procEventoNFe_v1.00.xsd",
            }
            doc_zips.append(
                MockDocZip(
                    NSU=rec.nsu,
                    schema_value=schema_map.get(rec.schema_type, rec.schema_type),
                    schema=schema_map.get(rec.schema_type, rec.schema_type),
                    value=gzipped,
                )
            )

        # Mark consumed only for pagination queries (not specific searches)
        if not chave and not nsu_especifico:
            records.write({"consumed": True})

        max_nsu_rec = MockNsu.search(
            [("company_id", "=", self.id), ("fiscal_type", "=", "nfe")],
            order="nsu desc",
            limit=1,
        )
        ult_nsu = records[-1].nsu
        max_nsu = max_nsu_rec.nsu if max_nsu_rec else ult_nsu

        retorno_xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>' b"<mock>cStat=138</mock>"
        )
        return MockWrappedResponse(
            resposta=MockResposta(
                cStat="138",
                xMotivo="Documento(s) localizado(s)",
                ultNSU=ult_nsu,
                maxNSU=max_nsu,
                loteDistDFeInt=MockLoteDistDFeInt(docZip=doc_zips),
            ),
            envio_xml=b"<mock>consulta mock</mock>",
            retorno=MockRetorno(
                content=retorno_xml,
                _content=retorno_xml,
            ),
        )

    # ── NFS-e (national ADN) ───────────────────────────────────────────

    def _nfse_consulta_dfe(self, nsu):
        """Answer the ADN distribution from the local pool in mock mode.

        The ADN is a cursor, not a queue: the batch holds the rows above the
        NSU asked for, and ``consumed`` does not filter it, so the specific
        search by NSU, which replays an earlier batch, also works offline.
        """
        self.ensure_one()
        if not self.dfe_mock_mode:
            return super()._nfse_consulta_dfe(nsu)
        records = (
            self.env["dfe.mock.nsu"]
            .sudo()
            .search(
                [
                    ("company_id", "=", self.id),
                    ("fiscal_type", "=", "nfse"),
                    ("nsu", ">", str(int(nsu or 0)).zfill(15)),
                ],
                order="nsu asc",
                limit=NFSE_LOTE_SIZE,
            )
        )
        if not records:
            # The ADN answers 404 once the caller caught up with the feed.
            return NfseHttpResponse(status_code=404, body={}, headers={}, text="")
        records.write({"consumed": True})
        return NfseHttpResponse(
            status_code=200,
            body={"LoteDFe": [record._nfse_mock_lote_item() for record in records]},
            headers={},
            text="",
        )

    def _nfse_mock_row_by_access_key(self, access_key):
        return (
            self.env["dfe.mock.nsu"]
            .sudo()
            .search(
                [
                    ("company_id", "=", self.id),
                    ("fiscal_type", "=", "nfse"),
                    ("access_key", "=", access_key),
                ],
                limit=1,
            )
        )

    def _nfse_sefin_request(self, path):
        """Serve ``GET /nfse/{chave}`` from the local pool in mock mode.

        The search by access key does not go through the ADN cursor, it reads
        the note from Sefin Nacional over mTLS, so without this the mock would
        still ask for an e-CNPJ certificate and, with one configured, query a
        made-up key against the real service.
        """
        self.ensure_one()
        prefix = f"{NFSE_SEFIN_NFSE_PATH}/"
        if not self.dfe_mock_mode or not path.startswith(prefix):
            return super()._nfse_sefin_request(path)
        access_key = path[len(prefix) :].split("?")[0]
        record = self._nfse_mock_row_by_access_key(access_key)
        if not record:
            return NfseHttpResponse(status_code=404, body={}, headers={}, text="")
        # The key search replays one note, it does not move the feed, so the
        # row is left unconsumed for the distribution.
        item = record._nfse_mock_lote_item()
        return NfseHttpResponse(
            status_code=200,
            body={
                "chaveAcesso": record.access_key,
                "nfseXmlGZipB64": item["ArquivoXml"],
            },
            headers={},
            text="",
        )

    def _nfse_consulta_eventos(self, chave):
        """Answer the event list offline: the mock pool holds no NFS-e event."""
        self.ensure_one()
        if not self.dfe_mock_mode:
            return super()._nfse_consulta_eventos(chave)
        return NfseHttpResponse(status_code=404, body={}, headers={}, text="")
