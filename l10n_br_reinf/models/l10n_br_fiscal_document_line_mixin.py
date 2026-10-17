# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class FiscalDocumentLineMixin(models.AbstractModel):
    """Nature of income per line.

    The field is added to the fiscal line mixin, so it reaches both
    l10n_br_fiscal.document.line and account.move.line, which delegates to it.
    It lives here and not in l10n_br_fiscal because the EFD-Reinf is the only
    thing that reads it today: when the field is accepted upstream, this shim
    goes away and nothing else changes.

    It is a plain field on purpose, and the fallback to the service type and to
    the partner is resolved when it is read, by _reinf_nature_income(). A stored
    computed field here would be written back to the fiscal line on every change
    of its dependencies, and a write on the fiscal line makes l10n_br_account
    recompute the taxes of the line: on a line whose withholdings were informed
    without fiscal taxes behind them, that recomputation zeroes the withheld
    values. Paid for with a failing test, which is the cheap way to find it.
    """

    _inherit = "l10n_br_fiscal.document.line.mixin"

    reinf_nature_income_id = fields.Many2one(
        comodel_name="l10n_br_reinf.nature.income",
        string="EFD-Reinf Nature of Income",
        help="Nature of income (natRend) this line is declared under. Left "
        "empty, it is taken from the service type of the line, and then from "
        "the partner.",
    )

    def _reinf_nature_income(self):
        """The nature of income that actually applies to this line.

        The line wins, then the service type, then the partner. The service
        type is the meaningful default because the nature describes WHAT was
        paid for; the partner is only a last resort, and never the source of
        truth, since the same supplier can be paid for two different services
        in the same month.
        """
        self.ensure_one()
        return (
            self.reinf_nature_income_id
            or self.service_type_id.reinf_nature_income_id
            or self.partner_id.reinf_nature_income_id
        )
