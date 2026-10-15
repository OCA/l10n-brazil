# Copyright 2026 Engenere (<https://engenere.one>)
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import logging
import random
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from lxml import etree

from odoo import fields, models

from ..wizards.dfe_mock_generate_wizard import format_nfe_datetime

_logger = logging.getLogger(__name__)


# ── Mock dataclasses imitating nfelib MDE response ──────────────────────


@dataclass
class _MockInfEvento:
    cStat: str = "135"
    xMotivo: str = "Evento registrado e vinculado a NF-e"
    nProt: str = ""
    dhRegEvento: str = ""


@dataclass
class _MockRetEvento:
    infEvento: _MockInfEvento = field(default_factory=_MockInfEvento)


@dataclass
class _MockResposta:
    retEvento: list = field(default_factory=list)


@dataclass
class _MockRetorno:
    status_code: int = 200
    _content: bytes = b"<mock>MDE mock response</mock>"


@dataclass
class _MockMDeResult:
    retorno: _MockRetorno = field(default_factory=_MockRetorno)
    resposta: _MockResposta = field(default_factory=_MockResposta)


def _build_mde_result(record):
    """Build a successful mock MDE result."""
    now_iso = format_nfe_datetime(record, fields.Datetime.now())
    nprot = f"MOCK{random.randint(100000000000, 999999999999)}"
    inf = _MockInfEvento(
        cStat="135",
        xMotivo="Evento registrado e vinculado a NF-e",
        nProt=nprot,
        dhRegEvento=now_iso,
    )
    return _MockMDeResult(
        retorno=_MockRetorno(),
        resposta=_MockResposta(retEvento=[_MockRetEvento(infEvento=inf)]),
    )


class _MockMDeProcessor:
    """Emulates the MDeAdapter for all four manifestation operations.

    Holds the manifestation record so the mock timestamps follow the user
    timezone, like the ones the generator wizard writes.
    """

    def __init__(self, record):
        self.record = record

    def ciencia_da_operacao(self, chave, cnpj_dest):
        return _build_mde_result(self.record)

    def confirmacao_da_operacao(self, chave, cnpj_dest):
        return _build_mde_result(self.record)

    def desconhecimento_da_operacao(self, chave, cnpj_dest):
        return _build_mde_result(self.record)

    def operacao_nao_realizada(self, chave, cnpj_dest):
        return _build_mde_result(self.record)


# ── Odoo model override ────────────────────────────────────────────────


class NfeRecipientManifestationEvent(models.Model):
    _inherit = "l10n_br_nfe.md_event"

    def _get_processor(self):
        if self.company_id.dfe_mock_mode:
            _logger.info("MDE mock: using _MockMDeProcessor for %s", self.access_key)
            return _MockMDeProcessor(self)
        return super()._get_processor()

    def action_confirm(self):
        result = super().action_confirm()
        for record in self.filtered(
            lambda r: r.company_id.dfe_mock_mode and r.event_type == "ciente"
        ):
            record._mock_generate_proc_nfe()
        return result

    def _mock_generate_proc_nfe(self):
        """After ciência, auto-generate a procNFe in the mock pool."""
        MockNsu = self.env["dfe.mock.nsu"].sudo()
        access_key = self.access_key

        existing = MockNsu.search(
            [
                ("company_id", "=", self.company_id.id),
                ("access_key", "=", access_key),
                ("schema_type", "=", "procNFe"),
            ],
            limit=1,
        )
        if existing:
            _logger.info(
                "MDE mock: procNFe already exists for key %s (NSU %s)",
                access_key,
                existing.nsu,
            )
            return

        res_nfe = MockNsu.search(
            [
                ("company_id", "=", self.company_id.id),
                ("access_key", "=", access_key),
                ("schema_type", "=", "resNFe"),
            ],
            limit=1,
        )
        if not res_nfe:
            _logger.warning(
                "MDE mock: no resNFe found for key %s, cannot generate procNFe",
                access_key,
            )
            return

        partner_data, amount, emission_dt = self._mock_parse_res_nfe(
            res_nfe.xml_content
        )

        wizard = self.env["dfe.mock.generate.wizard"].new(
            {"company_id": self.company_id.id}
        )
        proc_xml = wizard._build_proc_nfe_xml(
            access_key, partner_data, amount, emission_dt
        )

        next_nsu = wizard._next_nsu(self.company_id)
        nsu_str = str(next_nsu).zfill(15)

        MockNsu.create(
            {
                "nsu": nsu_str,
                "schema_type": "procNFe",
                "xml_content": proc_xml,
                "access_key": access_key,
                "company_id": self.company_id.id,
                "consumed": False,
            }
        )
        _logger.info("MDE mock: created procNFe NSU %s for key %s", nsu_str, access_key)

    @staticmethod
    def _mock_parse_datetime(value):
        """Parse a NF-e timestamp into the naive UTC datetime Odoo stores.

        Values without an offset are already naive UTC, which is what the
        pool holds for documents this module generated.
        """
        if not value:
            return fields.Datetime.now()
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)

    def _mock_parse_res_nfe(self, xml_content):
        """Extract partner data, amount, and emission date from resNFe XML."""
        root = etree.fromstring(xml_content.encode("utf-8"))
        ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

        def _text(tag, default=""):
            el = root.find(f"nfe:{tag}", ns)
            if el is None:
                el = root.find(tag)
            return el.text if el is not None and el.text else default

        cnpj = _text("CNPJ")
        name = _text("xNome", "Emitente Mock")
        ie = _text("IE", "ISENTO")
        vnf = float(_text("vNF", "1000.00"))

        emission_dt = self._mock_parse_datetime(_text("dhEmi"))

        cnpj_digits = re.sub(r"[^0-9]", "", cnpj)
        uf_code = cnpj_digits[:2] if len(cnpj_digits) >= 2 else "35"
        # UF code from access key is more reliable
        if self.access_key and len(self.access_key) >= 2:
            uf_code = self.access_key[:2]

        partner_data = {
            "cnpj": cnpj_digits,
            "name": name,
            "uf_code": uf_code,
            "ie": ie,
        }
        return partner_data, vnf, emission_dt
