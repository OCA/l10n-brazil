# -*- coding: utf-8 -*-
# @ 2017 Akretion - www.akretion.com.br -
#   Clément Mombereau <clement.mombereau@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class AccountInvoiceTest(TransactionCase):
    """Test if a customer and a supplier invoice are in Draft state after creation"""

    def setUp(self):
        super(AccountInvoiceTest, self).setUp()

        ##setUp for SALE##

        #Create Fiscal Category for sale
        self.fiscal_category_sale = self.env['l10n_br_account.fiscal.category'].create({
            'code': 'Venda Teste',
            'name': 'Venda Teste',
            'type': 'output',
            'journal_type': 'sale',
            'property_journal': self.env.ref('account.sales_journal').id
            })

        #Create Fiscal Position for sale
        self.fiscal_position_sale = self.env['account.fiscal.position'].create({
            'name': 'Venda Teste',
            'type': 'output',
            'company_id': self.env.ref('base.main_company').id,
            'fiscal_category_id': self.fiscal_category_sale.id
            })

        #Create Fiscal Position Rule for sale
        self.fiscal_position_rule_sale = self.env['account.fiscal.position.rule'].create({
            'name': 'Venda',
            'description': 'Venda',
            'company_id': self.env.ref('base.main_company').id,
            'from_country': self.env.ref('base.br').id,
            'fiscal_category_id': self.fiscal_category_sale.id,
            'fiscal_position_id': self.fiscal_position_sale.id,
            'use_sale': True,
            'use_invoice': True,
            'use_picking': True
            })

        #Create a customer invoice
        self.account_invoice_customer0 = self.env['account.invoice'].create({
            'payment_term': self.env.ref('account.account_payment_term_advance').id,
            'partner_id': self.env.ref('base.res_partner_3').id,
            'account_id': self.env['res.partner'].browse(self.env.ref('base.res_partner_3').id).property_account_receivable.id,
            'reference_type': 'none',
            'name': 'Test Customer Invoice',
            'invoice_line': {
                'product_id': self.env.ref('product.product_product_5').id,
                'quantity': 10.0}
            })

        ##setUp for PURCHASE##

        #Create a Fiscal Category for purchase
        self.fiscal_category_purchase = self.env['l10n_br_account.fiscal.category'].create({
            'code': 'Compras Teste',
            'name': 'Compras Teste',
            'type': 'input',
            'journal_type': 'purchase',
            'property_journal': self.env.ref('account.expenses_journal').id
            })

        #Create a Fiscal Position for purchase
        self.fiscal_position_purchase = self.env['account.fiscal.position'].create({
            'name': 'Compras Teste',
            'type': 'input',
            'company_id': self.env.ref('base.main_company').id,
            'fiscal_category_id': self.fiscal_category_purchase.id
            })

        #Create Fiscal Position Rule for purchase
        self.fiscal_position_rule_purchase = self.env['account.fiscal.position.rule'].create({
            'name': 'Compras',
            'description': 'Compras',
            'company_id': self.env.ref('base.main_company').id,
            'from_country': self.env.ref('base.br').id,
            'fiscal_category_id': self.fiscal_category_purchase.id,
            'fiscal_position_id': self.fiscal_position_purchase.id,
            'use_purchase': True,
            'use_invoice': True,
            'use_picking': True
            })

        #Create a supplier invoice
        self.account_invoice_supplier0 = self.env['account.invoice'].create({
            'payment_term': self.env.ref('account.account_payment_term_advance').id,
            'partner_id': self.env.ref('base.res_partner_3').id,
            'account_id': self.env['res.partner'].browse(self.env.ref('base.res_partner_3').id).property_account_receivable.id,
            'reference_type': 'none',
            'name': 'Test Supplier Invoice',
            'invoice_line': {
                'product_id': self.env.ref('product.product_product_5').id,
                'quantity': 10.0}
            })

    def test_customer_invoice_draft(self):
        """Test if Initially customer invoice is in the "Draft" state"""

        self.assertEqual(self.account_invoice_customer0.state, 'draft')

    def test_supplier_invoice_draft(self):
        """Test if Initially supplier invoice is in the "Draft" state"""

        self.assertEqual(self.account_invoice_supplier0.state, 'draft')
