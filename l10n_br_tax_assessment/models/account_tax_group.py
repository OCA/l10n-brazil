# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountTaxGroup(models.Model):
    """The tax group carries the assessment regime.

    A mixed taxpayer (cumulative and non-cumulative revenue) configures one tax
    group per regime, so the same journal item is never counted under both.
    """

    _inherit = "account.tax.group"

    regime = fields.Selection(
        selection=[
            ("not_applicable", "Não se aplica"),
            ("non_cumulative", "Não cumulativo"),
            ("cumulative", "Cumulativo"),
        ],
        default="not_applicable",
        required=True,
        help="Regime de apuração dos impostos deste grupo. PIS e COFINS têm "
        "apuração separada por regime, como o M200 da EFD Contribuições "
        "pede: contribuinte com receita mista configura um grupo por "
        "regime. ICMS e IPI usam 'Não se aplica'.",
    )
