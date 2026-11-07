# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class L10nBrCoaGeneric(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.l10n_br_coa_generic = cls.env.ref(
            "l10n_br_coa_generic.l10n_br_coa_generic_template"
        )
        cls.l10n_br_company = cls.env["res.company"].create(
            {"name": "Empresa Teste do Plano de Contas CFC"}
        )

    def test_l10n_br_coa_generic(self):
        """Test installing the chart of accounts template in a new company"""
        self.l10n_br_coa_generic.try_loading(company=self.l10n_br_company)
        self.assertEqual(
            self.l10n_br_coa_generic, self.l10n_br_company.chart_template_id
        )

    def _taxes_by_name(self, name):
        return self.env["account.tax"].search(
            [("company_id", "=", self.l10n_br_company.id), ("name", "=", name)]
        )

    def _tax_line(self, tax, refund=False):
        lines = (
            tax.refund_repartition_line_ids
            if refund
            else (tax.invoice_repartition_line_ids)
        )
        return lines.filtered(lambda line: line.repartition_type == "tax")

    def test_icms_st_sale_taxes_have_accounts_and_deductible_pair(self):
        """ICMS ST of a sale has its liability account and a deductible pair.

        With the deductible taxes operation the product line already carries the
        ST, so the ST tax line has to be offset by the deductible tax, as it is
        done for the other taxes. Without the pair the due amount of the
        invoice counts the ST twice.
        """
        self.l10n_br_coa_generic.try_loading(company=self.l10n_br_company)
        st = self._taxes_by_name("ICMS Saida Subist")
        st_ded = self._taxes_by_name("ICMS Saida Subist Dedutível")
        self.assertEqual(len(st), 1)
        self.assertEqual(len(st_ded), 1)
        self.assertEqual(st_ded.type_tax_use, "sale")
        self.assertTrue(st_ded.deductible)
        self.assertEqual(st_ded.tax_group_id, st.tax_group_id)
        payable = self.env["account.account"].search(
            [("company_id", "=", self.l10n_br_company.id), ("code", "=", "2.1.7.1.11")]
        )
        deduction = self.env["account.account"].search(
            [("company_id", "=", self.l10n_br_company.id), ("code", "=", "6.1.1.2.07")]
        )
        deduction_refund = self.env["account.account"].search(
            [("company_id", "=", self.l10n_br_company.id), ("code", "=", "6.1.1.2.27")]
        )
        st_line = self._tax_line(st)
        ded_line = self._tax_line(st_ded)
        ded_refund_line = self._tax_line(st_ded, refund=True)
        self.assertEqual(st_line.account_id, payable)
        self.assertEqual(st_line.factor_percent, 100)
        self.assertEqual(ded_line.account_id, deduction)
        self.assertEqual(ded_line.factor_percent, -100)
        self.assertEqual(ded_refund_line.account_id, deduction_refund)
        self.assertEqual(ded_refund_line.factor_percent, -100)

    def test_icms_st_purchase_tax_stays_without_account(self):
        """The ST of a purchase is cost: it keeps no account."""
        self.l10n_br_coa_generic.try_loading(company=self.l10n_br_company)
        st = self._taxes_by_name("ICMS Entrada Subist")
        self.assertEqual(len(st), 1)
        self.assertFalse(self._tax_line(st).account_id)
        self.assertFalse(self._tax_line(st, refund=True).account_id)

    def _simulate_company_loaded_before(self):
        """Leave the company as a chart loaded before the ST pair left it.

        No deductible ICMS ST and the ICMS ST of the sale without account.
        """
        self.l10n_br_coa_generic.try_loading(company=self.l10n_br_company)
        st = self._taxes_by_name("ICMS Saida Subist")
        st_ded = self._taxes_by_name("ICMS Saida Subist Dedutível")
        xmlid = (
            f"l10n_br_coa.{self.l10n_br_company.id}_tax_template_icms_st_out_deductible"
        )
        st_ded.unlink()
        self.env["ir.model.data"].search(
            [
                ("module", "=", "l10n_br_coa"),
                (
                    "name",
                    "=",
                    f"{self.l10n_br_company.id}_tax_template_icms_st_out_deductible",
                ),
            ]
        ).unlink()
        self.assertFalse(self.env.ref(xmlid, raise_if_not_found=False))
        for refund in (False, True):
            self._tax_line(st, refund=refund).account_id = False
        return st

    def test_migration_creates_deductible_st_and_accounts(self):
        """The migration method completes a company that loaded the chart before."""
        st = self._simulate_company_loaded_before()
        self.env["account.chart.template"]._complete_icms_st()
        st_ded = self._taxes_by_name("ICMS Saida Subist Dedutível")
        self.assertEqual(len(st_ded), 1)
        self.assertTrue(st_ded.deductible)
        self.assertEqual(st_ded.type_tax_use, "sale")
        self.assertEqual(st_ded.tax_group_id, st.tax_group_id)
        code = {
            "payable": "2.1.7.1.11",
            "deduction": "6.1.1.2.07",
            "deduction_refund": "6.1.1.2.27",
        }
        accounts = {
            key: self.env["account.account"].search(
                [("company_id", "=", self.l10n_br_company.id), ("code", "=", value)]
            )
            for key, value in code.items()
        }
        self.assertEqual(self._tax_line(st).account_id, accounts["payable"])
        self.assertEqual(
            self._tax_line(st, refund=True).account_id, accounts["payable"]
        )
        self.assertEqual(self._tax_line(st).factor_percent, 100)
        self.assertEqual(self._tax_line(st_ded).account_id, accounts["deduction"])
        self.assertEqual(self._tax_line(st_ded).factor_percent, -100)
        self.assertEqual(
            self._tax_line(st_ded, refund=True).account_id, accounts["deduction_refund"]
        )
        self.assertEqual(self._tax_line(st_ded, refund=True).factor_percent, -100)

    def test_migration_is_idempotent_and_keeps_user_account(self):
        """Running again duplicates nothing and keeps an account set by the user."""
        st = self._simulate_company_loaded_before()
        custom = self.env["account.account"].search(
            [("company_id", "=", self.l10n_br_company.id), ("code", "=", "2.1.7.1.02")],
            limit=1,
        )
        self.assertTrue(custom)
        self._tax_line(st).account_id = custom
        Chart = self.env["account.chart.template"]
        Chart._complete_icms_st()
        Chart._complete_icms_st()
        self.assertEqual(len(self._taxes_by_name("ICMS Saida Subist Dedutível")), 1)
        self.assertEqual(len(self._taxes_by_name("ICMS Saida Subist")), 1)
        self.assertEqual(self._tax_line(st).account_id, custom)

    def test_migration_does_nothing_for_company_without_chart(self):
        """A company that never loaded the chart gets no tax from the migration."""
        company = self.env["res.company"].create({"name": "Empresa sem plano"})
        self.env["account.chart.template"]._complete_icms_st()
        self.assertFalse(
            self.env["account.tax"].search(
                [("company_id", "=", company.id), ("name", "ilike", "Subist")]
            )
        )

    def test_icms_st_sale_invoice_due_amount(self):
        """Sale of 1.000 with ST of 100: the customer owes 1.100, not 1.200.

        The ST is charged once, on its own tax line, which credits the ST
        payable account. Checked on the core invoice with the ST of the
        generic chart.
        """
        self.l10n_br_coa_generic.try_loading(company=self.l10n_br_company)
        st = self._taxes_by_name("ICMS Saida Subist")
        st.write({"amount_type": "percent", "amount": 10.0})
        partner = self.env["res.partner"].create({"name": "Cliente ST"})
        income = self.env["account.account"].search(
            [
                ("company_id", "=", self.l10n_br_company.id),
                ("account_type", "=", "income"),
            ],
            limit=1,
        )
        move = (
            self.env["account.move"]
            .with_company(self.l10n_br_company)
            .create(
                {
                    "move_type": "out_invoice",
                    "partner_id": partner.id,
                    "company_id": self.l10n_br_company.id,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "Produto",
                                "quantity": 1,
                                "price_unit": 1000.0,
                                "account_id": income.id,
                                "tax_ids": [(6, 0, st.ids)],
                            },
                        )
                    ],
                }
            )
        )
        self.assertEqual(move.amount_total, 1100.0)
        st_move_line = move.line_ids.filtered(lambda line: line.tax_line_id == st)
        self.assertEqual(st_move_line.credit, 100.0)
        self.assertEqual(st_move_line.account_id.code, "2.1.7.1.11")
