# -*- coding: utf-8 -*-
# Copyright (C) 2017  Daniel Sadamo - KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import tools
from odoo.tests.common import TransactionCase
from odoo.modules.module import get_resource_path

class InvoiceTestCommon(TransactionCase):

    def _load(self, module, *args):
        tools.convert_file(self.cr, 'account',
                           get_resource_path(module, *args),
                           {}, 'init', False, 'test',
                           self.registry._assertion_report)

    def setUp(self):
        super(InvoiceTestCommon, self).setUp()

        self._load('account', 'test', 'account_minimal_test.xml')

        self.main_company = self.env.ref('base.main_company')
        self.partner = self.env.ref('base.res_partner_3')
        self.currency = self.env.ref('base.BRL')

        #  customer invoice setup
        self.fiscal_category_sale = self.env[
            'l10n_br_account.fiscal.category'].create(
            dict(
                code='Venda Teste',
                name='Venda Teste',
                type='output',
                journal_type='sale',
                property_journal=self.env.ref('account.sales_journal').id
            )
        )
        self.fiscal_position_sale = self.env['account.fiscal.position'].create(
            dict(
                name='Venda Teste',
                type='output',
                company_id=self.main_company.id,
                fiscal_category_id=self.fiscal_category_sale.id
            )
        )
        self.fiscal_position_rule_sale = self.env[
            'account.fiscal.position.rule'].create(
            dict(
                name='Venda',
                company_id=self.main_company.id,
                from_country=self.env.ref('base.br').id,
                fiscal_category_id=self.fiscal_category_sale.id,
                fiscal_position_id=self.fiscal_position_sale.id,
                use_sale=True,
                use_invoice=True,
                use_picking=True,
            )
        )
        #  supplier invoice setup
        self.fiscal_category_purchase = self.env[
            'l10n_br_account.fiscal.category'].create(
            dict(
                code='Compra Teste',
                name='Compra Teste',
                type='input',
                journal_type='purchase',
                property_journal=self.env.ref('account.expenses_journal').id
            )
        )
        self.fiscal_position_purchase = self.env[
            'account.fiscal.position'].create(
            dict(
                name='Compra Teste',
                type='input',
                company_id=self.main_company.id,
                fiscal_category_id=self.fiscal_category_purchase.id
            )
        )
        self.fiscal_position_rule_purchase = self.env[
            'account.fiscal.position.rule'].create(
            dict(
                name='Compras',
                company_id=self.main_company.id,
                from_country=self.env.ref('base.br').id,
                fiscal_category_id=self.fiscal_category_purchase.id,
                fiscal_position_id=self.fiscal_position_purchase.id,
                use_purchase=True,
                use_invoice=True,
                use_picking=True,
            )
        )

    def test_customer_invoice(self):
        self.customer_invoice = self.env['account.invoice'].create(
            dict(
                payment_term=self.env.ref(
                    'account.account_payment_term_advance').id,
                partner_id=self.partner.id,
                account_id=self.env.ref(
                    'l10n_br.1_account_template_101050200').id,
                company_id=self.main_company.id,
                currency_id=self.currency.id,
                reference_type='none',
                fiscal_category_id=self.fiscal_category_sale.id,
                fiscal_position_id=self.fiscal_position_sale.id,
                name='Test Customer Invoice',
                invoice_line_ids=[(0, 0,
                                   dict(
                                       product_id=self.env.ref(
                                           'product.product_product_5').id,
                                       quantity=10.0,
                                       name='test invoice line',
                                       price_unit=20.0,
                                       uom_id=self.env.ref(
                                           'product.product_uom_unit').id,
                                       account_id=self.env.ref(
                                           'l10n_br.1_account_'
                                           'template_3010101010200').id,
                                   )
                                   )]
            )
        )
        self.assertEqual(self.customer_invoice.state, 'draft',
                         'Wrong customer invoice state')
        self.customer_invoice.action_invoice_open()
        self.assertEqual(self.customer_invoice.state, 'open',
                         'Wrong customer invoice state')

    def test_supplier_invoice(self):
        self.supplier_invoice = self.env['account.invoice'].create(
            dict(
                payment_term=self.env.ref(
                    'account.account_payment_term_advance').id,
                partner_id=self.partner.id,
                account_id=self.env.ref(
                    'l10n_br.1_account_template_201010100').id,
                company_id=self.main_company.id,
                currency_id=self.currency.id,
                reference_type='none',
                fiscal_category_id=self.fiscal_category_purchase.id,
                fiscal_position_id=self.fiscal_position_purchase.id,
                name='Test Supplier Invoice',
                invoice_line_ids=[(0, 0,
                                   dict(
                                       product_id=self.env.ref(
                                           'product.product_product_5').id,
                                       quantity=10.0,
                                       name='test invoice line',
                                       price_unit=20.0,
                                       uom_id=self.env.ref(
                                           'product.product_uom_unit').id,
                                       account_id=self.env.ref(
                                           'l10n_br.1_account_'
                                           'template_3010103010000').id,
                                   )
                                   )]
            )
        )
        self.assertEqual(self.supplier_invoice.state, 'draft',
                         'Wrong supplier invoice state')
        self.supplier_invoice.action_invoice_open()
        self.assertEqual(self.supplier_invoice.state, 'open',
                         'Wrong customer invoice state')
