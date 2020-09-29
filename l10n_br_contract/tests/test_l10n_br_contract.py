# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import TransactionCase


class TestL10nBrContract(TransactionCase):
    def setUp(self):
        super(TestL10nBrContract, self).setUp()

        self.today = fields.Date.today()
        self.partner = self.env.ref('base.res_partner_2')
        self.product = self.env.ref('product.product_product_3')

        self.contract = self.env['contract.contract'].create(
            {
                'name': 'Test Contract',
                'partner_id': self.partner.id,
                'contract_type': 'sale',
                'contract_line_ids': [
                    (
                        0,
                        0,
                        {
                            'product_id': self.product.id,
                            'name': 'Desk Combination',
                            'quantity': 1,
                            'uom_id': self.product.uom_id.id,
                            'recurring_rule_type': 'monthly',
                            'recurring_interval': 1,
                            'date_start': '2020-09-29',
                            'recurring_next_date': '2020-10-29',
                        },
                    )
                ],
            }
        )

    def test_create_document(self):
        self.contract.recurring_create_invoice()
        for invoice in self.contract._get_related_invoices():
            document_id = invoice.fiscal_document_id

            self.assertTrue(document_id, 'Fiscal Document was not created for'
                                         ' Contract Invoice')

            self.assertEqual(self.contract.partner_id.id,
                             document_id.partner_id.id,
                             'Fiscal Document Created with different Partner')

            self.assertEqual(len(document_id.line_ids), 1,
                             'Fiscal Document created with different number '
                             'of products')

            self.assertEqual(self.product.id,
                             document_id.line_ids[0].product_id.id,
                             'Fiscal Document created with different product')
