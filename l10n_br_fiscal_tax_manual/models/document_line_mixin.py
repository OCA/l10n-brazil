# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

MANUAL_TAX_DOMAINS = [
    "icms",
    "icmsst",
    "issqn",
    "issqn_wh",
    "ipi",
    "ii",
    "pis",
    "pisst",
    "pis_wh",
    "cofins",
    "cofinsst",
    "cofins_wh",
    "csll",
    "csll_wh",
    "irpj",
    "irpj_wh",
    "inss",
    "inss_wh",
    "cbs",
    "ibs",
]

MANUAL_TAX_FIELDS = [
    f"{domain}_{kind}_manual"
    for domain in MANUAL_TAX_DOMAINS
    for kind in ("base", "value")
]

MANUAL_TAX_HELP = "Leave empty to use the automatic calculation."


class FiscalDocumentLineMixin(models.AbstractModel):
    _inherit = "l10n_br_fiscal.document.line.mixin"

    icms_base_manual = fields.Monetary(
        string="Manual ICMS Base",
        help=MANUAL_TAX_HELP,
    )
    icms_value_manual = fields.Monetary(
        string="Manual ICMS Value",
        help=MANUAL_TAX_HELP,
    )

    icmsst_base_manual = fields.Monetary(
        string="Manual ICMS ST Base",
        help=MANUAL_TAX_HELP,
    )
    icmsst_value_manual = fields.Monetary(
        string="Manual ICMS ST Value",
        help=MANUAL_TAX_HELP,
    )

    issqn_base_manual = fields.Monetary(
        string="Manual ISSQN Base",
        help=MANUAL_TAX_HELP,
    )
    issqn_value_manual = fields.Monetary(
        string="Manual ISSQN Value",
        help=MANUAL_TAX_HELP,
    )

    issqn_wh_base_manual = fields.Monetary(
        string="Manual ISSQN RET Base",
        help=MANUAL_TAX_HELP,
    )
    issqn_wh_value_manual = fields.Monetary(
        string="Manual ISSQN RET Value",
        help=MANUAL_TAX_HELP,
    )

    ipi_base_manual = fields.Monetary(
        string="Manual IPI Base",
        help=MANUAL_TAX_HELP,
    )
    ipi_value_manual = fields.Monetary(
        string="Manual IPI Value",
        help=MANUAL_TAX_HELP,
    )

    ii_base_manual = fields.Monetary(
        string="Manual II Base",
        help=MANUAL_TAX_HELP,
    )
    ii_value_manual = fields.Monetary(
        string="Manual II Value",
        help=MANUAL_TAX_HELP,
    )

    pis_base_manual = fields.Monetary(
        string="Manual PIS Base",
        help=MANUAL_TAX_HELP,
    )
    pis_value_manual = fields.Monetary(
        string="Manual PIS Value",
        help=MANUAL_TAX_HELP,
    )

    pisst_base_manual = fields.Monetary(
        string="Manual PIS ST Base",
        help=MANUAL_TAX_HELP,
    )
    pisst_value_manual = fields.Monetary(
        string="Manual PIS ST Value",
        help=MANUAL_TAX_HELP,
    )

    pis_wh_base_manual = fields.Monetary(
        string="Manual PIS RET Base",
        help=MANUAL_TAX_HELP,
    )
    pis_wh_value_manual = fields.Monetary(
        string="Manual PIS RET Value",
        help=MANUAL_TAX_HELP,
    )

    cofins_base_manual = fields.Monetary(
        string="Manual COFINS Base",
        help=MANUAL_TAX_HELP,
    )
    cofins_value_manual = fields.Monetary(
        string="Manual COFINS Value",
        help=MANUAL_TAX_HELP,
    )

    cofinsst_base_manual = fields.Monetary(
        string="Manual COFINS ST Base",
        help=MANUAL_TAX_HELP,
    )
    cofinsst_value_manual = fields.Monetary(
        string="Manual COFINS ST Value",
        help=MANUAL_TAX_HELP,
    )

    cofins_wh_base_manual = fields.Monetary(
        string="Manual COFINS RET Base",
        help=MANUAL_TAX_HELP,
    )
    cofins_wh_value_manual = fields.Monetary(
        string="Manual COFINS RET Value",
        help=MANUAL_TAX_HELP,
    )

    csll_base_manual = fields.Monetary(
        string="Manual CSLL Base",
        help=MANUAL_TAX_HELP,
    )
    csll_value_manual = fields.Monetary(
        string="Manual CSLL Value",
        help=MANUAL_TAX_HELP,
    )

    csll_wh_base_manual = fields.Monetary(
        string="Manual CSLL RET Base",
        help=MANUAL_TAX_HELP,
    )
    csll_wh_value_manual = fields.Monetary(
        string="Manual CSLL RET Value",
        help=MANUAL_TAX_HELP,
    )

    irpj_base_manual = fields.Monetary(
        string="Manual IRPJ Base",
        help=MANUAL_TAX_HELP,
    )
    irpj_value_manual = fields.Monetary(
        string="Manual IRPJ Value",
        help=MANUAL_TAX_HELP,
    )

    irpj_wh_base_manual = fields.Monetary(
        string="Manual IRPJ RET Base",
        help=MANUAL_TAX_HELP,
    )
    irpj_wh_value_manual = fields.Monetary(
        string="Manual IRPJ RET Value",
        help=MANUAL_TAX_HELP,
    )

    inss_base_manual = fields.Monetary(
        string="Manual INSS Base",
        help=MANUAL_TAX_HELP,
    )
    inss_value_manual = fields.Monetary(
        string="Manual INSS Value",
        help=MANUAL_TAX_HELP,
    )

    inss_wh_base_manual = fields.Monetary(
        string="Manual INSS RET Base",
        help=MANUAL_TAX_HELP,
    )
    inss_wh_value_manual = fields.Monetary(
        string="Manual INSS RET Value",
        help=MANUAL_TAX_HELP,
    )

    cbs_base_manual = fields.Monetary(
        string="Manual CBS Base",
        help=MANUAL_TAX_HELP,
    )
    cbs_value_manual = fields.Monetary(
        string="Manual CBS Value",
        help=MANUAL_TAX_HELP,
    )

    ibs_base_manual = fields.Monetary(
        string="Manual IBS Base",
        help=MANUAL_TAX_HELP,
    )
    ibs_value_manual = fields.Monetary(
        string="Manual IBS Value",
        help=MANUAL_TAX_HELP,
    )

    def _prepare_br_manual_tax_dict(self):
        """Return only the manual tax values filled on the line."""
        self.ensure_one()
        return {fname: self[fname] for fname in MANUAL_TAX_FIELDS if self[fname]}

    def _compute_tax_fields(self):
        # Deliberately not declared with extra @api.depends on the manual
        # fields: this method is shared by l10n_br_fiscal.document.line,
        # account.move.line, sale/purchase order lines and stock.move, and
        # Odoo merges the @api.depends of every class overriding the same
        # compute method to decide which of its fields can be precomputed.
        # Adding non-precompute fields here would make every fiscal field on
        # all of those models lose precompute, everywhere. Recompute is
        # triggered explicitly instead, from write() and from an onchange,
        # below.
        manual_lines = self.filtered(lambda line: line._prepare_br_manual_tax_dict())
        res = super(FiscalDocumentLineMixin, self - manual_lines)._compute_tax_fields()
        # The core passes a fixed kwargs list to compute_taxes(), so the manual
        # values reach the tax engine through the context (see models/tax.py).
        for line in manual_lines:
            super(
                FiscalDocumentLineMixin,
                line.with_context(
                    l10n_br_manual_tax_values=line._prepare_br_manual_tax_dict()
                ),
            )._compute_tax_fields()
        return res

    @api.onchange(*MANUAL_TAX_FIELDS)
    def _onchange_manual_tax_values(self):
        self._compute_tax_fields()

    def write(self, vals):
        manual_fields_written = set(vals) & set(MANUAL_TAX_FIELDS)
        res = super().write(vals)
        if manual_fields_written:
            self._compute_tax_fields()
        return res
