

import openerp.tests.common as common
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp import workflow, exceptions


def create_simple_invoice(self):
    partner_id = self.ref('base.res_partner_2')
    product_id = self.ref('product.product_product_4')
    today = datetime.now()
    journal_id = self.ref('account.sales_journal')
    date = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
    return self.env['account.invoice']\
        .create({'partner_id': partner_id,
                 'account_id':
                 self.ref('account.a_recv'),
                 'journal_id':
                 journal_id,
                 'date_invoice': date,
                 'invoice_line': [(0, 0, {'name': 'test',
                                          'account_id':
                                          self.ref('account.a_sale'),
                                          'price_unit': 2000.00,
                                          'quantity': 1,
                                          'product_id': product_id,
                                          }
                                   )
                                  ],
                 })




def create_payment_order(self):
    mode = self.ref('account_payment.payment_mode_1')
    today = datetime.now()
    journal_id = self.ref('account.sales_journal')
    date = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
    return self.env['payment.order'].create({
        'reference': '1992/08',
        'mode': mode,
        'date_prefered': "due"
             })


class TestItau240(common.TransactionCase):

    # def test_draft_move_invoice(self):
    #         invoice = create_simple_invoice(self)
    #         workflow.trg_validate(self.uid, 'account.invoice', invoice.id,
    #                               'invoice_open', self.cr)
    #         self.assertEqual(invoice.move_id.state, 'posted',
    # 'State error!')

    def test_create_payment_order(self):
        payment_order = create_payment_order(self)
        self.assertEqual(payment_order.reference, '1992/08',
                         'Payment Order creation Error')
