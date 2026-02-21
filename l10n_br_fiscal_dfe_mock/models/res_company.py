# Copyright 2026 Engenere (<https://engenere.one>)
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import gzip
from dataclasses import dataclass, field
from io import BytesIO

from odoo import fields, models

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


class ResCompany(models.Model):
    _inherit = "res.company"

    dfe_mock_mode = fields.Boolean(
        string="DF-e Mock Mode",
        help="When enabled, DF-e distribution queries are answered "
        "from the local mock NSU pool instead of SEFAZ.",
    )

    def action_toggle_dfe_mock_mode(self):
        self.ensure_one()
        new_state = not self.dfe_mock_mode
        self.sudo().write({"dfe_mock_mode": new_state})
        label = "ON" if new_state else "OFF"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": f"DF-e Mock Mode: {label}",
                "message": f"Mock mode is now {label} for {self.name}.",
                "type": "info",
                "sticky": False,
            },
        }

    def action_reset_dfe_cooldown(self):
        self.ensure_one()
        self.sudo().write({"dfe_next_query": False})

    def _dfe_consultar_distribuicao(self, **kwargs):
        self.ensure_one()
        if self.dfe_mock_mode:
            return self._dfe_mock_build_response(**kwargs)
        return super()._dfe_consultar_distribuicao(**kwargs)

    def _dfe_mock_build_response(self, **kwargs):
        MockNsu = self.env["dfe.mock.nsu"].sudo()
        ultimo_nsu = kwargs.get("ultimo_nsu", "000000000000000")
        chave = kwargs.get("chave")
        nsu_especifico = kwargs.get("nsu_especifico")

        domain = [("company_id", "=", self.id)]

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
                [("company_id", "=", self.id)],
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
            [("company_id", "=", self.id)],
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
