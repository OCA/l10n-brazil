# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants import REINF_BENEFICIARY_PROFILES


class ResPartner(models.Model):
    """What the EFD-Reinf needs to know about a beneficiary.

    Only what really belongs to the person, and not what belongs to the
    payment: the nature of income here is a fallback for what has no service
    type, never the source of truth.

    The Simples Nacional is not repeated here: the localization already keeps
    it in tax_framework, and a second place to say the same thing is a second
    place to get it wrong.
    """

    _inherit = "res.partner"

    reinf_nature_income_id = fields.Many2one(
        comodel_name="l10n_br_reinf.nature.income",
        string="EFD-Reinf Nature of Income",
        help="Fallback nature of income for payments to this partner that have "
        "no service type to take it from.",
    )

    reinf_beneficiary_profile = fields.Selection(
        selection=REINF_BENEFICIARY_PROFILES,
        default="normal",
        required=True,
        help="Why the withholding of this beneficiary may differ from the rule "
        "of the nature of income. It matters for the aggregated withholding: a "
        "dispensation that belongs to the NATURE keeps the aggregate (a "
        "cooperative of work owes no CSLL and still aggregates PIS/PASEP and "
        "COFINS), while an exemption or a zero rate OF THE BENEFICIARY, and a "
        "judicial measure, require the specific revenue codes instead.",
    )

    reinf_exemption_legal_basis = fields.Char(
        string="Exemption Legal Basis",
        help="Legal ground of the exemption or of the zero rate, which the "
        "art. 2 of the IN RFB 459/2004 requires the beneficiary to state, and "
        "which is what a fiscal audit asks for first.",
    )

    @api.constrains("reinf_beneficiary_profile", "reinf_exemption_legal_basis")
    def _check_reinf_exemption_legal_basis(self):
        """An exemption with no legal ground is not an exemption."""
        for record in self:
            if (
                record.reinf_beneficiary_profile in ("exempt", "zero_rate")
                and not record.reinf_exemption_legal_basis
            ):
                raise ValidationError(
                    _(
                        "State the legal basis of the exemption of %s: the "
                        "art. 2 of the IN RFB 459/2004 requires it, and without "
                        "it the withholding is due.",
                        record.display_name,
                    )
                )
