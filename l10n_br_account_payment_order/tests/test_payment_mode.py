# @ 2021 KMEE - kmee.com.br
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import unittest

from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError


class TestPaymentMode(TransactionCase):

    def setUp(self):
        super().setUp()

        if not self.env['account.account'].search([]):
            raise unittest.SkipTest('No accounts defined')

        self.company = self.env.ref('base.main_company')
        self.journal_c1 = self.env['account.journal'].create({
            'name': 'Journal 1',
            'code': 'J1',
            'type': 'bank',
            'company_id': self.company.id,
        })

        self.account = self.env['account.account'].search([
            ('reconcile', '=', True),
            ('company_id', '=', self.company.id)
        ], limit=1)

        self.type_240 = self.env.ref(
            'l10n_br_account_payment_order.payment_mode_type_cnab240')

        self.type_400 = self.env.ref(
            'l10n_br_account_payment_order.payment_mode_type_cnab400')

        self.type_500 = self.env.ref(
            'l10n_br_account_payment_order.payment_mode_type_cnab500')

        self.payment_mode_test_240 = self.env['account.payment.mode'].create({
            'name': 'Banco Teste 240',
            'bank_account_link': 'fixed',
            'payment_method_id': self.type_240.id,
            'company_id': self.company.id,
            'fixed_journal_id': self.journal_c1.id,
            'group_lines': False,
            'generate_move': False,
            'post_move': False,
        })

        self.payment_mode_test_400 = self.env['account.payment.mode'].create({
            'name': 'Banco Teste 400',
            'bank_account_link': 'fixed',
            'payment_method_id': self.type_400.id,
            'company_id': self.company.id,
            'fixed_journal_id': self.journal_c1.id,
            'group_lines': False,
            'generate_move': False,
            'post_move': False,

        })

        self.payment_mode_test_500 = self.env['account.payment.mode'].create({
            'name': 'Banco Teste 500',
            'bank_account_link': 'fixed',
            'payment_method_id': self.type_500.id,
            'company_id': self.company.id,
            'fixed_journal_id': self.journal_c1.id,
            'group_lines': False,
            'generate_move': False,
            'post_move': False,
        })

    def test_constrains(self):
        with self.assertRaises(ValidationError):
            self.payment_mode_test_240.write({
                'group_lines': True,
            })
        with self.assertRaises(ValidationError):
            self.payment_mode_test_240.write({
                'generate_move': True,
            })
        with self.assertRaises(ValidationError):
            self.payment_mode_test_240.write({
                'post_move': True,
            })
