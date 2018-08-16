# -*- coding: utf-8 -*-
# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestCustomerInvoice(TransactionCase):

    def setUp(self):
        super(TestCustomerInvoice, self).setUp()
        self.sale_account = self.env['account.account'].create(dict(
            code='X1020',
            name='Product Sales - (test)',
            user_type_id=self.env.ref(
                'account.data_account_type_revenue').id,
        ))
        self.sale_journal = self.env['account.journal'].create(dict(
            name='Sales Journal - (test)',
            code='TSAJ',
            type='sale',
            refund_sequence=True,
            default_debit_account_id=self.sale_account.id,
            default_credit_account_id=self.sale_account.id,
        ))
        self.fiscal_category = self.env[
            'l10n_br_account.fiscal.category'].create(dict(
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
            'account.fiscal.position.rule'].create(dict(
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
            invoice_line_ids=[(0, 0, {
                'product_id': self.env.ref('product.product_product_5').id,
                'quantity': 10.0,
                'price_unit': 450.0,
                'account_id': self.env['account.account'].search(
                    [('user_type_id', '=', self.env.ref(
                        'account.data_account_type_revenue').id)], limit=1).id,
                'name': 'product test 5',
                'uom_id': self.env.ref('product.product_uom_unit').id
            })]
        ))

    def test_state(self):
        self.assertEquals(self.invoice_1.state, 'draft',
            "Invoice should be in state Draft")
