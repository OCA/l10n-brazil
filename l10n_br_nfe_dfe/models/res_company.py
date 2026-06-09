# Copyright (C) 2023 KMEE Informatica LTDA
# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
import re
from datetime import datetime, timezone

from lxml import objectify

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal_dfe.tools import utils

try:
    from nfelib.nfe.bindings.v4_0.proc_nfe_v4_00 import TnfeProc
    from nfelib.nfe.client.v4_0.dfe import DfeClient
except ImportError:
    DfeClient = None


class ResCompany(models.Model):
    _inherit = "res.company"

    nfe_last_nsu = fields.Char(string="NF-e Last NSU", size=25, default="0")
    nfe_max_nsu = fields.Char(string="NF-e Max NSU", readonly=True)
    nfe_dfe_next_query = fields.Datetime(string="NF-e Next Query")
    nfe_auto_fetch = fields.Boolean(default=False, string="Auto-fetch NF-e")
    auto_manifest_nfe = fields.Boolean(default=False, string="Auto Manifestation")
    nfe_dfe_last_query = fields.Datetime(string="NF-e Last Query")

    def _nfe_dfe_get_processor(self):
        self.ensure_one()
        cert = base64.b64decode(self.certificate.file)
        return DfeClient(
            ambiente=self.nfe_environment,
            uf=self.state_id.ibge_code,
            pkcs12_data=cert,
            pkcs12_password=self.certificate.password,
            wrap_response=True,
        )

    def _nfe_dfe_document_distribution(self):
        self.ensure_one()
        last_nsu = (
            self.nfe_last_nsu if self.nfe_last_nsu.isdigit() else "000000000000000"
        )
        processor = self._nfe_dfe_get_processor()

        while True:
            try:
                result = processor.consultar_distribuicao(
                    cnpj_cpf=re.sub("[^0-9]", "", self.vat),
                    ultimo_nsu=utils.format_nsu(last_nsu),
                )
            except Exception as exc:
                self._dfe_log(f"NF-e Search Error: {exc}", log_type="error")
                break

            resp = result.resposta
            if not self._dfe_validate_distribution_response(result):
                if resp.cStat == "656" and getattr(resp, "ultNSU", False):
                    last_nsu = resp.ultNSU
                break

            last_nsu = getattr(resp, "ultNSU", last_nsu)
            max_nsu = getattr(resp, "maxNSU", False)

            self._dfe_log(
                f"NF-e OK: {resp.cStat} - {resp.xMotivo}",
                log_type="success",
                result=result,
            )
            self._nfe_process_distribution(resp)

            if max_nsu and last_nsu >= max_nsu:
                self.nfe_max_nsu = max_nsu
                break

        self.nfe_last_nsu = last_nsu

    def _nfe_process_distribution(self, result):
        DfeRecord = self.env["l10n_br_fiscal_dfe.dfe"].sudo()
        for doc in result.loteDistDFeInt.docZip:
            payload = getattr(doc, "value", None) or getattr(doc, "valueOf_", None)
            if not payload:
                continue

            xml = utils.parse_gzip_xml(
                base64.b64encode(payload).decode()
                if isinstance(payload, bytes)
                else payload
            ).read()
            root = objectify.fromstring(xml)
            schema_type = (
                getattr(doc, "schema_value", "") or getattr(doc, "schema", "")
            ).split("_")[0]
            nsu = utils.format_nsu(getattr(doc, "NSU", False))

            if DfeRecord.search(
                [
                    ("nsu", "=", nsu),
                    ("company_id", "=", self.id),
                    ("fiscal_type", "=", "nfe"),
                ],
                limit=1,
            ):
                continue

            dfe_record = DfeRecord.create(
                {
                    "nsu": nsu,
                    "company_id": self.id,
                    "fiscal_type": "nfe",
                    "schema_type": schema_type,
                }
            )

            if schema_type == "procNFe":
                self._nfe_create_from_procNFe(root, dfe_record)
            elif schema_type == "resNFe":
                self._nfe_create_from_resNFe(root, dfe_record)

            dfe_record.create_xml_attachment(xml)

    def _nfe_get_or_create_document(self, access_key):
        Document = self.env["l10n_br_fiscal_dfe.document"].sudo()
        doc = Document.search(
            [("access_key", "=", access_key), ("company_id", "=", self.id)], limit=1
        )
        if not doc:
            doc = Document.create(
                {
                    "access_key": access_key,
                    "company_id": self.id,
                    "fiscal_type": "nfe",
                    "vat": utils.mask_cnpj(access_key[6:20]),
                    "serie": access_key[22:25].lstrip("0") or "0",
                    "document_number": access_key[25:34].lstrip("0") or "0",
                }
            )
        return doc

    def _nfe_create_from_procNFe(self, root, dfe_record):
        key = str(root.protNFe.infProt.chNFe)
        doc = self._nfe_get_or_create_document(key)
        dfe_record.write(
            {
                "access_key": key,
                "document_type_dfe": "complete",
                "dfe_document_id": doc.id,
            }
        )
        doc._update_metadata(
            {
                "emitter": str(root.NFe.infNFe.emit.xNome),
                "document_amount": float(root.NFe.infNFe.total.ICMSTot.vNF),
                "document_state": "1",
                "document_emission_date": datetime.fromisoformat(
                    str(root.NFe.infNFe.ide.dhEmi)
                )
                .astimezone(timezone.utc)
                .replace(tzinfo=None),
            },
            is_complete=True,
        )

    def _nfe_create_from_resNFe(self, root, dfe_record):
        key = str(root.chNFe)
        doc = self._nfe_get_or_create_document(key)
        dfe_record.write(
            {
                "access_key": key,
                "document_type_dfe": "summary",
                "dfe_document_id": doc.id,
            }
        )
        doc._update_metadata(
            {
                "emitter": str(root.xNome),
                "document_amount": float(root.vNF),
                "document_state": str(root.cSitNFe),
                "document_emission_date": datetime.fromisoformat(str(root.dhEmi))
                .astimezone(timezone.utc)
                .replace(tzinfo=None),
            }
        )
        if self.auto_manifest_nfe:
            mde = self.env["l10n_br_nfe.md_event"].create(
                {
                    "access_key": key,
                    "event_type": "ciente",
                    "company_id": self.id,
                    "document_type": "nfe",
                    "state": "draft",
                    "dfe_document_id": doc.id,
                }
            )
            mde.with_delay(
                channel="root.dfe",
                description=f"Auto-manifest ciência: {key}",
            ).action_confirm()

    @api.model
    def parse_procNFe(self, xml_stream):
        binding = TnfeProc.from_xml(xml_stream.read().decode())
        return self.env["l10n_br_fiscal.document"].import_binding_nfe(binding)

    def _nfe_dfe_search_specific_document(self, access_key=None, nsu=None):
        self.ensure_one()
        processor = self._nfe_dfe_get_processor()
        result = processor.consultar_distribuicao(
            chave=access_key,
            nsu_especifico=utils.format_nsu(nsu) if nsu else None,
            cnpj_cpf=re.sub("[^0-9]", "", self.vat),
        )
        if not self._dfe_validate_distribution_response(result, raise_message=True):
            return

        self._dfe_log(
            f"NF-e Specific OK: {result.resposta.cStat}",
            log_type="success",
            result=result,
        )
        self._nfe_process_distribution(result.resposta)

    @api.model
    def _cron_nfe_dfe_search_documents(self):
        companies = self.search([("nfe_auto_fetch", "=", True)])
        for company in companies:
            # Add delay logic here if needed or run synchronously
            company._nfe_dfe_document_distribution()
