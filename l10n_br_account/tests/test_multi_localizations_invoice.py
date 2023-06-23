# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.tests.common import OdooSuite, tagged

_logger = logging.getLogger(__name__)


# flake8: noqa: B950  - line too long
def addTest(self, test):
    """
    This monkey patch is required to avoid triggering all the tests from
    TestAccountMoveOutInvoiceOnchanges when it is imported.
    see https://stackoverflow.com/questions/69091760/how-can-i-import-a-testclass-properly-to-inherit-from-without-it-being-run-as-a
    """
    if type(test).__name__ == "MultiLocalizationsInvoice":
        if test._testMethodName.startswith("test_force_"):
            # in our MultiLocalizationInvoice class tests should start
            # with test_force_ to be enabled in the test suite.
            return OdooSuite.addTest._original_method(self, test)

    elif type(test).__name__ != "TestAccountMoveOutInvoiceOnchanges":
        return OdooSuite.addTest._original_method(self, test)


addTest._original_method = OdooSuite.addTest
OdooSuite.addTest = addTest


# flake8: noqa: E402  - module level import not at top of file
from odoo.addons.account.tests.test_account_move_out_invoice import (
    TestAccountMoveOutInvoiceOnchanges,
)


@tagged("post_install", "-at_install")
class MultiLocalizationsInvoice(TestAccountMoveOutInvoiceOnchanges):
    """
    This is a simple test for ensuring l10n_br_account doesn't break the basic
    account module behavior with customer invoices.
    """

    @classmethod
    def setup_company_data(cls, company_name, chart_template=None, **kwargs):
        usa = cls.env.ref("base.us").id  # would be Brazil by default otherwise
        return super().setup_company_data(
            company_name, chart_template, country_id=usa, **kwargs
        )

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref)
        # FIXME the following line should not be required but as for
        # now if we don't add this group, creating a refund will result
        # in an attempt to create a l10n_br_fiscal.subsequent.document record.
        cls.env.user.groups_id |= cls.env.ref("l10n_br_fiscal.group_manager")

    # The following tests list is taken with
    # cat addons/account/tests/test_account_move_out_invoice.py | grep "def test_"
    # then the following script will format the lines:
    # for line in lines.splitlines():
    #     print(line.replace("def test_", "def test_force_"))
    #     print(line.replace("def ", "    super().").replace("(self):", "()") + "\n")
    #
    # ideally they should made to pass for a True multi-localizations compatibility

    def test_force_out_invoice_onchange_invoice_date(self):
        super().test_out_invoice_onchange_invoice_date()

    def test_force_out_invoice_line_onchange_product_1(self):
        super().test_out_invoice_line_onchange_product_1()

    def test_force_out_invoice_line_onchange_product_2_with_fiscal_pos_1(self):
        super().test_out_invoice_line_onchange_product_2_with_fiscal_pos_1()

    def test_force_out_invoice_line_onchange_product_2_with_fiscal_pos_2(self):
        super().test_out_invoice_line_onchange_product_2_with_fiscal_pos_2()

    #    def test_force_out_invoice_line_onchange_business_fields_1(self):
    #        FIXME
    #        super().test_out_invoice_line_onchange_business_fields_1()

    #    def test_force_out_invoice_line_onchange_accounting_fields_1(self):
    #        FIXME this test works with most of the l10n-brazil modules
    #        but fails because of _order = "date desc, date_maturity ASC, id desc"
    #        inside l10n_br_account_payment_order/models/account_move_line.py
    #        super().test_out_invoice_line_onchange_accounting_fields_1()

    def test_force_out_invoice_line_onchange_partner_1(self):
        super().test_out_invoice_line_onchange_partner_1()

    def test_force_out_invoice_line_onchange_taxes_1(self):
        super().test_out_invoice_line_onchange_taxes_1()

    def test_force_out_invoice_line_onchange_rounding_price_subtotal_1(self):
        super().test_out_invoice_line_onchange_rounding_price_subtotal_1()

    def test_force_out_invoice_line_onchange_rounding_price_subtotal_2(self):
        super().test_out_invoice_line_onchange_rounding_price_subtotal_2()

    def test_force_out_invoice_line_onchange_taxes_2_price_unit_tax_included(self):
        super().test_out_invoice_line_onchange_taxes_2_price_unit_tax_included()

    def test_force_out_invoice_line_onchange_analytic(self):
        super().test_out_invoice_line_onchange_analytic()

    def test_force_out_invoice_line_onchange_analytic_2(self):
        super().test_out_invoice_line_onchange_analytic_2()

    def test_force_out_invoice_line_onchange_cash_rounding_1(self):
        super().test_out_invoice_line_onchange_cash_rounding_1()

    def test_force_out_invoice_line_onchange_currency_1(self):
        super().test_out_invoice_line_onchange_currency_1()

    #    def test_force_out_invoice_line_tax_fixed_price_include_free_product(self):
    #        FIXME
    #        super().test_out_invoice_line_tax_fixed_price_include_free_product()

    #    def test_force_out_invoice_line_taxes_fixed_price_include_free_product(self):
    #        FIXME
    #        super().test_out_invoice_line_taxes_fixed_price_include_free_product()

    def test_force_out_invoice_create_refund(self):
        super().test_out_invoice_create_refund()

    def test_force_out_invoice_create_refund_multi_currency(self):
        super().test_out_invoice_create_refund_multi_currency()

    def test_force_out_invoice_create_refund_auto_post(self):
        super().test_out_invoice_create_refund_auto_post()

    def test_force_out_invoice_create_1(self):
        super().test_out_invoice_create_1()

    def test_force_out_invoice_create_child_partner(self):
        super().test_out_invoice_create_child_partner()

    def test_force_out_invoice_write_1(self):
        super().test_out_invoice_write_1()

    def test_force_out_invoice_write_2(self):
        super().test_out_invoice_write_2()

    def test_force_out_invoice_post_1(self):
        super().test_out_invoice_post_1()

    def test_force_out_invoice_post_2(self):
        super().test_out_invoice_post_2()

    def test_force_out_invoice_switch_out_refund_1(self):
        super().test_out_invoice_switch_out_refund_1()

    def test_force_out_invoice_switch_out_refund_2(self):
        super().test_out_invoice_switch_out_refund_2()

    def test_force_out_invoice_reverse_move_tags(self):
        super().test_out_invoice_reverse_move_tags()

    def test_force_out_invoice_change_period_accrual_1(self):
        super().test_out_invoice_change_period_accrual_1()

    def test_force_out_invoice_multi_date_change_period_accrual(self):
        super().test_out_invoice_multi_date_change_period_accrual()

    def test_force_out_invoice_filter_zero_balance_lines(self):
        super().test_out_invoice_filter_zero_balance_lines()

    def test_force_out_invoice_recomputation_receivable_lines(self):
        super().test_out_invoice_recomputation_receivable_lines()

    def test_force_out_invoice_rounding_recomputation_receivable_lines(self):
        super().test_out_invoice_rounding_recomputation_receivable_lines()

    def test_force_out_invoice_multi_company(self):
        super().test_out_invoice_multi_company()

    def test_force_out_invoice_multiple_switch_payment_terms(self):
        super().test_out_invoice_multiple_switch_payment_terms()

    def test_force_out_invoice_copy_custom_date(self):
        super().test_out_invoice_copy_custom_date()

    def test_force_select_specific_product_account(self):
        super().test_select_specific_product_account()

    def test_force_out_invoice_note_and_tax_partner_is_set(self):
        super().test_out_invoice_note_and_tax_partner_is_set()

    def test_force_out_invoice_reverse_caba(self):
        super().test_out_invoice_reverse_caba()

    def test_force_out_invoice_duplicate_currency_rate(self):
        super().test_out_invoice_duplicate_currency_rate()

    def test_force_out_invoice_depreciated_account(self):
        super().test_out_invoice_depreciated_account()
