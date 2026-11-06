# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import json
import logging
import re
from datetime import datetime

from erpbrasil.base.misc import punctuation_rm

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_ISSUER_COMPANY

from ..constants.duimp import (
    DUIMP_CARACTERIZACAO_TPINTERMEDIO,
    DUIMP_CBS_TYPE,
    DUIMP_FREE_TEXT_DATE_FIELDS,
    DUIMP_FREE_TEXT_ICMS_BASE,
    DUIMP_FREE_TEXT_MONETARY_FIELDS,
    DUIMP_FREE_TEXT_PATTERNS,
    DUIMP_HEADER_EXTRA_TAX_FIELD,
    DUIMP_HEADER_PAYLOAD_PATHS,
    DUIMP_IBS_TYPES,
    DUIMP_STATE_SELECTION,
    DUIMP_TAX_FIELD_PREFIX,
    DUIMP_TAX_TYPE_SELECTION,
)

_logger = logging.getLogger(__name__)

# Help of the fields the query service never returns, in any node nor in
# the free-text block: they are manual input. Three of them feed the NF-e
# import-declaration group, where the layout requires them, so leaving
# them empty blocks a valid NF-e.
_MANUAL_HELP = (
    "Not returned by the DUIMP query service; fill it in manually from "
    "the DUIMP extract."
)

_TAX_TYPES = {code for code, _label in DUIMP_TAX_TYPE_SELECTION}


class L10nBrDuimpDeclaration(models.Model):
    _name = "l10n_br_duimp.declaration"
    _inherit = ["mail.thread", "mail.activity.mixin", "l10n_br_duimp.mixin"]
    _description = "DUIMP Declaration"
    _rec_name = "number"
    _order = "registration_date desc, number"

    @api.model
    def _default_fiscal_operation(self):
        return self.env.company.import_fiscal_operation_id

    state = fields.Selection(
        selection=DUIMP_STATE_SELECTION,
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )

    number = fields.Char(string="DUIMP Number", index=True, copy=False, tracking=True)
    version = fields.Integer(copy=False, tracking=True)
    status = fields.Char()
    channel = fields.Char()
    registration_date = fields.Date()
    clearance_date = fields.Date(help=_MANUAL_HELP)
    access_key = fields.Char(copy=False)

    importer_name = fields.Char(string="Importer")
    importer_number = fields.Char(string="Importer ID (CNPJ)")
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Vendor", ondelete="restrict"
    )

    incoterm_id = fields.Many2one(
        comodel_name="account.incoterms",
        string="Incoterm",
    )
    clearance_office_name = fields.Char(string="Clearance Customs Unit")
    clearance_office_code = fields.Char(
        string="Clearance Customs Unit Code",
    )
    origin_country_code = fields.Char(string="Country of Origin Code")
    cargo_identification = fields.Char(string="Cargo ID (RUC)")

    # Recovered from the free-text block (see DUIMP_FREE_TEXT_PATTERNS).
    bonded_warehouse = fields.Char()
    gross_weight = fields.Float(string="Gross Weight (kg)", digits=(12, 5))
    net_weight = fields.Float(string="Net Weight (kg)", digits=(12, 5))
    shipping_date = fields.Date()
    arrival_date = fields.Date()
    clearance_state = fields.Char(help=_MANUAL_HELP)
    transport_mode_code = fields.Char()
    operation_type_code = fields.Char(help=_MANUAL_HELP)

    company_id = fields.Many2one(
        comodel_name="res.company", default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.ref("base.BRL"),
        readonly=True,
    )
    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        default=_default_fiscal_operation,
        domain="[('state', '=', 'approved')]",
        readonly=True,
        states={"draft": [("readonly", False)], "open": [("readonly", False)]},
    )
    fiscal_document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document", string="Fiscal Document", copy=False
    )
    account_move_id = fields.Many2one(
        comodel_name="account.move", string="Vendor Bill", copy=False
    )
    total_freight = fields.Monetary()
    total_insurance = fields.Monetary()
    total_customs_value = fields.Monetary(
        compute="_compute_total_customs_value",
        store=True,
    )
    ii_amount = fields.Monetary(string="II (header)")
    ipi_amount = fields.Monetary(string="IPI (header)")
    pis_amount = fields.Monetary(string="PIS (header)")
    cofins_amount = fields.Monetary(string="COFINS (header)")

    # Returned by the DUIMP but with no counterpart on the fiscal document
    # line, so they stay here for auditing only.
    # ICMS is a state tax: this federal service never returns it in a
    # structured node, only inside the free-text block.
    icms_base = fields.Monetary(string="ICMS Base")
    icms_amount = fields.Monetary(string="ICMS Amount")

    # Freight the payload declares at header level ("carga.consolidada"),
    # kept to reconcile against the sum of the items.
    declared_freight_total = fields.Monetary(string="Declared Freight (header)")

    reconciliation_warning = fields.Text(
        compute="_compute_reconciliation_warning",
        string="Reconciliation",
    )

    cbs_total = fields.Monetary(string="CBS (header)")
    ibs_estadual_total = fields.Monetary(string="IBS State (header)")
    ibs_municipal_total = fields.Monetary(string="IBS Municipal (header)")
    siscomex_usage_fee_amount = fields.Monetary(string="Siscomex Fee (header)")

    afrmm_amount = fields.Monetary(
        string="AFRMM Total",
        help="Additional Freight for Renewal of the Merchant Marine. Not "
        "returned by the DUIMP query API (Siscomex Carga/Mercante); enter "
        "it manually from the DUIMP extract.",
    )
    siscomex_fee_amount = fields.Monetary()
    handling_fee_amount = fields.Monetary()
    payload_json = fields.Text(string="Raw DUIMP JSON", copy=False)
    item_ids = fields.One2many(
        comodel_name="l10n_br_duimp.item",
        inverse_name="declaration_id",
        string="Items",
    )
    # Flat views over the items' children, so the per-item tax breakdown
    # the payload carries (base, rate, amount due, legal regime) is
    # actually reachable. Both child models already store declaration_id.
    tax_ids = fields.One2many(
        comodel_name="l10n_br_duimp.item.tax",
        inverse_name="declaration_id",
        string="Item Taxes",
        readonly=True,
    )
    addition_deduction_ids = fields.One2many(
        comodel_name="l10n_br_duimp.addition.deduction",
        inverse_name="declaration_id",
        string="Additions/Deductions",
        readonly=True,
    )
    payment_ids = fields.One2many(
        comodel_name="l10n_br_duimp.payment",
        inverse_name="declaration_id",
        string="Payments",
    )

    _sql_constraints = [
        (
            "number_version_company_uniq",
            "unique(number, version, company_id)",
            "A DUIMP with this number/version already exists for this company.",
        ),
    ]

    @api.depends(
        "item_ids.tax_ids.ad_valorem_rate",
        "total_freight",
        "declared_freight_total",
        "ii_amount",
        "ipi_amount",
        "pis_amount",
        "cofins_amount",
        "item_ids.tax_ids.amount_due",
        "item_ids.allocated_freight",
    )
    def _compute_reconciliation_warning(self):
        """Cross-check what the items add up to against the header totals.

        The DUIMP reports every amount twice - once per item and once
        consolidated - so a mismatch means something was dropped on the
        way in. It catches, for instance, an item whose tax breakdown is
        missing: the line taxes are then taken from the item alone and no
        longer reconcile with the declared total. Informational on
        purpose: rounding differences of a few cents are normal and must
        not block invoicing.
        """
        for record in self:
            messages = []
            declared = record.declared_freight_total
            if declared and record.currency_id.compare_amounts(
                record.total_freight, declared
            ):
                messages.append(
                    _(
                        "Freight: items add up to %(items)s but the DUIMP "
                        "declares %(declared)s."
                    )
                    % {"items": record.total_freight, "declared": declared}
                )
            for type, prefix in DUIMP_TAX_FIELD_PREFIX.items():
                header_total = record[f"{prefix}_total"]
                items_total = sum(
                    record.item_ids.tax_ids.filtered(
                        lambda t, type=type: t.type == type
                    ).mapped("amount_due")
                )
                if not header_total and not items_total:
                    continue
                if record.currency_id.compare_amounts(items_total, header_total):
                    messages.append(
                        _(
                            "%(tax)s: items add up to %(items)s but the header "
                            "declares %(header)s."
                        )
                        % {
                            "tax": type,
                            "items": items_total,
                            "header": header_total,
                        }
                    )
            # False, not "": the view hides the banner with
            # [('reconciliation_warning', '=', False)], and an empty
            # string would leave an empty alert box on screen.
            missing = record.missing_fiscal_taxes() if record.item_ids else []
            if missing:
                messages.append(
                    _(
                        "No tax registered for: %s. These amounts will be "
                        "carried on the invoice line but posted to no tax "
                        "account."
                    )
                    % ", ".join(f"{tax} {rate:g}%" for tax, rate in missing)
                )
            # False, not "": the view hides the banner with
            # [('reconciliation_warning', '=', False)], and an empty
            # string would leave an empty alert box on screen.
            record.reconciliation_warning = "\n".join(messages) or False

    @api.depends("item_ids.customs_value")
    def _compute_total_customs_value(self):
        for record in self:
            record.total_customs_value = sum(record.item_ids.mapped("customs_value"))

    def _import_from_payload(self, dados_gerais, itens=None):
        """Populate this declaration (header + items + tributes +
        additions/deductions + payments) from the Portal Único JSON."""
        self.ensure_one()
        self.item_ids.unlink()
        self.payment_ids.unlink()

        dados_gerais = dados_gerais or {}
        if itens is None:
            itens = dados_gerais.get("itens") or []
        if not itens and isinstance(dados_gerais.get("dadosGerais"), dict):
            dados_gerais = dados_gerais.get("dadosGerais") or dados_gerais
            itens = dados_gerais.get("itens") or itens

        self.payload_json = json.dumps(
            {"dados_gerais": dados_gerais, "itens": itens},
            ensure_ascii=False,
            indent=2,
        )
        header_values = self._prepare_header_values(dados_gerais)
        header_values.update(self._prepare_header_values_from_items(itens or []))
        header_values.update(self._prepare_header_totals_from_items(itens or []))
        self.update(header_values)
        item_vals = []
        for item in itens or []:
            if (
                isinstance(item, dict)
                and item.get("link")
                and not item.get("identificacao")
                and not item.get("mercadoria")
            ):
                continue
            item_vals.append((0, 0, self._prepare_item_values(item)))
        self.write(
            {
                "item_ids": item_vals,
                "payment_ids": [
                    (0, 0, self._prepare_payment_values(pag))
                    for pag in self._payload_payments(dados_gerais)
                ],
            }
        )
        self.item_ids._match_product()
        if not self.partner_id:
            self._match_vendor(itens)
        return self

    def _match_vendor(self, itens):
        """Best-effort vendor preset from the first item's exporter.

        The real response identifies the exporter only by its catalogue
        code (``exportador.codigo``, e.g. "OPE_3") plus ``niOperador`` and
        the country: it carries **no** exporter name anywhere, so matching
        a partner by name can never succeed. The code is matched against
        ``res.partner.ref``, which is where a de-para to the Siscomex
        operator catalogue (CATP) naturally lives; a name, when a future
        payload does provide one, is still honoured first.
        """
        if not itens:
            return
        item = itens[0] if isinstance(itens[0], dict) else {}
        operador = (
            (item.get("dadosOperadorExportador") or {})
            or (item.get("dadosOperadorFabricante") or {})
            or (item.get("exportador") or {})
            or (item.get("fabricante") or {})
        )
        if not operador:
            return
        name = (
            operador.get("nome")
            or operador.get("nomeOperador")
            or operador.get("razaoSocial")
        )
        if name:
            domain = ["|", ("legal_name", "=", name), ("name", "=", name)]
        elif operador.get("codigo"):
            domain = [("ref", "=", operador["codigo"])]
        else:
            return
        partner = self.env["res.partner"].search(domain, limit=1)
        if partner:
            self.partner_id = partner

    def _prepare_header_values(self, dados_gerais):
        identificacao = dados_gerais.get("identificacao") or {}
        situacao = dados_gerais.get("situacao") or {}
        importador = (
            identificacao.get("importador") or dados_gerais.get("importador") or {}
        )
        taxes = self._payload_header_taxes(dados_gerais)
        # "resultadoAnaliseRisco" is a sibling of "situacao" inside
        # dados_gerais, not a child of it. There is deliberately no fallback
        # to situacaoConferenciaAduaneira: that holds the customs conference
        # status ("CONCLUIDA_AUTOMATICAMENTE"), not the channel, and writing
        # it here fills the field with a plausible but wrong value.
        resultado_risco = dados_gerais.get("resultadoAnaliseRisco") or {}
        channel = (
            resultado_risco.get("canalConsolidado")
            or situacao.get("canalConsolidado")
            or situacao.get("canalConferencia")
            or identificacao.get("canal")
        )
        vals = {
            "number": identificacao.get("numero") or self.number,
            "version": identificacao.get("versao") or self.version,
            "status": situacao.get("situacaoDuimp")
            or situacao.get("descricaoSituacaoAtual")
            or identificacao.get("situacao"),
            "channel": channel,
            "registration_date": self._parse_payload_date(
                identificacao.get("dataRegistro")
            ),
            # The payload identifies the importer by "ni" only, with no
            # name. When that CNPJ is the company's own - which it is for
            # every DUIMP it can query - the company name is the answer.
            "importer_name": importador.get("nome")
            or identificacao.get("importadorNome")
            or self._importer_name_from_company(importador.get("ni")),
            "importer_number": importador.get("ni")
            or importador.get("numero")
            or importador.get("cnpj"),
            "access_key": identificacao.get("chaveAcesso")
            or dados_gerais.get("chaveAcesso"),
        }
        vals.update(self._prepare_header_payload_values(dados_gerais))
        vals.update(self._prepare_free_text_values(identificacao))
        vals["declared_freight_total"] = self._payload_float(
            self._payload_path(dados_gerais, "carga.consolidada.freteCargaValorReal")
        )
        for type, prefix in DUIMP_TAX_FIELD_PREFIX.items():
            vals[f"{prefix}_total"] = taxes.get(type, 0.0)
        for type, field_name in DUIMP_HEADER_EXTRA_TAX_FIELD.items():
            vals[field_name] = taxes.get(type, 0.0)
        return {k: v for k, v in vals.items() if v is not None}

    def _prepare_header_values_from_items(self, itens):
        """Header fields the payload only carries inside the items.

        The incoterm and the import characterisation are declared per
        item, but they describe the operation as a whole, so the first
        item that states them answers for the declaration. Both feed the
        NF-e import-declaration group.
        """
        vals = {}
        for item in itens:
            if not isinstance(item, dict):
                continue
            if not vals.get("incoterm_id"):
                code = self._payload_code(
                    (item.get("condicaoVenda") or {}).get("incoterm")
                )
                if code:
                    incoterm = self.env["account.incoterms"].search(
                        [("code", "=", code)], limit=1
                    )
                    if incoterm:
                        vals["incoterm_id"] = incoterm.id
                    else:
                        _logger.warning(
                            "DUIMP %s: incoterm %s is not in the standard "
                            "incoterm table.",
                            self.number,
                            code,
                        )
            if not vals.get("operation_type_code"):
                indicador = (item.get("caracterizacaoImportacao") or {}).get(
                    "indicador"
                )
                codigo = DUIMP_CARACTERIZACAO_TPINTERMEDIO.get(indicador)
                if codigo:
                    vals["operation_type_code"] = codigo
            if len(vals) == 2:
                break
        return vals

    def _prepare_header_totals_from_items(self, itens):
        """Header amounts the payload only exposes per item.

        Freight/insurance come as ``condicaoVenda.frete.valorBRL`` and
        ``condicaoVenda.seguro.valorBRL`` on each item; summing them is
        exact and avoids parsing ``carga.consolidada.freteCargaValorReal``,
        which is a pt-BR formatted string ("6.729,95"). The AFRMM and the
        Siscomex fee are also per item (``tributos.mercadoria.afrmm`` and
        ``.taxaUtilizacao``), so they no longer have to be typed in by
        hand; both stay editable afterwards.
        """
        totals = {
            "total_freight": 0.0,
            "total_insurance": 0.0,
            "afrmm_amount": 0.0,
            "siscomex_fee_amount": 0.0,
        }
        for item in itens:
            condicao_venda = item.get("condicaoVenda") or {}
            tributos_mercadoria = (item.get("tributos") or {}).get("mercadoria") or {}
            totals["total_freight"] += self._payload_float(
                (condicao_venda.get("frete") or {}).get("valorBRL")
            )
            totals["total_insurance"] += self._payload_float(
                (condicao_venda.get("seguro") or {}).get("valorBRL")
            )
            totals["afrmm_amount"] += self._payload_float(
                tributos_mercadoria.get("afrmm")
            )
            totals["siscomex_fee_amount"] += self._payload_float(
                tributos_mercadoria.get("taxaUtilizacao")
            )
        return totals

    def _prepare_free_text_values(self, identificacao):
        """Fields recovered from ``informacaoComplementar``.

        This is the only place the DUIMP reports the ICMS, the transport
        mode and the clearance location, so parsing it is what fills the
        NF-e import-declaration group. Everything here is best effort: a
        label that no longer matches leaves its field empty instead of
        raising, and all of them stay editable.
        """
        text = identificacao.get("informacaoComplementar")
        if not text:
            return {}
        vals = {}
        for field_name, pattern in DUIMP_FREE_TEXT_PATTERNS.items():
            match = re.search(pattern, text, re.MULTILINE)
            if not match:
                continue
            value = match.group(1).strip()
            if field_name in DUIMP_FREE_TEXT_DATE_FIELDS:
                vals[field_name] = self._parse_payload_date_br(value)
            elif field_name in DUIMP_FREE_TEXT_MONETARY_FIELDS:
                vals[field_name] = self._payload_float(value)
            else:
                vals[field_name] = value
        icms_base = re.search(DUIMP_FREE_TEXT_ICMS_BASE, text, re.MULTILINE | re.DOTALL)
        if icms_base:
            vals["icms_base"] = self._payload_float(icms_base.group(1))
        # The bonded warehouse is where clearance physically happened, so
        # it answers nfe40_xLocDesemb when nothing else does.
        if vals.get("bonded_warehouse") and not self.clearance_office_name:
            vals["clearance_office_name"] = vals["bonded_warehouse"]
        return vals

    @api.model
    def _parse_payload_date_br(self, value):
        """dd/mm/yyyy, the format used inside the free-text block."""
        try:
            return datetime.strptime(value, "%d/%m/%Y").date()
        except (TypeError, ValueError):
            return False

    def _importer_name_from_company(self, importer_ni):
        """Company name when the payload's importer CNPJ is the company's."""
        if not importer_ni:
            return False
        company = self.company_id or self.env.company
        if company.cnpj_cpf_stripped == punctuation_rm(str(importer_ni)):
            return company.name
        return False

    def _prepare_header_payload_values(self, dados_gerais):
        """Header fields read straight from DUIMP_HEADER_PAYLOAD_PATHS.

        Freight and insurance are not taken from ``carga`` here: the real
        response only gives them in the negotiated currency, so the BRL
        totals are summed from the items instead (see
        ``_prepare_header_totals_from_items``).
        """
        vals = {}
        for field_name, paths in DUIMP_HEADER_PAYLOAD_PATHS.items():
            value = next(
                (
                    found
                    for found in (
                        self._payload_path(dados_gerais, path) for path in paths
                    )
                    if found
                ),
                False,
            )
            # _payload_code first: a node returned as {"codigo": ...}
            # would otherwise be stringified into the Char field.
            value = self._payload_code(value)
            if value:
                vals[field_name] = str(value)
        return vals

    @api.model
    def _payload_code(self, value):
        """Code of a payload entry that may be a plain value or an object.

        Several nodes are returned as ``{"codigo": "EXW", "complemento":
        null}`` rather than as the bare code, and storing the dict in a
        Char field writes "{'codigo': 'EXW', ...}" into it.
        """
        if isinstance(value, dict):
            return value.get("codigo") or value.get("code") or False
        return value or False

    @api.model
    def _payload_float(self, value):
        """Coerce a payload amount to float.

        The response mixes plain numbers (``valorAduaneiroBRL: 3541.96``),
        numeric strings (``"1218.48"``, ``"24.00000"``) and pt-BR formatted
        strings (``freteCargaValorReal: "6.729,95"``), so the thousands
        separator has to be dropped before the decimal comma is converted.
        """
        if value in (None, False, ""):
            return 0.0
        if isinstance(value, int | float):
            return float(value)
        text = str(value).strip()
        if "," in text:
            text = text.replace(".", "").replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return 0.0

    @api.model
    def _payload_path(self, payload, path):
        """Walk dotted path into payload, return False if missing."""
        value = payload
        for key in path.split("."):
            if not isinstance(value, dict):
                return False
            value = value.get(key)
            if value is None:
                return False
        return value

    @api.model
    def _parse_payload_date(self, value):
        """Parse ISO date (YYYY-MM-DD) from payload."""
        if not value:
            return False
        try:
            return fields.Date.to_date(str(value)[:10])
        except ValueError:
            return False

    def _payload_header_taxes(self, dados_gerais):
        tributos = (dados_gerais.get("tributos") or {}).get("tributosCalculados") or []
        result = {}
        for tributo in tributos:
            type = tributo.get("type")
            if not type:
                continue
            valores = tributo.get("valoresBRL") or {}
            # TAXA_UTILIZACAO comes with "devido": null and only
            # "aRecolher" filled, hence the chain.
            result[type] = self._payload_float(
                valores.get("devido")
                or valores.get("aRecolher")
                or valores.get("calculado")
            )
        return result

    def _payload_payments(self, dados_gerais):
        return dados_gerais.get("pagamentos") or []

    def _prepare_item_values(self, item):
        item_tributo = item.get("itemTributo") or {}
        dados_produto = item.get("dadosProduto") or {}
        dados_mercadoria = item_tributo.get("dadosMercadoria") or {}
        valor_mercadoria = item_tributo.get("valorMercadoria") or {}
        identificacao = item.get("identificacao") or {}
        produto = item.get("produto") or {}
        mercadoria = item.get("mercadoria") or {}
        condicao_venda = item.get("condicaoVenda") or {}
        tributos_item = item.get("tributos") or {}
        tributos_mercadoria = tributos_item.get("mercadoria") or {}
        quantity = self._payload_float(
            dados_mercadoria.get("quantidadeUnidadeComercializada")
            or mercadoria.get("quantidadeComercial")
        )
        price_total = self._payload_float(
            valor_mercadoria.get("valorMercadoria")
            or dados_mercadoria.get("valorMercadoriaCondicaoVendaReal")
            or condicao_venda.get("valorBRL")
            or tributos_mercadoria.get("valorLocalEmbarqueBRL")
        )
        moeda_codigo = self._payload_currency_code(
            valor_mercadoria, dados_mercadoria, mercadoria, condicao_venda
        ) or (mercadoria.get("moedaNegociada") or {}).get("codigo")
        customs_value = self._payload_float(
            valor_mercadoria.get("valorAduaneiro")
            or tributos_mercadoria.get("valorAduaneiroBRL")
        )
        allocated_freight = self._payload_float(
            valor_mercadoria.get("valorFreteRateado")
            or (condicao_venda.get("frete") or {}).get("valorBRL")
        )
        allocated_insurance = self._payload_float(
            valor_mercadoria.get("valorSeguroRateado")
            or (condicao_venda.get("seguro") or {}).get("valorBRL")
        )
        return {
            "item_number": identificacao.get("numeroItem")
            or item.get("numeroItem")
            or item.get("indice"),
            "product_code": dados_produto.get("codigoProduto") or produto.get("codigo"),
            "ncm_code": dados_produto.get("codigoNCM") or produto.get("ncm"),
            "description": dados_produto.get("descricao")
            or dados_mercadoria.get("descricaoMercadoria")
            or mercadoria.get("descricao"),
            "quantity": quantity,
            "trade_uom": dados_mercadoria.get("unidadeComercializada")
            or mercadoria.get("unidadeComercial"),
            "price_unit": (price_total / quantity) if quantity else 0.0,
            "merchandise_value": price_total,
            "customs_value": customs_value,
            "allocated_freight": allocated_freight,
            "allocated_insurance": allocated_insurance,
            "exporter_code": (item.get("exportador") or {}).get("codigo")
            or (item.get("fabricante") or {}).get("codigo"),
            "siscomex_fee": self._payload_float(
                tributos_mercadoria.get("taxaUtilizacao")
            ),
            "trade_currency_id": self._s_currency(moeda_codigo).id,
            "exchange_rate": self._payload_exchange_rate(
                valor_mercadoria, condicao_venda
            ),
            "trade_unit_value": self._payload_float(
                dados_mercadoria.get("valorUnitarioCondicaoVenda")
                or mercadoria.get("valorUnitarioMoedaNegociada")
            ),
            "tax_ids": [(0, 0, vals) for vals in self._prepare_item_tax_values(item)],
            "addition_deduction_ids": [
                (0, 0, vals) for vals in self._prepare_addition_deduction_values(item)
            ],
        }

    @api.model
    def _payload_exchange_rate(self, valor_mercadoria, condicao_venda):
        """Exchange rate used by Siscomex for this item.

        The real response carries no explicit rate per item, but it gives
        the same amount in both currencies, so the implicit rate is
        ``valorBRL / valorMoedaNegociada`` (checked against the quote in
        the free-text block: 1218.48 / 216.00 = 5.6411, the euro rate of
        the day). Returns 0.0 when the amounts do not allow it.
        """
        explicit = self._payload_float(valor_mercadoria.get("taxaCambio"))
        if explicit:
            return explicit
        valor_brl = self._payload_float(condicao_venda.get("valorBRL"))
        valor_moeda = self._payload_float(condicao_venda.get("valorMoedaNegociada"))
        if valor_brl and valor_moeda:
            return valor_brl / valor_moeda
        return 0.0

    @api.model
    def _payload_currency_code(self, *payload_parts):
        """Siscomex numeric currency code, wherever the payload carries it."""
        for part in payload_parts:
            code = (part.get("moedaNegociada") or {}).get("codigo") or part.get(
                "codigoMoedaNegociada"
            )
            if code:
                return code
        return False

    def _prepare_addition_deduction_values(self, item):
        result = []
        item_tributo = item.get("itemTributo") or {}
        acrescimos = []
        if isinstance(item.get("condicaoVenda"), dict):
            acrescimos = item["condicaoVenda"].get("acrescimosDeducoes") or []
        if not acrescimos:
            acrescimos = (
                item_tributo.get("acrescimosDeducoes")
                or item.get("acrescimosDeducoes")
                or []
            )
        for acrescimo in acrescimos:
            amount = self._payload_float(
                acrescimo.get("valorReais")
                or acrescimo.get("valorBRL")
                or acrescimo.get("valor")
            )
            if str(acrescimo.get("type") or "").upper().startswith("DEDUC"):
                amount = -abs(amount)
            moeda_codigo = self._payload_currency_code(acrescimo)
            trade_currency_amount = self._payload_float(
                acrescimo.get("valorMoedaNegociada")
            )
            exchange_rate = self._payload_float(acrescimo.get("taxaCambio"))
            result.append(
                {
                    "code": acrescimo.get("codigo"),
                    "description": acrescimo.get("description")
                    or acrescimo.get("nome"),
                    "trade_currency_id": self._s_currency(moeda_codigo).id,
                    "amount": amount,
                    "trade_currency_amount": trade_currency_amount,
                    "exchange_rate": exchange_rate,
                }
            )
        return result

    def _prepare_item_tax_values(self, item):
        result = []
        item_tributo = item.get("itemTributo") or item or {}
        tributos_item = (
            item.get("tributos") if isinstance(item.get("tributos"), dict) else {}
        )
        calculos = (
            item_tributo.get("calculosTributos")
            or tributos_item.get("tributosCalculados")
            or []
        )
        for tributo in calculos:
            type = tributo.get("type") or (tributo.get("tributo") or {}).get("codigo")
            valores = tributo.get("valoresBRL") or {}
            memoria = tributo.get("memoriaCalculo") or {}
            regime = tributo.get("regime") or {}
            fundamentos = memoria.get("fundamentosAplicados") or []
            if not regime and fundamentos:
                regime = fundamentos[0] or {}
            tax_base = self._payload_float(
                memoria.get("baseCalculoBRL")
                or tributo.get("baseCalculo")
                or valores.get("baseCalculo")
            )
            ad_valorem_rate = self._payload_float(
                memoria.get("valorAliquota") or tributo.get("aliquotaAdValorem")
            )
            amount_due = self._payload_float(
                valores.get("devido") or valores.get("calculado")
            )
            amount_to_collect = (
                self._payload_float(valores.get("aRecolher") or valores.get("recolher"))
                or amount_due
            )
            result.append(
                {
                    "type": type if type in _TAX_TYPES else "OUTRO",
                    "regime_code": regime.get("codigo") or regime.get("regime"),
                    "legal_basis_code": regime.get("fundamento")
                    or memoria.get("codigoFundamentoLegalNormal"),
                    "cst": regime.get("cst"),
                    "cclass_trib": regime.get("cclassTrib"),
                    "tax_base": tax_base,
                    "ad_valorem_rate": ad_valorem_rate,
                    "amount_due": amount_due,
                    "amount_to_collect": amount_to_collect,
                }
            )
        return result

    def _prepare_payment_values(self, pagamento):
        principal = pagamento.get("principal") or pagamento or {}
        tributo = principal.get("tributo") or {}
        juros = principal.get("juros") or {}
        return {
            "revenue_code": principal.get("codigoReceita")
            or pagamento.get("codigoReceita"),
            "payment_type_name": tributo.get("type")
            or principal.get("nomeTipoPagamento")
            or pagamento.get("nomeTipoPagamento"),
            # DARF bank details, useful to reconcile the payment
            "bank_name": principal.get("banco"),
            "bank_branch": principal.get("agencia"),
            "bank_account": principal.get("conta"),
            "payment_date": self._parse_payload_date(
                principal.get("dataPagamento") or pagamento.get("dataPagamento")
            ),
            "amendment_number": principal.get("numeroRetificacao")
            or pagamento.get("numeroRetificacao")
            or "0",
            "revenue_amount": principal.get("valor")
            if principal.get("valor") is not None
            else (pagamento.get("valorReceita") or 0.0),
            "interest_amount": juros.get("valor")
            if juros.get("valor") is not None
            else (pagamento.get("valorJurosEncargos") or 0.0),
            "penalty_amount": principal.get("multa")
            if principal.get("multa") is not None
            else (pagamento.get("valorMulta") or 0.0),
        }

    def action_open(self):
        self.write({"state": "open"})

    def action_cancel(self):
        self.write({"state": "canceled"})

    def action_draft(self):
        self.write({"state": "draft"})

    def action_refresh_from_siscomex(self):
        self.ensure_one()
        if self.state == "locked":
            raise UserError(
                _("Cannot refresh a DUIMP that already generated an invoice.")
            )
        if not self.number:
            raise UserError(_("Set the DUIMP number first."))
        webservice = self.company_id._get_duimp_webservice()
        versao = self.version or None
        dados_gerais = webservice.get_general_data(self.number, versao)
        itens = webservice.get_items(self.number, versao)
        self._import_from_payload(dados_gerais, itens)
        return True

    def action_generate_vendor_bill(self):
        self.ensure_one()
        self._validate_invoice_fields()
        confirmation = self._check_missing_fiscal_taxes()
        if confirmation:
            return confirmation
        document = self._create_fiscal_document()
        move = self.env["account.move"].import_fiscal_document(
            document, move_type="in_invoice"
        )
        if self.incoterm_id:
            # account.move carries the incoterm natively; the fiscal
            # document does not, so it is set on the bill directly.
            move.invoice_incoterm_id = self.incoterm_id
        self.write(
            {
                "fiscal_document_id": document.id,
                "account_move_id": move.id,
                "state": "locked",
            }
        )
        return self.action_view_invoice()

    def _validate_invoice_fields(self):
        if not self.item_ids:
            raise UserError(_("The DUIMP must have at least one item."))
        if not self.fiscal_operation_id:
            raise UserError(_("Invoicing requires a fiscal operation."))
        if self.fiscal_operation_id.state != "approved":
            raise UserError(_("The selected fiscal operation is not approved."))
        if not self.partner_id:
            raise UserError(_("Select the vendor (manufacturer/exporter)."))
        missing = self.item_ids.filtered(lambda i: not i.product_id)
        if missing:
            raise UserError(
                _("Every DUIMP item must be matched to an internal product.")
            )
        missing_cfop = self.item_ids.filtered(lambda i: not i.cfop_id)
        if missing_cfop:
            raise UserError(_("Select the CFOP for every DUIMP item."))

    def _get_document_serie(self):
        document_type = self.env.ref("l10n_br_fiscal.document_55")
        serie = self.env["l10n_br_fiscal.document.serie"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("document_type_id", "=", document_type.id),
            ],
            limit=1,
        )
        if not serie:
            serie = self.env["l10n_br_fiscal.document.serie"].create(
                {
                    "code": "1",
                    "name": _("DUIMP Serie"),
                    "document_type_id": document_type.id,
                    "company_id": self.company_id.id,
                }
            )
        return serie

    def _create_fiscal_document(self):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "partner_id": self.partner_id.id,
                "company_id": self.company_id.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "document_serie_id": self._get_document_serie().id,
                "fiscal_operation_id": self.fiscal_operation_id.id,
                "issuer": DOCUMENT_ISSUER_COMPANY,
                "duimp_declaration_id": self.id,
                "duimp_number": self.number,
                "duimp_version": self.version,
                "imported_document": True,
            }
        )
        self.env["l10n_br_fiscal.document.line"].create(
            [
                self._prepare_document_line_values(document, item)
                for item in self.item_ids
            ]
        )
        return document

    def _prepare_document_line_values(self, document, item):
        vals = {
            "document_id": document.id,
            "duimp_item_id": item.id,
            "product_id": item.product_id.id,
            "cfop_id": item.cfop_id.id,
            "fiscal_operation_id": self.fiscal_operation_id.id,
            "uom_id": (item.uom_id or item.product_id.uom_id).id,
            "quantity": item.quantity,
            "price_unit": item.final_price_unit,
            "afrmm_value": item.amount_afrmm,
            "other_value": item.amount_siscomex + item.amount_capatazia,
            "freight_value": item.allocated_freight,
            "insurance_value": item.allocated_insurance,
        }
        vals.update(self._prepare_line_tax_values(item))
        return vals

    def _prepare_line_tax_values(self, item):
        """Federal taxes for the fiscal document line.

        Prefers the per-item breakdown (``itemTributo.calculosTributos``)
        when the payload provides it; otherwise falls back to allocating
        the header totals (``tributos.tributosCalculados``) proportionally
        to the item's customs value - the original behaviour of PR #4655,
        and what the real extract queried so far actually exposes.
        """
        vals = {}
        fiscal_taxes = self.env["l10n_br_fiscal.tax"]
        base = item.customs_value
        line_tributos = item.tax_ids.filtered(
            lambda t: t.type in DUIMP_TAX_FIELD_PREFIX
        )
        if line_tributos:
            for tributo in line_tributos:
                prefix = DUIMP_TAX_FIELD_PREFIX[tributo.type]
                tax_base = tributo.tax_base or base
                percent = tributo.ad_valorem_rate or (
                    (tributo.amount_due / tax_base * 100) if tax_base else 0.0
                )
                vals[f"{prefix}_base"] = tax_base
                vals[f"{prefix}_value"] = tributo.amount_due
                vals[f"{prefix}_percent"] = percent
                fiscal_taxes |= self._link_fiscal_tax(vals, prefix, percent)
            vals.update(self._prepare_line_reform_tax_values(item))
            vals["fiscal_tax_ids"] = [(6, 0, fiscal_taxes.ids)]
            return vals

        proportion = (
            (base / self.total_customs_value) if self.total_customs_value else 0.0
        )
        header_totals = {
            "ii": self.ii_amount,
            "ipi": self.ipi_amount,
            "pis": self.pis_amount,
            "cofins": self.cofins_amount,
        }
        for prefix, total_value in header_totals.items():
            if not total_value:
                continue
            value = proportion * total_value
            percent = (value / base * 100) if base else 0.0
            vals[f"{prefix}_base"] = base
            vals[f"{prefix}_value"] = value
            vals[f"{prefix}_percent"] = percent
            fiscal_taxes |= self._link_fiscal_tax(vals, prefix, percent)
        # CBS/IBS have no fiscal.tax to link to in this fallback, but the
        # amounts are still allocated so the reform fields are not empty.
        # The CST/classification come only with the per-item breakdown.
        for prefix, total_value in (
            ("cbs", self.cbs_total),
            ("ibs", self.ibs_estadual_total + self.ibs_municipal_total),
        ):
            if not total_value:
                continue
            value = proportion * total_value
            vals[f"{prefix}_base"] = base
            vals[f"{prefix}_value"] = value
            vals[f"{prefix}_percent"] = (value / base * 100) if base else 0.0
        vals["fiscal_tax_ids"] = [(6, 0, fiscal_taxes.ids)]
        return vals

    def _prepare_line_reform_tax_values(self, item):
        """CBS/IBS fields of the fiscal document line.

        The DUIMP reports the IBS split into its state and municipal
        shares over the same base, while the line carries a single IBS, so
        the rates and amounts are summed. The CST and the tax
        classification (cClassTrib) come from
        ``memoriaCalculo.fundamentosAplicados``, which only the reform
        taxes fill in.
        """
        vals = {}
        cbs = item.tax_ids.filtered(lambda t: t.type == DUIMP_CBS_TYPE)
        ibs = item.tax_ids.filtered(lambda t: t.type in DUIMP_IBS_TYPES)
        if cbs:
            vals.update(
                {
                    "cbs_base": cbs[0].tax_base,
                    "cbs_percent": sum(cbs.mapped("ad_valorem_rate")),
                    "cbs_value": sum(cbs.mapped("amount_due")),
                }
            )
            vals.update(self._prepare_reform_cst_values(cbs[0], "cbs"))
        if ibs:
            vals.update(
                {
                    "ibs_base": ibs[0].tax_base,
                    "ibs_percent": sum(ibs.mapped("ad_valorem_rate")),
                    "ibs_value": sum(ibs.mapped("amount_due")),
                }
            )
            vals.update(self._prepare_reform_cst_values(ibs[0], "ibs"))
        return vals

    def _prepare_reform_cst_values(self, tributo, tax_domain):
        """CST and tax classification of a reform tax, when registered."""
        vals = {}
        if tributo.cst:
            cst = self.env["l10n_br_fiscal.cst"].search(
                [("code", "=", tributo.cst), ("tax_domain", "=", tax_domain)],
                limit=1,
            )
            if cst:
                vals[f"{tax_domain}_cst_id"] = cst.id
        if tributo.cclass_trib:
            classification = self.env["l10n_br_fiscal.tax.classification"].search(
                [("code", "=", tributo.cclass_trib)], limit=1
            )
            if classification:
                vals["tax_classification_id"] = classification.id
        return vals

    def _check_missing_fiscal_taxes(self):
        """Ask for confirmation when a rate has no tax registered.

        Returns the confirmation wizard action, or None to go ahead. The
        declaration already shows the same warning on the form, so this is
        the last net rather than the first notice.
        """
        self.ensure_one()
        if self.env.context.get("duimp_skip_tax_check"):
            return None
        missing = self.missing_fiscal_taxes()
        if not missing:
            return None
        wizard = self.env["l10n_br_duimp.tax_warning_wizard"].create(
            {
                "declaration_id": self.id,
                "message": _(
                    "No tax is registered in the system for:\n\n%(taxes)s\n\n"
                    "The amounts will still be carried on the invoice lines, "
                    "but they will not be posted to a tax account - they end "
                    "up as part of the expense.\n\n"
                    "Register the missing taxes and import the DUIMP again, "
                    "or generate the bill anyway and adjust it afterwards."
                )
                % {"taxes": "\n".join(f"  - {tax} {rate:g}%" for tax, rate in missing)},
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": wizard._name,
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
            "name": _("Taxes not registered"),
        }

    def _line_tax_rates(self, item):
        """[(prefix, rate)] the line will carry, per federal tax.

        Shared by the invoice generation and by the "missing tax" warning,
        so what is announced beforehand is exactly what will be looked up.
        """
        base = item.customs_value
        line_tributos = item.tax_ids.filtered(
            lambda t: t.type in DUIMP_TAX_FIELD_PREFIX
        )
        if line_tributos:
            rates = []
            for tributo in line_tributos:
                tax_base = tributo.tax_base or base
                rates.append(
                    (
                        DUIMP_TAX_FIELD_PREFIX[tributo.type],
                        tributo.ad_valorem_rate
                        or ((tributo.amount_due / tax_base * 100) if tax_base else 0.0),
                    )
                )
            return rates

        proportion = (
            (base / self.total_customs_value) if self.total_customs_value else 0.0
        )
        rates = []
        for prefix in DUIMP_TAX_FIELD_PREFIX.values():
            total_value = self[f"{prefix}_total"]
            if not total_value:
                continue
            value = proportion * total_value
            rates.append((prefix, (value / base * 100) if base else 0.0))
        return rates

    def _find_fiscal_tax(self, prefix, percent):
        return self.env["l10n_br_fiscal.tax"].search(
            [
                ("tax_group_id.tax_domain", "=", prefix),
                ("percent_amount", "=", percent),
            ],
            limit=1,
        )

    def missing_fiscal_taxes(self):
        """Rates used by this DUIMP with no l10n_br_fiscal.tax registered.

        Those amounts reach the invoice line but post to no tax account,
        so the user is told before generating the bill, while there is
        still time to register the tax.
        """
        self.ensure_one()
        missing = set()
        for item in self.item_ids:
            for prefix, percent in self._line_tax_rates(item):
                if not percent:
                    continue
                if not self._find_fiscal_tax(prefix, percent):
                    missing.add((prefix.upper(), round(percent, 4)))
        return sorted(missing)

    def _link_fiscal_tax(self, vals, prefix, percent):
        """Point the line at the l10n_br_fiscal.tax of this rate.

        Without ``<tax>_tax_id`` and ``fiscal_tax_ids`` the amounts show up
        on the line but produce no account.tax, so the vendor bill posts
        everything to the expense account and nothing to the tax accounts.
        This mirrors what the NF-e XML importer does
        (``l10n_br_nfe.document_line``).

        The amounts themselves are never recomputed from the tax found
        here: ``_compute_tax_fields`` and ``_prepare_tax_fields`` both skip
        imported documents, so what the DUIMP declared is what stays.

        Returns an empty recordset when no tax is registered for the rate -
        PIS/COFINS-Importação are often missing from the default tax table -
        and logs it, rather than attaching a tax of the wrong rate.
        """
        tax = self._find_fiscal_tax(prefix, percent)
        if not tax:
            _logger.warning(
                "DUIMP %s: no l10n_br_fiscal.tax registered for %s at %s%%, "
                "the amount is kept on the line but will not be posted to a "
                "tax account.",
                self.number,
                prefix.upper(),
                percent,
            )
            return tax
        vals[f"{prefix}_tax_id"] = tax.id
        return tax

    def action_view_invoice(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_in_invoice_type"
        )
        action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
        action["res_id"] = self.account_move_id.id
        return action

    def action_view_fiscal_document(self):
        """The fiscal document was stored but had no way to be opened."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "l10n_br_fiscal.document",
            "res_id": self.fiscal_document_id.id,
            "view_mode": "form",
            "target": "current",
        }
