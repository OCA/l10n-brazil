from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_br_coa.models.template_br_oca import DEFAULT_TAX_ACCOUNTS


@tagged("post_install", "-at_install")
class TestCoaLoad(TransactionCase):  # AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()  # chart_template_ref=None)

        cls.company = cls.env["res.company"].create(
            {
                "name": "Brazilian Test Company",
                "country_id": cls.env.ref("base.br").id,
            }
        )
        cls.env.user.company_ids = [(4, cls.company.id)]
        cls.env.user.company_id = cls.company

        cls.env["account.chart.template"].try_loading(
            "br_oca", company=cls.company, install_demo=False
        )

    def test_load_and_populate_coa(self):
        # Manually call and verify _populate_default_br_tax_accounts
        # This call is normally done from l10n_br_account, so we simulate it here
        # to test the method in isolation within the l10n_br_coa module.
        self.env["account.chart.template"]._populate_default_br_tax_accounts(
            self.company, flavor="cfc", review_suffix="", template_module="account"
        )

        Account = self.env["account.account"]

        # Verify account creation from DEFAULT_TAX_ACCOUNTS
        icms_payable_data = DEFAULT_TAX_ACCOUNTS["tax_icms_payable"]
        icms_payable_account = Account.search(
            [
                ("code", "=", icms_payable_data[0]),
                ("company_id", "=", self.company.id),
            ]
        )
        self.assertEqual(
            len(icms_payable_account), 1, "ICMS a Recolher account was not created."
        )
        self.assertEqual(icms_payable_account.name, icms_payable_data[2])
        self.assertEqual(icms_payable_account.account_type, icms_payable_data[3])

        icms_receivable_data = DEFAULT_TAX_ACCOUNTS["tax_icms_receivable"]
        icms_receivable_account = Account.search(
            [
                ("code", "=", icms_receivable_data[0]),
                ("company_id", "=", self.company.id),
            ]
        )
        self.assertEqual(
            len(icms_receivable_account), 1, "ICMS a Compensar account was not created."
        )

    def test_set_tax_group_accs(self):
        """Test that _set_tax_group_accs correctly updates tax_data with accounts"""
        tax_group = self.env["account.tax.group"].create({"name": "Test Group"})

        account_payable = self.env["account.account"].create(
            {
                "name": "Payable",
                "code": "2.1.0.01.TEST",
                "account_type": "liability_current",
                "company_id": self.company.id,
            }
        )
        account_receivable = self.env["account.account"].create(
            {
                "name": "Receivable",
                "code": "1.1.0.01.TEST",
                "account_type": "asset_current",
                "company_id": self.company.id,
            }
        )
        account_deductible = self.env["account.account"].create(
            {
                "name": "Deductible",
                "code": "1.1.0.02.TEST",
                "account_type": "asset_current",
                "company_id": self.company.id,
            }
        )
        account_deductible_refund = self.env["account.account"].create(
            {
                "name": "Deductible Refund",
                "code": "2.1.0.02.TEST",
                "account_type": "liability_current",
                "company_id": self.company.id,
            }
        )

        mock_group_accounts = {
            tax_group.id: {
                "account_id": account_payable.id,
                "refund_account_id": account_receivable.id,
                "ded_account_id": account_deductible.id,
                "ded_refund_account_id": account_deductible_refund.id,
            }
        }

        with patch.object(
            type(self.env["account.chart.template"]),
            "_get_tax_group_accounts",
            return_value=mock_group_accounts,
        ):
            # Test case 1: Standard Sale Tax
            tax_data_sale = {
                "tax_1": {
                    "tax_group_id": tax_group.id,
                    "type_tax_use": "sale",
                    "repartition_line_ids": [],
                    "refund_repartition_line_ids": [],
                    "deductible": False,
                    "withholdable": False,
                }
            }
            self.env["account.chart.template"]._set_tax_group_accs(
                "br_oca", tax_data_sale
            )
            tax_res = tax_data_sale["tax_1"]
            for _cmd, _id, vals in tax_res["invoice_repartition_line_ids"]:
                self.assertEqual(vals["account_id"], account_payable.id)
            for _cmd, _id, vals in tax_res["refund_repartition_line_ids"]:
                self.assertEqual(vals["account_id"], account_receivable.id)

            # Test case 2: Purchase Tax (swaps accounts)
            tax_data_purchase = {
                "tax_2": {
                    "tax_group_id": tax_group.id,
                    "type_tax_use": "purchase",
                    "repartition_line_ids": [],
                    "refund_repartition_line_ids": [],
                    "deductible": False,
                    "withholdable": False,
                }
            }
            self.env["account.chart.template"]._set_tax_group_accs(
                "br_oca", tax_data_purchase
            )
            tax_res_p = tax_data_purchase["tax_2"]
            # Invoice uses refund_account_id (receivable)
            for _cmd, _id, vals in tax_res_p["invoice_repartition_line_ids"]:
                self.assertEqual(vals["account_id"], account_receivable.id)
            # Refund uses account_id (payable)
            for _cmd, _id, vals in tax_res_p["refund_repartition_line_ids"]:
                self.assertEqual(vals["account_id"], account_payable.id)

            # Test case 3: Deductible Purchase Tax
            tax_data_deductible = {
                "tax_3": {
                    "tax_group_id": tax_group.id,
                    "type_tax_use": "purchase",
                    "repartition_line_ids": [],
                    "refund_repartition_line_ids": [],
                    "deductible": True,
                    "withholdable": False,
                }
            }
            self.env["account.chart.template"]._set_tax_group_accs(
                "br_oca", tax_data_deductible
            )
            tax_res_d = tax_data_deductible["tax_3"]
            # Deductible taxes use ded_account_id directly
            # (no swap logic in code for deductible)
            for _cmd, _id, vals in tax_res_d["invoice_repartition_line_ids"]:
                self.assertEqual(vals["account_id"], account_deductible.id)
            for _cmd, _id, vals in tax_res_d["refund_repartition_line_ids"]:
                self.assertEqual(vals["account_id"], account_deductible_refund.id)
            # Factor percent check (deductible taxes are usually negative in repartition
            # to indicate deduction, code sets it to -100)
            for _cmd, _id, vals in tax_res_d["invoice_repartition_line_ids"]:
                self.assertEqual(vals["factor_percent"], -100)

            # Test case 4: Withholdable Sale Tax
            tax_data_wh_sale = {
                "tax_4": {
                    "tax_group_id": tax_group.id,
                    "type_tax_use": "sale",
                    "repartition_line_ids": [],
                    "refund_repartition_line_ids": [],
                    "deductible": False,
                    "withholdable": True,
                }
            }
            self.env["account.chart.template"]._set_tax_group_accs(
                "br_oca", tax_data_wh_sale
            )
            tax_res_ws = tax_data_wh_sale["tax_4"]
            # Withholdable sale: accounts are set to False
            for _cmd, _id, vals in tax_res_ws["invoice_repartition_line_ids"]:
                self.assertFalse(vals["account_id"])

            # Test case 5: Withholdable Purchase Tax
            tax_data_wh_purchase = {
                "tax_5": {
                    "tax_group_id": tax_group.id,
                    "type_tax_use": "purchase",
                    "repartition_line_ids": [],
                    "refund_repartition_line_ids": [],
                    "deductible": False,
                    "withholdable": True,
                }
            }
            self.env["account.chart.template"]._set_tax_group_accs(
                "br_oca", tax_data_wh_purchase
            )
            tax_res_wp = tax_data_wh_purchase["tax_5"]
            # Withholdable purchase falls into else block, but swap is skipped.
            # So it uses account_id (payable) for invoice.
            for _cmd, _id, vals in tax_res_wp["invoice_repartition_line_ids"]:
                self.assertEqual(vals["account_id"], account_payable.id)
            # And factor percent should be -100 for withholdable
            for _cmd, _id, vals in tax_res_wp["invoice_repartition_line_ids"]:
                self.assertEqual(vals["factor_percent"], -100)
