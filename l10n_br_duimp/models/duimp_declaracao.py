# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_ISSUER_COMPANY

from ..constants.duimp import (
    DUIMP_STATE_SELECTION,
    DUIMP_TAX_FIELD_PREFIX,
    DUIMP_TRIBUTO_TYPE_SELECTION,
)

_logger = logging.getLogger(__name__)

_TRIBUTO_TYPES = {code for code, _label in DUIMP_TRIBUTO_TYPE_SELECTION}


class L10nBrDuimpDeclaracao(models.Model):
    """Persistent DUIMP (Declaração Única de Importação).

    Merges the persistent relational model of ``l10n_br_di.declaracao``
    (KMEE 14.0) — header, item/payment/value children, state machine and
    chatter — with the Portal Único Siscomex REST payload consumed by the
    Escodoo PR #4655. Unlike the DI (fed by an XML extract), the DUIMP is
    fed by the JSON returned by :class:`DuimpWebservice`.
    """

    _name = "l10n_br_duimp.declaracao"
    _inherit = ["mail.thread", "mail.activity.mixin", "l10n_br_duimp.mixin"]
    _description = "DUIMP Declaration"
    _rec_name = "numero"
    _order = "data_registro desc, numero"

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

    # --- Identification -------------------------------------------------
    numero = fields.Char(string="DUIMP Number", index=True, copy=False, tracking=True)
    versao = fields.Integer(string="Version", copy=False, tracking=True)
    situacao = fields.Char(string="Status")
    canal = fields.Char(string="Channel")
    data_registro = fields.Date(string="Registration Date")
    data_desembaraco = fields.Date(string="Clearance Date")

    # --- Parties --------------------------------------------------------
    importador_nome = fields.Char(string="Importer")
    importador_numero = fields.Char(string="Importer ID (CNPJ)")
    fornecedor_partner_id = fields.Many2one(
        comodel_name="res.partner", string="Vendor", ondelete="restrict"
    )

    # --- Cargo / logistics ----------------------------------------------
    incoterm = fields.Char()
    urf_despacho_nome = fields.Char(string="Clearance Customs Unit")
    uf_desembaraco = fields.Char(string="Clearance State")
    via_transporte_codigo = fields.Char(string="Transport Mode Code")
    caracterizacao_operacao_codigo = fields.Char(string="Operation Type Code")

    # --- Company / accounting -------------------------------------------
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

    # --- Header monetary values -----------------------------------------
    frete_total = fields.Monetary(string="Total Freight")
    seguro_total = fields.Monetary(string="Total Insurance")
    total_valor_aduaneiro = fields.Monetary(
        string="Total Customs Value",
        compute="_compute_totais",
        store=True,
        help="Sum of the items' customs value; allocation base for "
        "header-level costs (AFRMM, Siscomex fee, capatazia).",
    )
    ii_total = fields.Monetary(string="II (header)")
    ipi_total = fields.Monetary(string="IPI (header)")
    pis_total = fields.Monetary(string="PIS (header)")
    cofins_total = fields.Monetary(string="COFINS (header)")

    # Costs not returned by the DUIMP query API (AFRMM comes from Siscomex
    # Carga/Mercante; Siscomex fee/capatazia from the broker): entered
    # manually and allocated to the items by customs value. Full
    # automation (API Mercante) is phase 2.
    afrmm_total = fields.Monetary(
        string="AFRMM Total",
        help="Additional Freight for Renewal of the Merchant Marine. Not "
        "returned by the DUIMP query API (Siscomex Carga/Mercante); enter "
        "it manually from the DUIMP extract.",
    )
    taxa_siscomex_total = fields.Monetary(string="Siscomex Fee Total")
    capatazia_total = fields.Monetary()

    # --- Raw payload (audit) --------------------------------------------
    payload_json = fields.Text(string="Raw DUIMP JSON", copy=False)

    # --- Relations ------------------------------------------------------
    item_ids = fields.One2many(
        comodel_name="l10n_br_duimp.item",
        inverse_name="declaracao_id",
        string="Items",
    )
    pagamento_ids = fields.One2many(
        comodel_name="l10n_br_duimp.pagamento",
        inverse_name="declaracao_id",
        string="Payments",
    )

    _sql_constraints = [
        (
            "numero_versao_company_uniq",
            "unique(numero, versao, company_id)",
            "A DUIMP with this number/version already exists for this company.",
        ),
    ]

    @api.depends("item_ids.valor_aduaneiro")
    def _compute_totais(self):
        for record in self:
            record.total_valor_aduaneiro = sum(
                record.item_ids.mapped("valor_aduaneiro")
            )

    # ====================================================================
    # Payload import (JSON → persistent records)
    # ====================================================================
    def _import_from_payload(self, dados_gerais, itens):
        """Populate this declaration (header + items + tributes +
        additions/deductions + payments) from the Portal Único JSON.

        NOTE (phase 2 / B2): the exact nesting of some keys was not
        validated against a real DUIMP response yet (no e-CNPJ + VAL
        environment access at build time). The mapping follows the public
        documentation and the community client, mirroring what PR #4655
        assumed. Adjust ``_prepare_*_values`` against an actual payload
        before production use.
        """
        self.ensure_one()
        self.item_ids.unlink()
        self.pagamento_ids.unlink()

        self.payload_json = json.dumps(
            {"dados_gerais": dados_gerais, "itens": itens},
            ensure_ascii=False,
            indent=2,
        )
        self.update(self._prepare_header_values(dados_gerais))
        self.write(
            {
                "item_ids": [(0, 0, self._prepare_item_values(item)) for item in itens],
                "pagamento_ids": [
                    (0, 0, self._prepare_pagamento_values(pag))
                    for pag in self._payload_pagamentos(dados_gerais)
                ],
            }
        )
        self.item_ids._match_product()
        if not self.fornecedor_partner_id:
            self._match_vendor(itens)
        return self

    def _match_vendor(self, itens):
        """Best-effort vendor preset from the foreign exporter/manufacturer
        name of the first item (``dadosOperadorExportador`` /
        ``dadosOperadorFabricante``), ported from the transient wizard of
        PR #4655. Missing keys just leave the vendor empty for the user to
        fill in manually."""
        if not itens:
            return
        operador = (itens[0].get("dadosOperadorExportador") or {}) or (
            itens[0].get("dadosOperadorFabricante") or {}
        )
        name = operador.get("nome") or operador.get("nomeOperador")
        if not name:
            return
        partner = self.env["res.partner"].search(
            ["|", ("legal_name", "=", name), ("name", "=", name)], limit=1
        )
        if partner:
            self.fornecedor_partner_id = partner

    def _prepare_header_values(self, dados_gerais):
        identificacao = dados_gerais.get("identificacao") or {}
        # "situacao" is a top-level object on the live payload (the same
        # keys the search wizard reads); keep the identificacao fallback
        # for older/other payload shapes.
        situacao = dados_gerais.get("situacao") or {}
        tributos = self._payload_header_tributos(dados_gerais)
        vals = {
            "numero": identificacao.get("numero") or self.numero,
            "versao": identificacao.get("versao") or self.versao,
            "situacao": situacao.get("situacaoDuimp")
            or situacao.get("descricaoSituacaoAtual")
            or identificacao.get("situacao"),
            "canal": situacao.get("canalConferencia") or identificacao.get("canal"),
            "data_registro": self._parse_payload_date(
                identificacao.get("dataRegistro")
            ),
        }
        for tipo, prefix in DUIMP_TAX_FIELD_PREFIX.items():
            vals[f"{prefix}_total"] = tributos.get(tipo, 0.0)
        return {k: v for k, v in vals.items() if v is not None}

    @api.model
    def _parse_payload_date(self, value):
        """Best-effort ISO date extraction ("2026-01-15", possibly with a
        time part). Returns False when the value cannot be parsed, since
        this field is informational."""
        if not value:
            return False
        try:
            return fields.Date.to_date(str(value)[:10])
        except ValueError:
            return False

    def _payload_header_tributos(self, dados_gerais):
        tributos = (dados_gerais.get("tributos") or {}).get("tributosCalculados") or []
        return {
            tributo.get("tipo"): (tributo.get("valoresBRL") or {}).get("devido") or 0.0
            for tributo in tributos
        }

    def _payload_pagamentos(self, dados_gerais):
        return dados_gerais.get("pagamentos") or []

    def _prepare_item_values(self, item):
        item_tributo = item.get("itemTributo") or {}
        dados_produto = item.get("dadosProduto") or {}
        dados_mercadoria = item_tributo.get("dadosMercadoria") or {}
        valor_mercadoria = item_tributo.get("valorMercadoria") or {}

        quantity = dados_mercadoria.get("quantidadeUnidadeComercializada") or 0.0
        price_total = (
            valor_mercadoria.get("valorMercadoria")
            or dados_mercadoria.get("valorMercadoriaCondicaoVendaReal")
            or 0.0
        )
        return {
            "numero_item": item.get("numeroItem"),
            "codigo_produto": dados_produto.get("codigoProduto"),
            "ncm_codigo": dados_produto.get("codigoNCM"),
            "descricao": dados_produto.get("descricao")
            or dados_mercadoria.get("descricaoMercadoria"),
            "quantidade": quantity,
            "unidade_comercializada": dados_mercadoria.get("unidadeComercializada"),
            "price_unit": (price_total / quantity) if quantity else 0.0,
            "valor_mercadoria": valor_mercadoria.get("valorMercadoria") or 0.0,
            "valor_aduaneiro": valor_mercadoria.get("valorAduaneiro") or 0.0,
            "valor_frete_rateado": valor_mercadoria.get("valorFreteRateado") or 0.0,
            "valor_seguro_rateado": valor_mercadoria.get("valorSeguroRateado") or 0.0,
            "tributo_ids": [
                (0, 0, vals) for vals in self._prepare_item_tributo_values(item_tributo)
            ],
        }

    def _prepare_item_tributo_values(self, item_tributo):
        result = []
        for tributo in item_tributo.get("calculosTributos") or []:
            tipo = tributo.get("tipo")
            valores = tributo.get("valoresBRL") or {}
            result.append(
                {
                    "tipo": tipo if tipo in _TRIBUTO_TYPES else "OUTRO",
                    "regime_codigo": (tributo.get("regime") or {}).get("codigo"),
                    "regime_nome": (tributo.get("regime") or {}).get("nome"),
                    "base_calculo": tributo.get("baseCalculo") or 0.0,
                    "aliquota_ad_valorem": tributo.get("aliquotaAdValorem") or 0.0,
                    "valor_devido": valores.get("devido") or 0.0,
                    "valor_recolher": valores.get("aRecolher")
                    or valores.get("recolher")
                    or 0.0,
                }
            )
        return result

    def _prepare_pagamento_values(self, pagamento):
        return {
            "codigo_receita": pagamento.get("codigoReceita"),
            "codigo_tipo_pagamento": pagamento.get("codigoTipoPagamento"),
            "nome_tipo_pagamento": pagamento.get("nomeTipoPagamento"),
            "valor_receita": pagamento.get("valorReceita") or 0.0,
            "valor_juros_encargos": pagamento.get("valorJurosEncargos") or 0.0,
            "valor_multa": pagamento.get("valorMulta") or 0.0,
        }

    # ====================================================================
    # State machine
    # ====================================================================
    def action_open(self):
        self.write({"state": "open"})

    def action_cancel(self):
        self.write({"state": "canceled"})

    def action_draft(self):
        self.write({"state": "draft"})

    def action_refresh_from_siscomex(self):
        """Re-query the Portal Único for the latest DUIMP data and refresh
        the persistent records (only allowed before the invoice is
        generated)."""
        self.ensure_one()
        if self.state == "locked":
            raise UserError(
                _("Cannot refresh a DUIMP that already generated an invoice.")
            )
        if not self.numero:
            raise UserError(_("Set the DUIMP number first."))
        webservice = self.company_id._get_duimp_webservice()
        versao = self.versao or None
        dados_gerais = webservice.get_general_data(self.numero, versao)
        itens = webservice.get_items(self.numero, versao)
        self._import_from_payload(dados_gerais, itens)
        return True

    # ====================================================================
    # Invoice generation (fusion of DI.gerar_fatura + #4655)
    # ====================================================================
    def action_generate_vendor_bill(self):
        self.ensure_one()
        self._validate_invoice_fields()
        document = self._create_fiscal_document()
        move = self.env["account.move"].import_fiscal_document(
            document, move_type="in_invoice"
        )
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
        if not self.fornecedor_partner_id:
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
        """Create the l10n_br_fiscal.document (imported, so tax fields stay
        editable) with one line per DUIMP item, then let
        ``import_fiscal_document`` materialise the account.move."""
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "partner_id": self.fornecedor_partner_id.id,
                "company_id": self.company_id.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "document_serie_id": self._get_document_serie().id,
                "fiscal_operation_id": self.fiscal_operation_id.id,
                "issuer": DOCUMENT_ISSUER_COMPANY,
                "duimp_declaracao_id": self.id,
                "duimp_number": self.numero,
                "duimp_version": self.versao,
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
            "quantity": item.quantidade,
            "price_unit": item.final_price_unit,
            # AFRMM is added to the total via mixin._add_fields_to_amount,
            # so keep the Siscomex fee + capatazia in "other_value" only to
            # avoid double counting.
            "afrmm_value": item.amount_afrmm,
            "other_value": item.amount_siscomex + item.amount_capatazia,
            "freight_value": item.valor_frete_rateado,
            "insurance_value": item.valor_seguro_rateado,
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
        base = item.valor_aduaneiro
        line_tributos = item.tributo_ids.filtered(
            lambda t: t.tipo in DUIMP_TAX_FIELD_PREFIX
        )
        if line_tributos:
            for tributo in line_tributos:
                prefix = DUIMP_TAX_FIELD_PREFIX[tributo.tipo]
                tax_base = tributo.base_calculo or base
                vals[f"{prefix}_base"] = tax_base
                vals[f"{prefix}_value"] = tributo.valor_devido
                vals[f"{prefix}_percent"] = tributo.aliquota_ad_valorem or (
                    (tributo.valor_devido / tax_base * 100) if tax_base else 0.0
                )
            return vals

        proportion = (
            (base / self.total_valor_aduaneiro) if self.total_valor_aduaneiro else 0.0
        )
        header_totals = {
            "ii": self.ii_total,
            "ipi": self.ipi_total,
            "pis": self.pis_total,
            "cofins": self.cofins_total,
        }
        for prefix, total_value in header_totals.items():
            if not total_value:
                continue
            value = proportion * total_value
            vals[f"{prefix}_base"] = base
            vals[f"{prefix}_value"] = value
            vals[f"{prefix}_percent"] = (value / base * 100) if base else 0.0
        return vals

    def action_view_invoice(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_in_invoice_type"
        )
        action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
        action["res_id"] = self.account_move_id.id
        return action
