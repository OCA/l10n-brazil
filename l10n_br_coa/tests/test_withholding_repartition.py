# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestWithholdingDeltaDistribution(TransactionCase):
    """A withholding tax leaves the regular repartition branch with no factor.

    _set_tax_group_accs stamps factor_percent -100 on the single tax
    repartition line of a withholding tax, so the branch of
    _add_accounting_data_to_base_line_tax_details that keeps factors >= 0 finds
    nothing and still carries the whole tax amount as a delta. Native Odoo then
    indexes an empty list.
    """

    def test_an_empty_factor_list_distributes_nothing(self):
        self.assertEqual(
            self.env["account.tax"]._distribute_delta_amount_smoothly(
                precision_digits=2, delta_amount=-1312.29, target_factors=[]
            ),
            [],
        )

    def test_a_zero_delta_on_an_empty_list_is_still_empty(self):
        self.assertEqual(
            self.env["account.tax"]._distribute_delta_amount_smoothly(
                precision_digits=2, delta_amount=0.0, target_factors=[]
            ),
            [],
        )

    def test_a_single_factor_takes_the_whole_delta(self):
        self.assertEqual(
            self.env["account.tax"]._distribute_delta_amount_smoothly(
                precision_digits=2, delta_amount=0.03, target_factors=[{"factor": 1.0}]
            ),
            [0.03],
        )

    def test_the_delta_splits_across_the_factors(self):
        self.assertEqual(
            self.env["account.tax"]._distribute_delta_amount_smoothly(
                precision_digits=2,
                delta_amount=0.03,
                target_factors=[{"factor": 0.4}, {"factor": 0.3}, {"factor": 0.3}],
            ),
            [0.01, 0.01, 0.01],
        )

    def test_a_negative_delta_keeps_its_sign(self):
        self.assertEqual(
            self.env["account.tax"]._distribute_delta_amount_smoothly(
                precision_digits=2, delta_amount=-0.02, target_factors=[{"factor": 1.0}]
            ),
            [-0.02],
        )
