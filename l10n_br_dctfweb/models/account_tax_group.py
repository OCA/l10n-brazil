# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountTaxGroup(models.Model):
    """The tax group already carries the regime, so it carries the code too.

    The revenue code of a debit depends on the tax and on the regime, and the
    regime is what the tax assessment partitions by. Putting the code here
    means the mapping has exactly one home, and a mixed taxpayer, which
    already needs one group per regime, gets one code per regime for free.
    """

    _inherit = "account.tax.group"

    dctfweb_revenue_code_id = fields.Many2one(
        comodel_name="l10n_br_dctfweb.revenue.code",
        string="MIT revenue code",
        ondelete="restrict",
        help="Revenue code the debits of this group are confessed under in "
        "the MIT. Leave it empty for a tax the MIT does not cover, such as "
        "ICMS, or for a group whose debits are declared in the eSocial or in "
        "the EFD-Reinf.",
    )
