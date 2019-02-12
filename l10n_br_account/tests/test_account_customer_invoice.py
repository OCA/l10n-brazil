# -*- coding: utf-8 -*-
# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestCustomerInvoice(TransactionCase):

    def setUp(self):
        super(TestCustomerInvoice, self).setUp()
        self.sale_account = self.env['account.account'].create(dict(
            code='X1020',
            name='Product Sales - (test)',
            user_type_id=self.env.ref(
                'account.data_account_type_revenue').id,
            reconcile=True,
        ))
        self.sale_journal = self.env['account.journal'].create(dict(
            name='Sales Journal - (test)',
            code='TSAJ',
            type='sale',
            refund_sequence=True,
            default_debit_account_id=self.sale_account.id,
            default_credit_account_id=self.sale_account.id,
            revenue_expense=True,
        ))
        self.fiscal_category = self.env[
            'l10n_br_account.fiscal.category'].create(
            dict(
                code='Venda Teste',
                name='Venda Teste',
                type='output',
                journal_type='sale',
                property_journal=self.sale_journal.id
            ))
        self.fiscal_position = self.env['account.fiscal.position'].create(dict(
            name='Venda Teste',
            type='output',
            company_id=self.env.ref('base.main_company').id,
            fiscal_category_id=self.fiscal_category.id,
        ))
        self.fiscal_position_rule = self.env[
            'account.fiscal.position.rule'].create(
            dict(
                name='Venda',
                description='Venda',
                company_id=self.env.ref('base.main_company').id,
                from_country=self.env.ref('base.br').id,
                fiscal_category_id=self.fiscal_category.id,
                fiscal_position_id=self.fiscal_position.id,
                use_sale=True,
                use_invoice=True,
                use_picking=True,
            ))
        self.invoice_1 = self.env['account.invoice'].create(dict(
            name='Test Customer Invoice',
            payment_term_id=self.env.ref(
                'account.account_payment_term_advance').id,
            fiscal_category_id=self.fiscal_category.id,
            partner_id=self.env.ref('base.res_partner_3').id,
            reference_type="none",
            journal_id=self.sale_journal.id,
            invoice_line_ids=[(0, 0, {
                'product_id': self.env.ref('product.product_product_5').id,
                'quantity': 10.0,
                'price_unit': 450.0,
                'account_id': self.env['account.account'].search(
                    [('user_type_id', '=', self.env.ref(
                        'account.data_account_type_revenue').id)], limit=1).id,
                'name': 'product test 5',
                'uom_id': self.env.ref('product.product_uom_unit').id,
                'fiscal_category_id': self.fiscal_category.id,
            })]
        ))
        # Invoice with TAXES
        tax_fixed = self.env['account.tax'].create({
            'sequence': 10,
            'name': 'Tax 10.0 (Fixed)',
            'amount': 10.0,
            'amount_type': 'fixed',
            'include_base_amount': True,
        })
        tax_percent_included_base_incl = self.env['account.tax'].create({
            'sequence': 20,
            'name': 'Tax 50.0% (Percentage of Price Tax Included)',
            'amount': 50.0,
            'amount_type': 'division',
            'include_base_amount': True,
        })
        tax_percentage = self.env['account.tax'].create({
            'sequence': 30,
            'name': 'Tax 20.0% (Percentage of Price)',
            'amount': 20.0,
            'amount_type': 'percent',
            'include_base_amount': False,
        })
        self.invoice_2 = self.env['account.invoice'].create(dict(
            name='Test Customer Invoice',
            payment_term_id=self.env.ref(
                'account.account_payment_term_advance').id,
            fiscal_category_id=self.fiscal_category.id,
            partner_id=self.env.ref('base.res_partner_3').id,
            reference_type="none",
            journal_id=self.sale_journal.id,
            invoice_line_ids=[(0, 0, {
                'product_id': self.env.ref('product.product_product_5').id,
                'quantity': 5.0,
                'price_unit': 100.0,
                'account_id': self.env['account.account'].search(
                    [('user_type_id', '=', self.env.ref(
                        'account.data_account_type_revenue').id)], limit=1).id,
                'name': 'product test 5',
                'uom_id': self.env.ref('product.product_uom_unit').id,
                'fiscal_category_id': self.fiscal_category.id,
                'invoice_line_tax_ids': [(6, 0, [
                    tax_fixed.id,
                    tax_percent_included_base_incl.id,
                    tax_percentage.id
                ])],
            })]
        ))
        tax_discount = self.env['account.tax'].create({
            'sequence': 40,
            'name': 'Tax 20.0% (Discount)',
            'amount': 20.0,
            'amount_type': 'percent',
            'include_base_amount': False,
            'tax_discount': True
        })
        self.invoice_3 = self.env['account.invoice'].create(dict(
            payment_term_id=self.env.ref(
                'account.account_payment_term_advance').id,
            fiscal_category_id=self.fiscal_category.id,
            currency_id=self.env.ref('base.EUR').id,
            partner_id=self.env.ref('base.res_partner_3').id,
            reference_type="none",
            journal_id=self.sale_journal.id,
            invoice_line_ids=[(0, 0, {
                'product_id': self.env.ref('product.product_product_5').id,
                'quantity': 10.0,
                'price_unit': 450.0,
                'account_id': self.env['account.account'].search(
                    [('user_type_id', '=', self.env.ref(
                        'account.data_account_type_revenue').id)], limit=1).id,
                'name': 'product test 5',
                'uom_id': self.env.ref('product.product_uom_unit').id,
                'fiscal_category_id': self.fiscal_category.id,
                'invoice_line_tax_ids': [(6, 0, [
                    tax_discount.id,
                    tax_percent_included_base_incl.id,
                    tax_percentage.id
                ])],
            })]
        ))

    def test_state(self):
        self.assertEquals(self.invoice_1.state, 'draft',
                          "Invoice should be in state Draft")
        self.invoice_1.action_invoice_open()
        self.assertEquals(self.invoice_1.state, 'open',
                          "Invoice should be in state Open")

    def test_tax(self):
        self.invoice_2.action_invoice_open()
        self.assertEquals(self.invoice_2.state, 'open',
                          "Invoice should be in state Open")
        invoice_tax = self.invoice_2.tax_line_ids.sorted(
            key=lambda r: r.sequence)
        self.assertEquals(invoice_tax.mapped('amount'), [110.0, 550.0, 220.0])
        self.assertEquals(invoice_tax.mapped('base'), [500.0, 550.0, 1100.0])
        assert self.invoice_2.move_id, "Move not created for open invoice"
        self.invoice_2.pay_and_reconcile(
            self.env['account.journal'].search(
                [('type', '=', 'bank')], limit=1), 10050.0)
        assert self.invoice_2.payment_move_line_ids, \
            "Paymente Move Line not created for Paid invoice"
        self.assertEquals(self.invoice_2.state, 'paid',
                          "Invoice should be in state Paid")

    def test_invoice_other_currency(self):
        self.assertEquals(self.invoice_3.state, 'draft',
                          "Invoice should be in state Draft")
        self.invoice_3.action_invoice_open()
        assert self.invoice_3.move_id, \
            "Move Receivable not created for open invoice"
        assert self.invoice_3.move_line_receivable_id, \
            "Field move_line_receivable_id not created for open invoice"
        self.assertEquals(self.invoice_3.state, 'open',
                          "Invoice should be in state Open")

    def test_account_invoice_cce(self):
        self.account_cce = self.env['l10n_br_account.invoice.cce'].create(dict(
            invoice_id=self.invoice_3.id,
            motivo='TESTE',
        ))
        assert self.account_cce.display_name, \
            'Error with function display_name() of object ' \
            'l10n_br_account.invoice.cce'

    def test_account_invoice_cancel(self):
        with self.assertRaises(ValidationError):
            self.account_invoice_cancel = self.env[
                'l10n_br_account.invoice.cancel'].create(dict(
                    invoice_id=self.invoice_3.id,
                    justificative='TESTE'))
        self.account_invoice_cancel = self.env[
            'l10n_br_account.invoice.cancel'].create(dict(
                invoice_id=self.invoice_3.id,
                justificative='TESTE DEVE TER MAIS DE QUINZE CARACTERES.'))
        assert self.account_invoice_cancel.display_name, \
            'Error with function display_name() of object ' \
            'l10n_br_account.invoice.cancel'
