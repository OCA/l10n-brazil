# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants import REINF_REVENUE_PERIODICITIES


class ReinfRevenueCode(models.Model):
    """Revenue code (CR) of a DARF.

    It is the code the withholding is collected under, and the key the
    totalizers R-9005 and R-9015 answer with. The periodicity is what tells in
    which group of the R-9015 the code shows up (CRDia, CRSem, CRQui, CRDec or
    CRMen), so it is data, never a constant in the code.

    The validity dates of l10n_br_fiscal.data.abstract are load bearing here:
    the codes and the rates change by law, and the aggregated code of
    PIS/COFINS/CSLL stops existing when PIS and COFINS are extinguished.
    """

    _name = "l10n_br_reinf.revenue.code"
    _inherit = ["l10n_br_fiscal.data.abstract"]
    _description = "EFD-Reinf Revenue Code"

    rate = fields.Float(
        string="Rate (%)",
        digits=(5, 2),
        help="Rate the collection under this code applies over the base. It is "
        "data with validity, and not a constant in the source, because the "
        "rates change by law: the aggregated code of PIS/PASEP, COFINS and CSLL "
        "stops existing as it is when the two first are extinguished.",
    )

    periodicity = fields.Selection(
        selection=REINF_REVENUE_PERIODICITIES,
        required=True,
        default="monthly",
        help="Periodicity of the collection of this revenue code. It says in "
        "which totalizer group of the R-9015 the code is answered.",
    )

    _sql_constraints = [
        (
            "reinf_revenue_code_code_uniq",
            "unique (code)",
            "The revenue code must be unique.",
        )
    ]

    @api.model
    def _valid_at(self, code, date):
        """The revenue code record that is valid at a date.

        Validity is not decoration here: it is what lets a rate change by law
        without rewriting history.
        """
        return self.search(
            [
                ("code", "=", code),
                "|",
                ("date_start", "=", False),
                ("date_start", "<=", date),
                "|",
                ("date_end", "=", False),
                ("date_end", ">=", date),
            ],
            limit=1,
        )

    @api.constrains("code")
    def _check_code(self):
        for record in self:
            code = record.code or ""
            if not 4 <= len(code) <= 6:
                raise ValidationError(
                    _(
                        "The revenue code %(code)s is not valid: the layout asks "
                        "for 4 to 6 characters.",
                        code=code,
                    )
                )
