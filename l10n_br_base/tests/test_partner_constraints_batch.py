# Copyright (C) 2026 - KMEE (<https://kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
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


class PartnerConstraintsBatchTest(TransactionCase):
    """The duplicate checks run a fixed number of queries per recordset,
    not one search() per record, and still catch every duplicate."""

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
        cls.partner_model = cls.env["res.partner"]
        cls.state_es = cls.env.ref("base.state_br_es")
        cls.state_ba = cls.env.ref("base.state_br_ba")
        cls.base_vals = {
            "is_company": True,
            "country_id": cls.env.ref("base.br").id,
            "state_id": cls.state_es.id,
            "city_id": cls.env.ref("l10n_br_base.city_3205002").id,
        }

    def _create(self, vals_list):
        return self.partner_model.create(
            [dict(self.base_vals, **vals) for vals in vals_list]
        )

    def _count_queries(self, method):
        self.env.invalidate_all()
        before = self.env.cr.sql_log_count
        method()
        return self.env.cr.sql_log_count - before

    def test_cnpj_check_queries_do_not_grow_with_the_batch(self):
        partners = self._create(
            [
                {"name": f"Batch {n}", "vat": _cnpj(f"11222333{n:04d}")}
                for n in range(1, 9)
            ]
        )
        # the first count after the create also loads caches: discard it
        self._count_queries(partners[:4]._check_cnpj_l10n_br_ie_code)
        half = self._count_queries(partners[:4]._check_cnpj_l10n_br_ie_code)
        full = self._count_queries(partners._check_cnpj_l10n_br_ie_code)
        self.assertEqual(full, half)

    def test_state_tax_number_check_queries_do_not_grow_with_the_batch(self):
        partners = self._create(
            [
                {
                    "name": f"Batch {n}",
                    # without country check_ie returns early: only the
                    # duplicate search is measured
                    "country_id": False,
                    "state_tax_number_ids": [
                        (0, 0, {"state_id": self.state_ba.id, "l10n_br_ie_code": n})
                    ],
                }
                for n in range(100001, 100009)
            ]
        )
        # the first count after the create also loads caches: discard it
        self._count_queries(partners[:4]._check_state_tax_number_ids)
        half = self._count_queries(partners[:4]._check_state_tax_number_ids)
        full = self._count_queries(partners._check_state_tax_number_ids)
        self.assertEqual(full, half)

    def test_duplicate_cnpj_inside_the_batch(self):
        cnpj = _cnpj("112223330001")
        with self.assertRaises(ValidationError):
            self._create(
                [{"name": "First", "vat": cnpj}, {"name": "Second", "vat": cnpj}]
            )

    def test_parent_is_not_a_duplicate_of_its_child(self):
        cnpj = _cnpj("112223330001")
        parent = self._create([{"name": "Parent", "vat": cnpj}])
        self.partner_model.create(
            {"name": "Contact", "parent_id": parent.id, "vat": cnpj}
        )
        # the check runs again on the parent, which has no parent itself
        parent.write({"l10n_br_ie_code": "111111111"})

    def test_state_tax_number_already_used(self):
        bahia = {
            "name": "Bahia",
            "state_id": self.state_ba.id,
            "l10n_br_ie_code": "999",
        }
        self._create([bahia])
        with self.assertRaisesRegex(ValidationError, "State Tax Number already used"):
            self._create(
                [
                    {"name": "Other"},
                    {
                        "name": "Branch",
                        "state_tax_number_ids": [
                            (
                                0,
                                0,
                                {
                                    "state_id": self.state_ba.id,
                                    "l10n_br_ie_code": "999",
                                },
                            )
                        ],
                    },
                ]
            )
