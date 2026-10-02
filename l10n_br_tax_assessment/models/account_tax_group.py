# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountTaxGroup(models.Model):
    """The tax group carries the assessment regime.

    This is the partition criterion (council decision D1): a mixed taxpayer,
    with both cumulative and non-cumulative revenue, configures ONE tax group
    per regime. Since the assessment computes only the taxes of its own group,
    the two regimes can never count the same journal items twice, which was
    the defect that doubled the M200 of EFD Contribuicoes.

    Putting the regime here instead of on the assessment makes the invalid
    setup unrepresentable: a group simply cannot be assessed under two
    regimes, so there is no constraint to forget and no user choice to get
    wrong at assessment time.
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
