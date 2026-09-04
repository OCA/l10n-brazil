# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import gzip
import logging
import os
import re
import shutil
import tempfile
import time
from contextlib import contextmanager

import requests
from lxml import etree

from odoo import _, api, fields, models

from ..constants.nfse import NFSE_NAC_BASE_URLS, NFSE_NAC_DFE_PATH

_logger = logging.getLogger(__name__)


class NfseDfe(models.Model):
    """NFS-e Nacional Received Documents Fetch Engine.

    Queries the SEFAZ ADN REST API (post-2024 national NFS-e) as
    contribuinte/tomador. Authentication is performed via the company's
    e-CNPJ certificate (mTLS).
    Base URLs: https://adn.nfse.gov.br (prod) /
    https://adn.producaorestrita.nfse.gov.br (test).
    """

    _name = "l10n_br_nfse.dfe"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "NFS-e Nacional Fetch Engine"
    _order = "company_id, id"

    name = fields.Char(string="Name", required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    nfse_nac_environment = fields.Selection(
        selection=[
            ("producao", "Production"),
            ("producao_restrita", "Test / Restricted Production"),
        ],
        string="ADN Environment",
        required=True,
        default="producao_restrita",
        tracking=True,
        help="Which SEFAZ ADN environment to query:\n"
        "Production → https://adn.nfse.gov.br\n"
        "Test → https://adn.producaorestrita.nfse.gov.br",
    )
    last_nsu = fields.Char(
        string="Last NSU",
        readonly=True,
        tracking=True,
        help="Last NSU (Número Sequencial Único) seen from the SEFAZ ADN. "
        "Updated automatically during sync; informational only.",
    )
    last_query = fields.Datetime(string="Last Query", readonly=True)
    use_cron = fields.Boolean(
        string="Sync Automatically",
        default=False,
        help="Enable to have the daily cron job fetch received NFS-e.",
    )
    fetch_from_year = fields.Integer(
        string="Fetch From Year",
        default=lambda self: fields.Date.today().year,
        help="Only import NFS-e issued from January 1st of this year onwards. "
        "Set 0 to disable the filter.",
    )
    fetch_limit = fields.Integer(
        string="Max Records per Sync",
        default=0,
        help="Maximum number of NFS-e to import per sync run. 0 = no limit.",
    )
    active = fields.Boolean(default=True)
    received_ids = fields.One2many(
        comodel_name="l10n_br_nfse.received",
        inverse_name="dfe_id",
        string="Received NFS-e",
    )

    def search_received_nfse(self):
        """Query the SEFAZ ADN and create pending received records."""
        for dfe in self:
            try:
                data_list = dfe._query_nfse_nacional_tomado()
                dfe._create_received_records(data_list)
                dfe.last_query = fields.Datetime.now()
                dfe.message_post(
                    body=_("Sync completed: %d NFS-e retrieved.") % len(data_list)
                )
            except Exception as exc:
                _logger.exception("NFS-e DFe sync failed for %s", dfe.name)
                dfe.message_post(body=_("Sync error: %s") % str(exc))

    def action_discover_nfse_nac_paths(self):
        """Probe SEFAZ ADN Redoc pages to find OpenAPI spec and API paths."""
        self.ensure_one()
        base_url = NFSE_NAC_BASE_URLS.get(
            self.nfse_nac_environment,
            NFSE_NAC_BASE_URLS["producao_restrita"],
        )
        lines = ["<b>ADN path discovery — %s</b><br/>" % base_url]
        doc_pages = [
            ("/cnc/consulta/docs/index.html", "/cnc/consulta/docs/index.js"),
            ("/contribuintes/docs/index.html", "/contribuintes/docs/index.js"),
            ("/cnc/docs/index.html", "/cnc/docs/index.js"),
        ]

        try:
            with self._nfse_nac_session() as session:
                for html_path, js_path in doc_pages:
                    self._process_doc_page(session, base_url, html_path, js_path, lines)
        except Exception as exc:
            lines.append("<br/>Session error: %s" % str(exc))

        self.message_post(body="".join(lines))

    def _process_doc_page(self, session, base_url, html_path, js_path, lines):
        lines.append("<br/><b>%s</b><br/>" % html_path)
        try:
            js_resp = session.get(base_url + js_path, timeout=15)
            if js_resp.status_code != 200:
                lines.append(
                    "❌ <code>%s</code> → HTTP %s<br/>" % (js_path, js_resp.status_code)
                )
                return

            js_text = js_resp.text
            _logger.info(
                "ADN index.js [%s] (first 3000 chars):\n%s",
                js_path,
                js_text[:3000],
            )

            spec_url = self._find_spec_url(js_text)
            if not spec_url:
                clean_text = js_text[:500].replace("<", "&lt;").replace(">", "&gt;")
                lines.append(
                    "⚠️ No spec URL found in <code>%s</code>. "
                    "First 500 chars logged.<br/>"
                    "<small><pre>%s</pre></small><br/>" % (js_path, clean_text)
                )
                return

            lines.append("✅ Spec URL: <code>%s</code><br/>" % spec_url)
            spec_full = spec_url if spec_url.startswith("http") else base_url + spec_url
            self._fetch_and_parse_spec(session, spec_full, lines)
        except Exception as exc:
            lines.append("? Error: %s<br/>" % str(exc)[:100])

    def _find_spec_url(self, js_text):
        patterns = [
            r"Redoc\.init\(['\"]([^'\"]+)['\"]",
            r'specUrl\s*[=:]\s*["\']([^"\']+)["\']',
            r'spec-url=["\']([^"\']+)["\']',
            r'["\']([^"\']*(?:api-docs|openapi|swagger)[^"\']*)["\']',
            r'["\']([^"\']*/v\d+/[^"\']*)["\']',
        ]
        for pattern in patterns:
            m = re.search(pattern, js_text)
            if m:
                return m.group(1)
        return None

    def _fetch_and_parse_spec(self, session, spec_full, lines):
        try:
            spec_resp = session.get(spec_full, timeout=20)
            if spec_resp.status_code != 200:
                lines.append(
                    "&nbsp;&nbsp;Spec fetch → HTTP %s<br/>" % spec_resp.status_code
                )
                return

            spec = spec_resp.json()
            paths_obj = spec.get("paths") or {}
            api_paths = sorted(paths_obj.keys())
            lines.append(
                "&nbsp;&nbsp;Paths (%d):<br/>%s"
                % (
                    len(api_paths),
                    "".join("&nbsp;&nbsp;<code>%s</code><br/>" % p for p in api_paths),
                )
            )
            for api_path, methods in paths_obj.items():
                for method, op in methods.items():
                    self._parse_spec_operation(api_path, method, op, spec, lines)
        except Exception as exc:
            lines.append("&nbsp;&nbsp;Spec fetch error: %s<br/>" % str(exc)[:120])

    def _parse_spec_operation(self, api_path, method, op, spec, lines):
        params = op.get("parameters") or []
        lines.append(
            "&nbsp;&nbsp;<b>%s %s</b> — %s<br/>"
            % (method.upper(), api_path, op.get("summary", ""))
        )
        for p in params:
            schema = p.get("schema") or {}
            lines.append(
                "&nbsp;&nbsp;&nbsp;&nbsp;param <code>%s</code>"
                " in=%s type=%s required=%s<br/>"
                % (
                    p.get("name", "?"),
                    p.get("in", "?"),
                    schema.get("type", "?"),
                    p.get("required", False),
                )
            )
        resp200 = (op.get("responses") or {}).get("200", {})
        schema_ref = (
            resp200.get("content", {}).get("application/json", {}).get("schema", {})
        )
        if schema_ref:
            ref = schema_ref.get("$ref", "")
            schema_name = ref.split("/")[-1] if ref else ""
            lines.append(
                "&nbsp;&nbsp;&nbsp;&nbsp;200 schema: "
                "<code>%s</code><br/>" % (schema_name or str(schema_ref)[:200])
            )
            if schema_name:
                comp = (
                    (spec.get("components") or {})
                    .get("schemas", {})
                    .get(schema_name, {})
                )
                props = comp.get("properties") or {}
                if props:
                    lines.append("&nbsp;&nbsp;&nbsp;&nbsp;properties:<br/>")
                    for prop_name, prop_schema in props.items():
                        self._parse_spec_property(prop_name, prop_schema, spec, lines)

    def _parse_spec_property(self, prop_name, prop_schema, spec, lines):
        prop_type = prop_schema.get("type", "")
        prop_ref = prop_schema.get("$ref", "")
        items_ref = (
            prop_schema.get("items", {}).get("$ref", "") if prop_type == "array" else ""
        )

        display_type = "?"
        if items_ref:
            display_type = items_ref.split("/")[-1]
        elif prop_ref:
            display_type = prop_ref.split("/")[-1]
        elif prop_type:
            display_type = prop_type

        lines.append(
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "<code>%s</code>: %s<br/>" % (prop_name, display_type)
        )
        if items_ref:
            item_name = items_ref.split("/")[-1]
            item_comp = (
                (spec.get("components") or {}).get("schemas", {}).get(item_name, {})
            )
            for ip, is_ in (item_comp.get("properties") or {}).items():
                is_type = is_.get("type", is_.get("$ref", "?")).split("/")[-1]
                lines.append(
                    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                    "<code>%s</code>: %s<br/>" % (ip, is_type)
                )

    def _query_nfse_nacional_tomado(self):
        """Query SEFAZ ADN REST API for received documents."""
        self.ensure_one()
        cnpj = self._company_cnpj_digits()
        base_url = NFSE_NAC_BASE_URLS.get(
            self.nfse_nac_environment,
            NFSE_NAC_BASE_URLS["producao_restrita"],
        )
        nsu = 0

        all_data = []
        with self._nfse_nac_session() as session:
            while True:
                url = "%s%s/%d" % (base_url, NFSE_NAC_DFE_PATH, nsu)
                params = {"lote": "true"}
                if cnpj:
                    params["cnpjConsulta"] = cnpj

                resp = self._get_with_retry(session, url, params=params)

                if resp.status_code == 404:
                    break

                if not resp.ok:
                    try:
                        body = resp.json()
                        detail = (
                            body.get("mensagem")
                            or body.get("message")
                            or body.get("detail")
                            or str(body)
                        )
                    except Exception:
                        detail = resp.text[:500]
                    raise requests.exceptions.HTTPError(
                        "%s %s — %s" % (resp.status_code, resp.reason, detail),
                        response=resp,
                    )

                payload = resp.json()
                _logger.debug(
                    "NFS-e Nacional DFe from NSU %d: keys=%s",
                    nsu,
                    list(payload.keys())
                    if isinstance(payload, dict)
                    else type(payload).__name__,
                )

                if isinstance(payload, list):
                    items = payload
                else:
                    erros = payload.get("Erros") or []
                    if erros:
                        msgs = [
                            "%s: %s" % (e.get("Codigo", ""), e.get("Descricao", str(e)))
                            for e in erros
                        ]
                        raise ValueError("SEFAZ ADN error: %s" % "; ".join(msgs))
                    items = payload.get("LoteDFe") or []

                for item in items:
                    data = self._extract_nfse_nacional(item)
                    if data:
                        all_data.append(data)

                if items and len(items) >= 50:
                    last_item = items[-1]
                    last_item_nsu = (
                        last_item.get("NSU") if isinstance(last_item, dict) else None
                    )
                    if last_item_nsu is not None and int(last_item_nsu) != nsu:
                        nsu = int(last_item_nsu)
                        self.last_nsu = str(nsu)
                        time.sleep(1)
                        continue

                if items:
                    last_item = items[-1]
                    last_item_nsu = (
                        last_item.get("NSU") if isinstance(last_item, dict) else None
                    )
                    if last_item_nsu is not None:
                        self.last_nsu = str(last_item_nsu)
                break

        if self.fetch_from_year:
            all_data = [
                d
                for d in all_data
                if self._emission_year(d.get("emission_date")) >= self.fetch_from_year
            ]
        if self.fetch_limit:
            all_data = all_data[: self.fetch_limit]

        return all_data

    @staticmethod
    def _emission_year(emission_date):
        """Return year from emission_date string or 0."""
        if not emission_date:
            return 0
        try:
            return int(str(emission_date)[:4])
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _get_with_retry(session, url, params=None, max_retries=3, timeout=30):
        """GET with automatic retry on 429, honoring Retry-After."""
        for attempt in range(max_retries + 1):
            resp = session.get(url, params=params, timeout=timeout)
            if resp.status_code != 429:
                return resp
            fallback_delay = min(2**attempt * 5, 60)
            retry_after = int(resp.headers.get("Retry-After", fallback_delay))
            _logger.warning(
                "Rate limited (429) on %s — waiting %ds (attempt %d/%d)",
                url,
                retry_after,
                attempt + 1,
                max_retries,
            )
            time.sleep(retry_after)
        return resp

    @contextmanager
    def _nfse_nac_session(self):
        """Yield requests.Session configured with mTLS from e-CNPJ."""
        try:
            cert_obj = self.company_id._get_br_ecertificate(only_ecnpj=True)
        except Exception as exc:
            raise ValueError(
                _(
                    "Could not load e-CNPJ certificate for "
                    "company '%s': %s. Configure the "
                    "certificate under Company → e-CNPJ."
                )
                % (self.company_id.name, exc)
            ) from exc

        cert_pem_str, key_pem_str = cert_obj.cert_chave()
        tmpdir = tempfile.mkdtemp(prefix="nfse_nac_")
        cert_path = os.path.join(tmpdir, "cert.pem")
        key_path = os.path.join(tmpdir, "key.pem")
        try:
            with open(cert_path, "w") as f:
                f.write(cert_pem_str)
            with open(key_path, "w") as f:
                f.write(key_pem_str)
            session = requests.Session()
            session.cert = (cert_path, key_path)
            session.verify = False
            session.headers["Accept"] = "application/json"
            yield session
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    @staticmethod
    def _decode_xml(xml_b64, nsu):
        """Decode a base64-encoded, possibly gzip-compressed XML payload."""
        if not xml_b64:
            return None, None
        try:
            raw = base64.b64decode(xml_b64)
            try:
                xml_bytes = gzip.decompress(raw)
            except (OSError, gzip.BadGzipFile):
                xml_bytes = raw
            return xml_bytes, xml_bytes.decode("utf-8", errors="replace")
        except Exception as exc:
            _logger.warning("Could not decode ArquivoXml for NSU %s: %s", nsu, exc)
            return None, xml_b64

    @staticmethod
    def _extract_nfse_nacional(item):
        """Map a DistribuicaoNSU item to a data dict."""
        if not isinstance(item, dict):
            return None

        nsu = item.get("NSU")
        chave = item.get("ChaveAcesso") or ""
        tipo_doc = item.get("TipoDocumento")
        tipo_evento = item.get("TipoEvento")
        xml_b64 = item.get("ArquivoXml") or ""
        data_hora = item.get("DataHoraGeracao") or ""

        if not nsu and not chave:
            return None

        _logger.debug(
            "NFS-e Nacional DFe NSU=%s ChaveAcesso=%s "
            "TipoDocumento=%s TipoEvento=%s",
            nsu,
            chave,
            tipo_doc,
            tipo_evento,
        )

        xml_bytes, xml_str = NfseDfe._decode_xml(xml_b64, nsu)

        res = {
            "nfse_number": None,
            "verify_code": None,
            "provider_cnpj": None,
            "provider_name": None,
            "service_value": 0.0,
            "service_description": None,
            "emission_date": (data_hora[:19].replace("T", " ") if data_hora else False),
            "issqn_base": 0.0,
            "issqn_percent": 0.0,
            "issqn_value": 0.0,
            "issqn_wh_percent": 0.0,
            "issqn_wh_value": 0.0,
            "service_lc116_code": None,
            "service_nbs_code": None,
            "issqn_city_ibge": None,
            "document_serie": None,
            "rps_number": None,
            "civil_construction_code": None,
            "civil_construction_art": None,
            "fiscal_additional_data": None,
            "xml_content": xml_str,
        }

        if xml_bytes:
            NfseDfe._parse_xml_bytes(xml_bytes, nsu, res)

        res["verify_code"] = chave or res.get("verify_code") or str(nsu)
        if not res["nfse_number"]:
            res["nfse_number"] = str(nsu) if nsu else res["verify_code"]

        return res

    @staticmethod
    def _find_xpath(root, *xpaths):
        """Helper to find the first matching non-empty text node across XPaths."""
        for xp in xpaths:
            el = root.find(xp)
            if el is not None and el.text:
                return el.text.strip()
        return None

    @staticmethod
    def _extract_basic_info(root, res):
        """Extract basic core transaction attributes from the XML root."""
        t = NfseDfe._find_xpath
        res["nfse_number"] = t(root, ".//nNFSe", ".//Numero", ".//NumNFSe", ".//NNfse")
        raw_cnpj = t(
            root,
            ".//emit/CNPJ",
            ".//Emitente/CNPJ",
            ".//Prestador/CNPJ",
            ".//PrestadorServico//CNPJ",
            ".//CNPJ",
        )
        if raw_cnpj:
            res["provider_cnpj"] = "".join(c for c in raw_cnpj if c.isdigit())

        res["provider_name"] = t(
            root,
            ".//emit/xNome",
            ".//Emitente/xNome",
            ".//Prestador/xNome",
            ".//PrestadorServico/RazaoSocial",
            ".//RazaoSocial",
            ".//xNome",
        )
        val_text = t(
            root,
            ".//vServPrest/vServ",
            ".//vServPrest/vReceb",
            ".//vBC",
            ".//vNFSe",
            ".//vServicos",
            ".//ValorServicos",
            ".//ValorTotal",
            ".//vLiq",
        )
        if val_text:
            res["service_value"] = float(val_text)

        res["service_description"] = t(
            root,
            ".//cServ/xDescServ",
            ".//xDescServ",
            ".//xDiscriminacao",
            ".//Discriminacao",
            ".//DescricaoServico",
        )
        dt_text = t(root, ".//dhEmi", ".//DataEmissao")
        if dt_text:
            res["emission_date"] = dt_text[:19].replace("T", " ")

    @staticmethod
    def _extract_issqn_values(root, res):
        """Extract ISSQN tax bases, rates, and withholdings from the XML root."""
        t = NfseDfe._find_xpath
        vbc = t(root, ".//valores/vBC", ".//vBC")
        paliq = t(root, ".//pAliqAplic", ".//Aliquota", ".//aliquota")
        vissqn = t(root, ".//vISSQN", ".//ValorIss", ".//valorIss")
        vwh = t(root, ".//ValorIssRetido", ".//valorIssRetido")
        tp_ret = t(root, ".//tpRetISSQN", ".//IssRetido")

        if vbc:
            res["issqn_base"] = float(vbc)
        if vissqn:
            res["issqn_value"] = float(vissqn)
        if paliq:
            res["issqn_percent"] = float(paliq)
            if tp_ret == "1":
                res["issqn_wh_percent"] = res["issqn_percent"]
        if vwh:
            res["issqn_wh_value"] = float(vwh)
        elif tp_ret == "1" and res.get("issqn_value"):
            res["issqn_wh_value"] = res["issqn_value"]

    @staticmethod
    def _extract_codes_and_refs(root, res):
        """Extract legal codes, operations, and complementary descriptive info."""
        t = NfseDfe._find_xpath
        lc116 = t(root, ".//cTribNac", ".//cServLC116", ".//ItemListaServico")
        nbs = t(root, ".//cNBS", ".//CodigoNbs")
        ibge = t(root, ".//cLocIncid", ".//cLocPrestacao", ".//CodigoMunicipio")
        serie = t(root, ".//serie", ".//Serie")
        ndps = t(root, ".//nDPS", ".//NumeroRps", ".//Numero")
        xnome_trib = t(root, ".//xTribNac", ".//xServicos")
        cobr = t(root, ".//cObra", ".//CodigoObra")
        art = t(root, ".//art", ".//Art", ".//ArtObra")
        inf_compl = t(root, ".//xInfComp", ".//InformacoesComplementares")

        inf_nfse_el = root.find(".//infNFSe") or root.find(".//InfNfse")
        if inf_nfse_el is not None:
            res["verify_code"] = inf_nfse_el.get("Id") or ""

        if lc116:
            res["service_lc116_code"] = lc116.strip()
        if nbs:
            res["service_nbs_code"] = "".join(c for c in nbs if c.isdigit())
        if ibge:
            res["issqn_city_ibge"] = "".join(c for c in ibge if c.isdigit())
        if serie:
            res["document_serie"] = serie.strip()
        if ndps:
            res["rps_number"] = ndps.strip()
        if cobr:
            res["civil_construction_code"] = cobr.strip()
        if art:
            res["civil_construction_art"] = art.strip()

        extra_parts = [p for p in [xnome_trib, inf_compl] if p]
        if extra_parts:
            res["fiscal_additional_data"] = "\n".join(extra_parts)

    @staticmethod
    def _parse_xml_bytes(xml_bytes, nsu, res):
        """Parse XML bytes to extract all relevant national NFS-e properties."""
        try:
            root = etree.fromstring(xml_bytes)
            for node in root.iter():
                if "}" in node.tag:
                    node.tag = node.tag.split("}", 1)[1]

            all_tags = sorted({n.tag for n in root.iter() if not n.tag.startswith("{")})
            _logger.debug("NFS-e Nacional XML tags for NSU %s: %s", nsu, all_tags)

            NfseDfe._extract_basic_info(root, res)
            NfseDfe._extract_issqn_values(root, res)
            NfseDfe._extract_codes_and_refs(root, res)

        except Exception as exc:
            _logger.warning(
                "Could not parse NFS-e Nacional XML for NSU %s: %s", nsu, exc
            )

    def _company_cnpj_digits(self):
        """Return the company CNPJ with only digits (14 chars)."""
        cnpj = self.company_id.cnpj_cpf or ""
        return "".join(c for c in cnpj if c.isdigit())

    def _create_received_records(self, data_list):
        """Create l10n_br_nfse.received records, skipping duplicates."""
        Received = self.env["l10n_br_nfse.received"]
        for data in data_list:
            verify_code = data.get("verify_code")
            nfse_number = data.get("nfse_number")
            provider_cnpj = data.get("provider_cnpj")

            if not verify_code and not nfse_number:
                continue

            existing = False
            if verify_code:
                existing = Received.search(
                    [
                        ("company_id", "=", self.company_id.id),
                        ("verify_code", "=", verify_code),
                    ],
                    limit=1,
                )

            if not existing and nfse_number:
                domain = [
                    ("company_id", "=", self.company_id.id),
                    ("nfse_number", "=", nfse_number),
                ]
                if provider_cnpj:
                    domain.append(("provider_cnpj", "=", provider_cnpj))
                existing = Received.search(domain, limit=1)

            if existing:
                continue

            xml_content = data.pop("xml_content", None)
            received = Received.create(
                {
                    "dfe_id": self.id,
                    "company_id": self.company_id.id,
                    **{k: v for k, v in data.items() if v is not None},
                }
            )
            if xml_content:
                received._create_xml_attachment(xml_content)

    @api.model
    def _cron_sync_received_nfse(self):
        """Fetch received NFS-e for active cron jobs."""
        self.search([("use_cron", "=", True)]).search_received_nfse()
