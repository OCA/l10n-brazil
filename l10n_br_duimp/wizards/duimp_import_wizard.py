# Copyright (C) 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import json
import logging

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_ISSUER_COMPANY

from ..constants.duimp import DUIMP_DOCUMENT_TYPE_CODE, DUIMP_TAX_FIELD_PREFIX

_logger = logging.getLogger(__name__)


class DocumentImportWizard(models.TransientModel):
    """Extends the generic fiscal document importer
    (``l10n_br_fiscal.document.import.wizard``, normally used to parse an
    uploaded NFe/CTe/MDFe XML file) to also support querying a DUIMP
    (Declaração Única de Importação) directly from the Portal Único
    Siscomex REST API by number/version, and generating the corresponding
    fiscal document and vendor bill.

    Unlike NFe/CTe/MDFe, the DUIMP has no official downloadable XML: it is
    only available through the authenticated REST API (mTLS with the
    e-CPF digital certificate of the person representing the company),
    see ``models/duimp_webservice.py``.
    """

    _inherit = "l10n_br_fiscal.document.import.wizard"

    duimp_number = fields.Char(string="DUIMP Number")

    duimp_version = fields.Integer(string="DUIMP Version")

    duimp_line_ids = fields.One2many(
        comodel_name="l10n_br_duimp.import_wizard.line",
        inverse_name="wizard_id",
        string="DUIMP Items",
    )

    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
    )

    duimp_afrmm_value = fields.Monetary(
        string="AFRMM Total",
        currency_field="company_currency_id",
        help="Total AFRMM (Additional Freight for Renewal of the Merchant "
        "Marine) amount. This value is not returned by the DUIMP query "
        "API (it is handled by Siscomex Carga/Mercante) and must be "
        "entered manually from the DUIMP extract. It is allocated to "
        "each item proportionally to its customs value.",
    )

    duimp_raw_json = fields.Text(string="DUIMP JSON", readonly=True)

    @api.onchange("duimp_number")
    def _onchange_duimp_number(self):
        self.duimp_line_ids = [Command.clear()]
        self.duimp_raw_json = False

    def action_consult_duimp(self):
        """Query the Portal Único Siscomex for the DUIMP general data and
        items, and populate the preview grid (``duimp_line_ids``) so the
        user can match each item to an internal product/CFOP before
        confirming the import.
        """
        self.ensure_one()
        if not self.duimp_number:
            raise UserError(_("Please enter the DUIMP number!"))
        webservice = self.company_id._get_duimp_webservice()
        general_data = webservice.get_general_data(
            self.duimp_number, self.duimp_version or None
        )
        items = webservice.get_items(self.duimp_number, self.duimp_version or None)
        self.duimp_raw_json = json.dumps(
            {"dados_gerais": general_data, "itens": items},
            ensure_ascii=False,
            indent=2,
        )
        self._fill_wizard_from_duimp(general_data, items)
        return self._reopen()

    def _fill_wizard_from_duimp(self, general_data, items):
        self._detect_document_type(DUIMP_DOCUMENT_TYPE_CODE)
        identification = general_data.get("identificacao") or {}
        self.duimp_version = identification.get("versao") or self.duimp_version

        exporter_name = self._duimp_exporter_name(items)
        if exporter_name:
            self.issuer_legal_name = exporter_name
            self.partner_id = self._search_partner(
                legal_name=exporter_name, name=exporter_name
            )

        self.duimp_line_ids = [
            Command.create(self._prepare_duimp_line_values(item)) for item in items
        ]

    def _duimp_exporter_name(self, items):
        """Best-effort extraction of the foreign exporter/manufacturer
        name from the first item so the wizard can try to preset the
        vendor.

        NOTE: the exact nesting/keys of ``dadosOperadorExportador`` /
        ``dadosOperadorFabricante`` were not validated against a real
        DUIMP response (only the general shape of the API was confirmed
        from public documentation and community client code). Adjust this
        method against an actual payload before relying on it in
        production; the item preview grid lets the user fix the partner
        manually in the meantime.
        """
        if not items:
            return False
        operator_data = (items[0].get("dadosOperadorExportador") or {}) or (
            items[0].get("dadosOperadorFabricante") or {}
        )
        return operator_data.get("nome") or operator_data.get("nomeOperador")

    def _prepare_duimp_line_values(self, item):
        item_tax = item.get("itemTributo") or {}
        product_data = item.get("dadosProduto") or {}
        merchandise_data = item_tax.get("dadosMercadoria") or {}
        merchandise_value = item_tax.get("valorMercadoria") or {}

        quantity = merchandise_data.get("quantidadeUnidadeComercializada") or 0.0
        price_total = (
            merchandise_value.get("valorMercadoria")
            or merchandise_data.get("valorMercadoriaCondicaoVendaReal")
            or 0.0
        )
        return {
            "wizard_id": self.id,
            "duimp_item_number": item.get("numeroItem"),
            "product_code": product_data.get("codigoProduto"),
            "ncm_code": product_data.get("codigoNCM"),
            "uom_code": merchandise_data.get("unidadeComercializada"),
            "quantity": quantity,
            "price_unit": (price_total / quantity) if quantity else 0.0,
            "customs_value": merchandise_value.get("valorAduaneiro") or 0.0,
            "freight_value": merchandise_value.get("valorFreteRateado") or 0.0,
            "insurance_value": merchandise_value.get("valorSeguroRateado") or 0.0,
        }

    def action_import_duimp(self):
        self.ensure_one()
        if not self.duimp_line_ids:
            raise UserError(_("Query the DUIMP before importing!"))
        if not self.partner_id:
            raise UserError(_("Select the vendor (manufacturer/exporter)!"))
        if self.duimp_line_ids.filtered(lambda line: not line.product_id):
            raise UserError(_("Select the internal product for every DUIMP item!"))
        if self.duimp_line_ids.filtered(lambda line: not line.cfop_id):
            raise UserError(_("Select the CFOP for every DUIMP item!"))

        document = self._create_document_from_duimp()
        move = self.env["account.move"].import_fiscal_document(
            document, move_type="in_invoice"
        )
        return {
            "name": _("Imported Invoice"),
            "type": "ir.actions.act_window",
            "target": "current",
            "views": [[False, "form"]],
            "res_id": move.id,
            "res_model": "account.move",
        }

    def _get_document_serie(self):
        serie = self.env["l10n_br_fiscal.document.serie"].search(
            [
                ("company_id", "=", self.company_id.id),
                (
                    "document_type_id",
                    "=",
                    self.env.ref("l10n_br_fiscal.document_55").id,
                ),
            ],
            limit=1,
        )
        if not serie:
            serie = self.env["l10n_br_fiscal.document.serie"].create(
                {
                    "code": "1",
                    "name": _("DUIMP Serie"),
                    "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                    "company_id": self.company_id.id,
                }
            )
        return serie

    def _create_document_from_duimp(self):
        """Creates the fiscal document with ``imported_document=True``,
        which unlocks free edition of the tax base/percent/value fields
        on its lines - the same mechanism already used when importing
        NFe/CTe/MDFe XML (see
        ``l10n_br_fiscal.document.line.mixin._is_imported()``).
        """
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "partner_id": self.partner_id.id,
                "company_id": self.company_id.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "fiscal_operation_id": self.fiscal_operation_id.id,
                "issuer": DOCUMENT_ISSUER_COMPANY,
                "document_serie_id": self._get_document_serie().id,
                "duimp_number": self.duimp_number,
                "duimp_version": self.duimp_version,
                "imported_document": True,
            }
        )

        totals_by_tax = self._duimp_tax_totals()
        total_customs_value = sum(self.duimp_line_ids.mapped("customs_value"))
        for line in self.duimp_line_ids:
            proportion = (
                (line.customs_value / total_customs_value)
                if total_customs_value
                else 0.0
            )
            self.env["l10n_br_fiscal.document.line"].create(
                self._prepare_document_line_values(
                    document, line, proportion, totals_by_tax
                )
            )
        return document

    def _duimp_tax_totals(self):
        """Header-level federal tax totals ("valor devido") from
        ``tributos.tributosCalculados``, keyed by the
        ``DUIMP_TAX_FIELD_PREFIX`` field prefix. These totals are
        allocated to each line proportionally to its customs value
        (``valorAduaneiro``).
        """
        general_data = json.loads(self.duimp_raw_json or "{}").get("dados_gerais", {})
        taxes = (general_data.get("tributos") or {}).get("tributosCalculados") or []
        return {
            DUIMP_TAX_FIELD_PREFIX[tax["tipo"]]: (tax.get("valoresBRL") or {}).get(
                "devido"
            )
            or 0.0
            for tax in taxes
            if tax.get("tipo") in DUIMP_TAX_FIELD_PREFIX
        }

    def _prepare_document_line_values(self, document, line, proportion, totals_by_tax):
        vals = {
            "document_id": document.id,
            "product_id": line.product_id.id,
            "cfop_id": line.cfop_id.id,
            "fiscal_operation_id": self.fiscal_operation_id.id,
            "quantity": line.quantity,
            "uom_id": line.product_id.uom_id.id,
            "price_unit": line.price_unit,
            "freight_value": line.freight_value,
            "insurance_value": line.insurance_value,
            "afrmm_value": (
                proportion * self.duimp_afrmm_value if self.duimp_afrmm_value else 0.0
            ),
        }
        base = line.customs_value
        for prefix, total_value in totals_by_tax.items():
            value = proportion * total_value
            vals[f"{prefix}_base"] = base
            vals[f"{prefix}_value"] = value
            vals[f"{prefix}_percent"] = (value / base * 100) if base else 0.0
        return vals


class DuimpImportWizardLine(models.TransientModel):
    """Preview/reconciliation grid for the items returned by the DUIMP
    "itens" endpoint, following the same pattern as
    ``l10n_br_nfe.import_xml.products`` used for NFe XML import: it lets
    the user match each DUIMP item (which only carries an internal
    product code reference and the NCM, no free-text description) to an
    existing Odoo product before the fiscal document/invoice lines are
    actually created.
    """

    _name = "l10n_br_duimp.import_wizard.line"
    _description = "DUIMP Import Wizard Line"

    wizard_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.import.wizard",
        required=True,
        ondelete="cascade",
    )

    duimp_item_number = fields.Char(string="DUIMP Item")

    product_code = fields.Char(string="DUIMP Product Code")

    ncm_code = fields.Char(string="DUIMP NCM")

    uom_code = fields.Char(string="DUIMP UoM")

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Internal Product",
    )

    cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP",
    )

    quantity = fields.Float()

    price_unit = fields.Float(string="Unit Price (BRL)")

    customs_value = fields.Monetary(
        currency_field="company_currency_id",
        help="II (Import Duty) tax base reported by the DUIMP for this item.",
    )

    freight_value = fields.Monetary(
        string="Allocated Freight", currency_field="company_currency_id"
    )

    insurance_value = fields.Monetary(
        string="Allocated Insurance", currency_field="company_currency_id"
    )

    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="wizard_id.company_currency_id",
    )
