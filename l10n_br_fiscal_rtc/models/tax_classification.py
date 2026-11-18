# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class TaxClassification(models.Model):
    """Add the RTC (IBS/CBS) semantics to the existing cClassTrib table.

    The fields are additive: ``tax_ibs_id`` / ``tax_cbs_id`` keep working for
    the modules that already use them.  The engine reads the treatment, the
    per-tax reduction and the credit indicators from here.
    """

    _inherit = "l10n_br_fiscal.tax.classification"

    rtc_treatment_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.rtc.treatment",
        string="RTC Treatment",
        ondelete="restrict",
        index=True,
    )
    rtc_reduction_cbs = fields.Float(
        string="CBS reduction (%)",
        digits=(16, 4),
        help="Percentual de redução da alíquota da CBS para este cClassTrib.",
    )
    rtc_reduction_ibs_uf = fields.Float(
        string="IBS State reduction (%)",
        digits=(16, 4),
    )
    rtc_reduction_ibs_mun = fields.Float(
        string="IBS Municipality reduction (%)",
        digits=(16, 4),
    )
    rtc_credit_acquirer_cbs = fields.Boolean(string="CBS credit for acquirer")
    rtc_credit_acquirer_ibs = fields.Boolean(string="IBS credit for acquirer")
    rtc_presumed_credit_supplier = fields.Boolean(string="Presumed credit for supplier")
    rtc_presumed_credit_acquirer = fields.Boolean(string="Presumed credit for acquirer")
    rtc_prior_credit = fields.Selection(
        selection=[("maintain", "Maintain"), ("reverse", "Reverse")],
        string="Prior operation credit",
    )
    rtc_nomenclature = fields.Selection(
        selection=[
            ("ncm", "NCM"),
            ("nbs", "NBS"),
            ("nbs_ncm", "NBS or NCM"),
            ("cib", "CIB"),
            ("cib_ncm", "CIB or NCM"),
            ("none", "None"),
        ],
        string="Nomenclature",
    )
    rtc_sn_revenue_type = fields.Integer(
        string="Simples Nacional revenue type (tpRBSN)",
        help="Tipo de Receita Bruta do Simples Nacional associado ao "
        "cClassTrib, usado pelo cálculo do Simples (NT 2026.005).",
    )
    rtc_legal_basis_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.rtc.legal.basis",
        string="RTC legal basis",
        ondelete="restrict",
    )

    def _rtc_reduction(self, tax):
        """Reduction in percent for ``tax`` (``cbs``, ``ibs_uf``, ``ibs_mun``)."""
        self.ensure_one()
        return getattr(self, f"rtc_reduction_{tax}", 0.0) or 0.0
