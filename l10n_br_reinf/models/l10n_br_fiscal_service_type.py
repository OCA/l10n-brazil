# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class FiscalServiceType(models.Model):
    """The nature of income of a service.

    This is where the default belongs: the nature of income describes WHAT was
    paid for, and the service type already carries the withholding_possible
    flag of the localization. Keeping the default on the partner instead, which
    is what the historical implementations did, breaks as soon as the same
    supplier is paid for two different services in the same month, and it
    breaks silently: the event goes out with the wrong natRend.

    The line of the document overrides it, and the partner only carries a
    fallback for what has no service type at all.
    """

    _inherit = "l10n_br_fiscal.service.type"

    reinf_nature_income_id = fields.Many2one(
        comodel_name="l10n_br_reinf.nature.income",
        string="EFD-Reinf Nature of Income",
        help="Default nature of income (natRend) declared for payments of this "
        "service type.",
    )
