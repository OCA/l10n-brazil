# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK_SIMPLES_ALL

_logger = logging.getLogger(__name__)


class DocumentLineMixin(models.AbstractModel):
    """Compute the IBS/CBS of a line with the official RTC rules.

    The override is deliberately narrow: ``l10n_br_fiscal`` keeps computing
    every tax as before, and only the IBS/CBS values are replaced when the
    cClassTrib of the line carries an RTC treatment.  Any missing piece (no
    treatment, no rate for the date, unfinished official rule) falls back to
    the legacy computation with a status on the line: an invoice must never
    fail because a reference table is incomplete.
    """

    _inherit = "l10n_br_fiscal.document.line.mixin"

    rtc_status = fields.Selection(
        selection=[
            ("calculated", "Calculated with the RTC rules"),
            ("no_treatment", "No RTC treatment"),
            ("error", "RTC error, legacy values kept"),
            ("not_implemented", "RTC rule not implemented"),
            ("not_applicable", "Not an IBS/CBS classification"),
            ("simples_nacional", "Simples Nacional, other rule set"),
        ],
        string="RTC status",
        readonly=True,
        copy=False,
    )
    rtc_base = fields.Float(
        string="RTC base",
        digits=(16, 2),
        readonly=True,
        copy=False,
    )
    rtc_ibs_uf_percent = fields.Float(
        string="IBS State rate (%)", digits=(16, 4), readonly=True, copy=False
    )
    rtc_ibs_uf_reduction = fields.Float(
        string="IBS State reduction (%)", digits=(16, 4), readonly=True, copy=False
    )
    rtc_ibs_uf_value = fields.Float(
        string="IBS State value", digits=(16, 2), readonly=True, copy=False
    )
    rtc_ibs_mun_percent = fields.Float(
        string="IBS Municipality rate (%)", digits=(16, 4), readonly=True, copy=False
    )
    rtc_ibs_mun_reduction = fields.Float(
        string="IBS Municipality reduction (%)",
        digits=(16, 4),
        readonly=True,
        copy=False,
    )
    rtc_ibs_mun_value = fields.Float(
        string="IBS Municipality value", digits=(16, 2), readonly=True, copy=False
    )
    rtc_cbs_percent = fields.Float(
        string="CBS rate (%)", digits=(16, 4), readonly=True, copy=False
    )
    rtc_cbs_reduction = fields.Float(
        string="CBS reduction (%)", digits=(16, 4), readonly=True, copy=False
    )
    rtc_cbs_value = fields.Float(
        string="CBS value", digits=(16, 2), readonly=True, copy=False
    )
    rtc_memoria = fields.Text(
        string="RTC calculation memory", readonly=True, copy=False
    )
    rtc_legal_basis = fields.Char(string="RTC legal basis", readonly=True, copy=False)

    # ------------------------------------------------------------------
    # inputs of the calculation
    # ------------------------------------------------------------------
    def _rtc_base_amount(self):
        """Value of the operation, the ``baseCalculoInformada`` of the API.

        For a NF-e/NFC-e line this is vProd + vFrete + vSeg + vOutro - vDesc;
        the legacy implementation computes the IBS base by removing the ICMS,
        PIS and COFINS, which belongs to the old "tax inside the price" logic
        and understates the base of a tax computed on the full price.
        """
        self.ensure_one()
        price = self.fiscal_price or self.price_unit or 0.0
        quantity = self.fiscal_quantity or self.quantity or 0.0
        amount = price * quantity
        amount -= self.discount_value or 0.0
        amount += (
            (self.freight_value or 0.0)
            + (self.insurance_value or 0.0)
            + (self.other_value or 0.0)
        )
        return amount

    def _rtc_nomenclature_code(self, classification):
        """NCM or NBS to validate against the annexes, depending on the code."""
        self.ensure_one()
        nomenclature = classification.rtc_nomenclature
        if nomenclature in ("ncm", "cib_ncm"):
            return self.ncm_id.code or None
        if nomenclature == "nbs":
            return self.nbs_id.code or None
        if nomenclature == "nbs_ncm":
            return self.nbs_id.code or self.ncm_id.code or None
        return None

    def _rtc_tax_date(self):
        """Date used to look the official rates up.

        Only the lines of a fiscal document carry a ``document_date``: the
        other models sharing this mixin (sale, purchase, contract...) have no
        ``document_id`` at all, so they fall back on the context date.
        """
        self.ensure_one()
        document_date = (
            self.document_id.document_date if hasattr(self, "document_id") else False
        )
        if document_date:
            return fields.Date.to_date(document_date)
        return fields.Date.context_today(self)

    # ------------------------------------------------------------------
    # engine call
    # ------------------------------------------------------------------
    def _rtc_compute(self):
        """Return ``(result, status)``; ``result`` is False on the legacy path.

        Odoo records have no ``__dict__``: the result cannot be cached on the
        line, and both ``_prepare_fields_ibs`` and ``_prepare_fields_cbs``
        call this method. The extra lookups are cheap (indexed searches) and
        keep the code free of environment-wide caches.
        """
        self.ensure_one()

        # Simples Nacional does not compute IBS/CBS from the cClassTrib
        # treatment: it applies its own effective rate on the gross revenue,
        # with its own matrices (regime x type of revenue).  See the
        # calculadora-rtc-simples-nacional project.
        if self.company_id.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
            return False, "simples_nacional"

        classification = self.tax_classification_id
        if not classification or not classification.rtc_treatment_id:
            return False, "no_treatment"

        partner = self.partner_id
        try:
            result = self.env["l10n_br_fiscal.rtc.engine"].compute_item(
                cclass=classification.code,
                base=self._rtc_base_amount(),
                date=self._rtc_tax_date(),
                state=partner.state_id or None,
                city=getattr(partner, "city_id", None) or None,
                quantity=self.fiscal_quantity or self.quantity or 1.0,
                nomenclature_code=self._rtc_nomenclature_code(classification),
            )
        except Exception:  # noqa: BLE001 - never block an invoice
            _logger.exception(
                "RTC computation failed for cClassTrib %s, legacy values kept",
                classification.code,
            )
            return False, "error"

        if result["status"] != "calculated":
            return False, result["status"]
        return result, "calculated"

    def _rtc_common_values(self, result):
        """Technical fields, whatever the tax being prepared."""
        self.ensure_one()
        return {
            "rtc_status": "calculated",
            "rtc_base": result["base"],
            "rtc_ibs_uf_percent": result["taxes"]["ibs_uf"]["rate"],
            "rtc_ibs_uf_reduction": result["taxes"]["ibs_uf"]["reduction"],
            "rtc_ibs_uf_value": result["taxes"]["ibs_uf"]["value"],
            "rtc_ibs_mun_percent": result["taxes"]["ibs_mun"]["rate"],
            "rtc_ibs_mun_reduction": result["taxes"]["ibs_mun"]["reduction"],
            "rtc_ibs_mun_value": result["taxes"]["ibs_mun"]["value"],
            "rtc_cbs_percent": result["taxes"]["cbs"]["rate"],
            "rtc_cbs_reduction": result["taxes"]["cbs"]["reduction"],
            "rtc_cbs_value": result["taxes"]["cbs"]["value"],
            "rtc_memoria": result["memoria"],
            "rtc_legal_basis": result["legal_basis"],
        }

    def _rtc_values_ibs(self, result):
        """IBS fields; the legacy ones stay the reference of the localization."""
        self.ensure_one()
        ibs_uf = result["taxes"]["ibs_uf"]
        ibs_mun = result["taxes"]["ibs_mun"]
        values = self._rtc_common_values(result)
        values.update(
            {
                "ibs_base": result["base"],
                "ibs_percent": ibs_uf["rate"],
                "ibs_reduction": ibs_uf["reduction"],
                "ibs_value": (ibs_uf["value"] or 0.0) + (ibs_mun["value"] or 0.0),
            }
        )
        return values

    def _rtc_values_cbs(self, result):
        self.ensure_one()
        cbs = result["taxes"]["cbs"]
        values = self._rtc_common_values(result)
        values.update(
            {
                "cbs_base": result["base"],
                "cbs_percent": cbs["rate"],
                "cbs_reduction": cbs["reduction"],
                "cbs_value": cbs["value"],
            }
        )
        return values

    # ------------------------------------------------------------------
    # extension points of l10n_br_fiscal
    # ------------------------------------------------------------------
    def _prepare_fields_ibs(self, tax_dict):
        values = super()._prepare_fields_ibs(tax_dict)
        result, status = self._rtc_compute()
        values["rtc_status"] = status
        if result:
            values.update(self._rtc_values_ibs(result))
        return values

    def _prepare_fields_cbs(self, tax_dict):
        values = super()._prepare_fields_cbs(tax_dict)
        result, status = self._rtc_compute()
        values["rtc_status"] = status
        if result:
            values.update(self._rtc_values_cbs(result))
        return values
