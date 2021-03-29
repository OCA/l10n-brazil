# @ 2021 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import time

from odoo.tests import tagged
from odoo.tests import SavepointCase
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestPaymentOrder(SavepointCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

        self.register_payments_model = \
            self.env['account.register.payments'].with_context(
                active_model='account.invoice')
        self.payment_model = self.env['account.payment']
        self.aml_cnab_change_model = self.env['account.move.line.cnab.change']

        # Get Invoice for test
        self.invoice_unicred = self.env.ref(
            'l10n_br_account_payment_order.'
            'demo_invoice_payment_order_unicred_cnab400'
        )
        self.invoice_cef = self.env.ref(
            'l10n_br_account_payment_order.'
            'demo_invoice_payment_order_cef_cnab240'
        )
        # I validate invoice by creating on
        self.invoice_cef.action_invoice_open()

        payment_order = self.env['account.payment.order'].search([
            ('payment_mode_id', '=', self.invoice_cef.payment_mode_id.id)
        ])
        # Open payment order
        payment_order.draft2open()
        # Generate and upload
        payment_order.open2generated()
        payment_order.generated2uploaded()

        # Journal
        self.journal_cash = self.env[
            'account.journal'].search([
            ('type', '=', 'cash'),
        ], limit=1)
        self.payment_method_manual_in = \
            self.env.ref('account.account_payment_method_manual_in')

    def test_create_payment_order_with_brcobranca(self):
        """ Test Create Payment Order with BRCobranca."""

        # I validate invoice by creating on
        self.invoice_unicred.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEquals(self.invoice_unicred.state, 'open')

        # Geração do Boleto
        self.invoice_unicred.view_boleto_pdf()

        payment_order = self.env['account.payment.order'].search([
            ('payment_mode_id', '=', self.invoice_unicred.payment_mode_id.id)
        ])

        bank_journal = self.env.ref(
            'l10n_br_account_payment_order.unicred_journal')

        payment_order.write({
            'journal_id': bank_journal.id
        })

        self.assertEquals(len(payment_order.payment_line_ids), 2)
        self.assertEquals(len(payment_order.bank_line_ids), 0)

        # Open payment order
        payment_order.draft2open()

        # Criação da Bank Line
        self.assertEquals(len(payment_order.bank_line_ids), 2)

        # Generate and upload
        payment_order.open2generated()
        payment_order.generated2uploaded()
        self.assertEquals(payment_order.state, 'done')

        # Ordem de Pagto CNAB não pode ser apagada
        with self.assertRaises(UserError):
             payment_order.unlink()

        # Ordem de Pagto CNAB não pode ser Cancelada
        with self.assertRaises(UserError):
            payment_order.action_done_cancel()

        # Testar Cancelamento
        self.invoice_cef.action_invoice_cancel()

    def test_payment_outside_cnab_writeoff_and_change_tittle_value(self):
        """
         Caso de Pagamento com CNAB já iniciado sendo necessário fazer a Baixa
         de uma Parcela e a Alteração de Valor de Titulo por pagto parcial.
        """

        ctx = {
            'active_model': 'account.invoice',
            'active_ids': [self.invoice_cef.id]
        }
        register_payments = \
            self.register_payments_model.with_context(ctx).create({
                'payment_date': time.strftime('%Y') + '-07-15',
                'journal_id': self.journal_cash.id,
                'payment_method_id': self.payment_method_manual_in.id,
                'amount': 600.0
            })

        register_payments.create_payments()
        # Ordem de PAgto com alterações
        payment_order = self.env['account.payment.order'].search([
            ('payment_mode_id', '=', self.invoice_cef.payment_mode_id.id),
            ('state', '=', 'draft')
        ])
        for l in payment_order.payment_line_ids:
            if l.amount_currency == 300:
                # Caso de Baixa do Titulo
                self.assertEquals(
                    l.mov_instruction_code_id.name,
                    l.order_id.payment_mode_id.cnab_write_off_code_id.name)
            else:
                # Caso de alteração do valor do titulo por pagamento parcial
                self.assertEquals(
                    l.mov_instruction_code_id.name,
                    l.order_id.payment_mode_id.
                        cnab_code_change_title_value_id.name)
                self.assertEquals(
                    l.move_line_id.amount_residual,
                    l.amount_currency)

    def test_cnab_change_methods(self):
        """
        Test CNAB Change Methods
        """
        aml_to_change = self.invoice_cef.financial_move_line_ids[0]
        ctx = {
            'active_model': 'account.move.line',
            'active_ids': [aml_to_change.id]
        }
        dict_change_due_date = {
            'change_type': 'change_date_maturity',
        }
        aml_cnab_change = \
            self.aml_cnab_change_model.with_context(ctx).create(
                dict_change_due_date)
        # Teste alteração com a mesma data não permitido
        with self.assertRaises(UserError):
            aml_cnab_change.doit()
        dict_change_due_date.update({
            'date_maturity': time.strftime('%Y') + '-07-15'
        })
        aml_cnab_change = \
            self.aml_cnab_change_model.with_context(ctx).create(
                dict_change_due_date)
        aml_cnab_change.doit()
        payment_order = self.env['account.payment.order'].search([
            ('payment_mode_id', '=', self.invoice_cef.payment_mode_id.id),
            ('state', '=', 'draft')
        ])
        for l in payment_order.payment_line_ids:
            self.assertEquals(
                l.mov_instruction_code_id.name,
                l.order_id.payment_mode_id.
                    cnab_code_change_maturity_date_id.name)

        # Open payment order
        payment_order.draft2open()
        # Generate and upload
        payment_order.open2generated()
        payment_order.generated2uploaded()
        self.assertEquals(payment_order.state, 'done')

        # Protesto
        aml_cnab_change = \
            self.aml_cnab_change_model.with_context(ctx).create({
                'change_type': 'protest_tittle'
            })
        aml_cnab_change.doit()
        payment_order = self.env['account.payment.order'].search([
            ('payment_mode_id', '=', self.invoice_cef.payment_mode_id.id),
            ('state', '=', 'draft')
        ])
        for l in payment_order.payment_line_ids:
            self.assertEquals(
                l.mov_instruction_code_id.name,
                l.order_id.payment_mode_id.cnab_code_protest_title_id.name)
        # Open payment order
        payment_order.draft2open()
        # Generate and upload
        payment_order.open2generated()
        payment_order.generated2uploaded()
        self.assertEquals(payment_order.state, 'done')

        # Suspender Protesto e manter em carteira
        aml_cnab_change = \
            self.aml_cnab_change_model.with_context(ctx).create({
                'change_type': 'suspend_protest_keep_wallet',
            })
        aml_cnab_change.doit()
        payment_order = self.env['account.payment.order'].search([
            ('payment_mode_id', '=', self.invoice_cef.payment_mode_id.id),
            ('state', '=', 'draft')
        ])
        for l in payment_order.payment_line_ids:
            self.assertEquals(
                l.mov_instruction_code_id.name,
                l.order_id.payment_mode_id.
                    cnab_code_suspend_protest_keep_wallet_id.name)
        # Open payment order
        payment_order.draft2open()
        # Generate and upload
        payment_order.open2generated()
        payment_order.generated2uploaded()
        self.assertEquals(payment_order.state, 'done')

        # Caso Conceder Abatimento
        aml_cnab_change = \
            self.aml_cnab_change_model.with_context(ctx).create({
                'change_type': 'grant_rebate',
                'rebate_value': 10.0,
            })
        aml_cnab_change.doit()
        payment_order = self.env['account.payment.order'].search([
            ('payment_mode_id', '=', self.invoice_cef.payment_mode_id.id),
            ('state', '=', 'draft')
        ])
        for l in payment_order.payment_line_ids:
            self.assertEquals(
                l.mov_instruction_code_id.name,
                l.order_id.payment_mode_id.
                    cnab_code_grant_rebate_id.name)
            self.assertEquals(l.rebate_value, 10.0)

        # Open payment order
        payment_order.draft2open()
        for l in payment_order.bank_line_ids:
            self.assertEquals(
                l.mov_instruction_code_id.name,
                l.order_id.payment_mode_id.
                    cnab_code_grant_rebate_id.name)
            self.assertEquals(l.rebate_value, 10.0)
        # Generate and upload
        payment_order.open2generated()
        payment_order.generated2uploaded()
        self.assertEquals(payment_order.state, 'done')

        # Caso Cancelar Abatimento
        aml_cnab_change = \
            self.aml_cnab_change_model.with_context(ctx).create({
                'change_type': 'cancel_rebate'
            })
        aml_cnab_change.doit()
        payment_order = self.env['account.payment.order'].search([
            ('payment_mode_id', '=', self.invoice_cef.payment_mode_id.id),
            ('state', '=', 'draft')
        ])
        for l in payment_order.payment_line_ids:
            self.assertEquals(
                l.mov_instruction_code_id.name,
                l.order_id.payment_mode_id.
                    cnab_code_cancel_rebate_id.name)

        # Open payment order
        payment_order.draft2open()
        # Generate and upload
        payment_order.open2generated()
        payment_order.generated2uploaded()
        self.assertEquals(payment_order.state, 'done')

        # Caso Conceder Desconto
        aml_cnab_change = \
            self.aml_cnab_change_model.with_context(ctx).create({
                    'change_type': 'grant_discount',
                    'discount_value': 10.0,
            })
        aml_cnab_change.doit()
        payment_order = self.env['account.payment.order'].search([
            ('payment_mode_id', '=', self.invoice_cef.payment_mode_id.id),
            ('state', '=', 'draft')
        ])
        for l in payment_order.payment_line_ids:
            self.assertEquals(
                l.mov_instruction_code_id.name,
                l.order_id.payment_mode_id.
                    cnab_code_grant_discount_id.name)
            self.assertEquals(l.discount_value, 10.0)

        # Open payment order
        payment_order.draft2open()
        for l in payment_order.bank_line_ids:
            self.assertEquals(
                l.mov_instruction_code_id.name,
                l.order_id.payment_mode_id.
                    cnab_code_grant_discount_id.name)
            self.assertEquals(l.discount_value, 10.0)
        # Generate and upload
        payment_order.open2generated()
        payment_order.generated2uploaded()
        self.assertEquals(payment_order.state, 'done')

        # Caso Cancelar discount
        aml_cnab_change = \
            self.aml_cnab_change_model.with_context(ctx).create({
                'change_type': 'cancel_discount'
            })
        aml_cnab_change.doit()
        payment_order = self.env['account.payment.order'].search([
            ('payment_mode_id', '=', self.invoice_cef.payment_mode_id.id),
            ('state', '=', 'draft')
        ])
        for l in payment_order.payment_line_ids:
            self.assertEquals(
                l.mov_instruction_code_id.name,
                l.order_id.payment_mode_id.
                    cnab_code_cancel_discount_id.name)

        # Open payment order
        payment_order.draft2open()
        # Generate and upload
        payment_order.open2generated()
        payment_order.generated2uploaded()
        self.assertEquals(payment_order.state, 'done')

        # Suspender Protesto e dar Baixa
        # TODO: Especificar melhor esse caso

    def test_cnab_change_method_not_payment(self):
        """
        Test CNAB Change Method Not Payment
        """
        aml_to_change = self.invoice_cef.financial_move_line_ids[0]
        ctx = {
            'active_model': 'account.move.line',
            'active_ids': [aml_to_change.id]
        }
        aml_cnab_change = \
            self.aml_cnab_change_model.with_context(ctx).create({
                'change_type': 'not_payment'
            })
        aml_cnab_change.doit()
        self.assertEquals(aml_to_change.payment_situation, 'nao_pagamento')
        self.assertEquals(aml_to_change.cnab_state, 'done')
        self.assertEquals(aml_to_change.reconciled, True)
