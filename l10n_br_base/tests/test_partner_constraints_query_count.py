# Copyright (C) 2026 - KMEE (<https://kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase


def _cnpj(root):
    """Return a valid CNPJ for a 12 digit root."""
    digits = [int(char) for char in root]
    for weights in (
        [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
        [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
    ):
        rest = sum(d * w for d, w in zip(digits, weights, strict=True)) % 11
        digits.append(0 if rest < 2 else 11 - rest)
    return "".join(str(d) for d in digits)


class PartnerConstraintsQueryCountTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context, tracking_disable=True, disable_ie_validation=True
            )
        )
        cls.env["ir.config_parameter"].sudo().set_param(
            "l10n_br_base.allow_cnpj_multi_ie", False
        )
        cls.state_ba = cls.env.ref("base.state_br_ba")
        cls.base_vals = {
            "is_company": True,
            "country_id": cls.env.ref("base.br").id,
            "state_id": cls.env.ref("base.state_br_es").id,
            "city_id": cls.env.ref("l10n_br_base.city_3205002").id,
        }

    def _create(self, vals_list):
        return self.env["res.partner"].create(
            [dict(self.base_vals, **vals) for vals in vals_list]
        )

    def _count_queries(self, method):
        self.env.invalidate_all()
        before = self.env.cr.sql_log_count
        method()
        return self.env.cr.sql_log_count - before

    def _assert_queries_do_not_grow(self, partners, method_name):
        # The constraint is called directly: through create() the number of
        # INSERTs also grows with the batch. The first call warms up the
        # ormcache of the system parameters.
        self._count_queries(getattr(partners[:4], method_name))
        half = self._count_queries(getattr(partners[:4], method_name))
        full = self._count_queries(getattr(partners, method_name))
        self.assertEqual(full, half)

    def test_cnpj_check(self):
        partners = self._create(
            [
                {"name": f"Batch {n}", "vat": _cnpj(f"11222333{n:04d}")}
                for n in range(1, 9)
            ]
        )
        self._assert_queries_do_not_grow(partners, "_check_cnpj_l10n_br_ie_code")

    def test_state_tax_number_check(self):
        partners = self._create(
            [
                {
                    "name": f"Batch {n}",
                    "state_tax_number_ids": [
                        (
                            0,
                            0,
                            {
                                "state_id": self.state_ba.id,
                                "l10n_br_ie_code": f"10000{n}",
                            },
                        )
                    ],
                }
                for n in range(1, 9)
            ]
        )
        self._assert_queries_do_not_grow(partners, "_check_state_tax_number_ids")
