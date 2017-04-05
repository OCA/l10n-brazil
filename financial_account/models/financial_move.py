# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

FINANCIAL_TYPE_AML = {
    'receivable': {
        'debit': 'r',
        'credit': 'rr',
    },
    'payable': {
        'credit': 'p',
        'debit': 'rr',
    }
}


INTERNAL_TYPE_TO_SYNC = (
    'receivable',
    'payable'
)


class FinancialMove(models.Model):

    _inherit = 'financial.move'

    @api.multi
    @api.depends('financial_account_move_line_id')
    def _compute_payment_receivable_ids(self):
        for record in self:
            ids = []
            aml = record.financial_account_move_line_id
            ids.extend([r.debit_move_id.id for r in
                        aml.matched_debit_ids] if
                       aml.credit > 0 else [r.credit_move_id.id for r in
                                            aml.matched_credit_ids])
            record.payment_receivable_ids = ids
            record.payment_receivable_ids |= \
                record.financial_account_move_line_id

    move_id = fields.Many2one(
        comodel_name='account.move',
        string=u'Journal Entry',
        readonly=True,
        index=True,
        ondelete='restrict',
        copy=False,
        help="Link to the automatically generated Journal Items."
    )
    financial_account_move_line_id = fields.Many2one(
        comodel_name='account.move.line',
        string=u'Financial account move line'
    )
    payment_receivable_ids = fields.One2many(
        comodel_name='account.move.line',
        compute='_compute_payment_receivable_ids',
    )

    def _create_account_move(self, move_vals):
        account_move = self.env['account.move']
        ctx = dict(self._context)
        ctx['company_id'] = self.company_id.id
        ctx['financial_move'] = self
        ctx_nolang = ctx.copy()
        ctx_nolang.pop('lang', None)
        move = account_move.with_context(ctx_nolang).create(move_vals)
        self.move_id = move.id
        return move

    @api.multi
    def finalize_move_vals(self, move_vals):
        return move_vals

    def _prepare_move_lines(self):
        # TODO: Criar os itens dos lançamentos
        # TODO: Possibilitar efetuar os lançamentos em
        #  - regime de competencia
        #  - regime de caixa

        # # partner_id = self.account_id =
        # self.partner_id.property_account_receivable_id \
        # # if self.voucher_type == 'sale' else
        # # self.partner_id.property_account_payable_id
        # credit = 0
        # debit = 0
        # if(self.move_type == 'receivable'):
        #     debit = self.amount_document
        # else:
        #     credit = self.amount_document
        # return dict(  # FIXME: change to account parameters
        #     name=self.display_name,
        #     date_maturity=self.date_due,
        #     date=self.document_date,
        #     company_id=self.company_id and self.company_id.id,
        #     currency_id=self.currency_id and self.currency_id.id,
        #     debit=debit,
        #     credit=credit,
        #     partner_id=self.partner_id and self.partner_id.id or False,
        #     internal_type=self.move_type,
        #     move_id=self.move_id,
        #     financial_move_id=self.id,
        #     account_id=self.account_id,
        # )
        return []

    def _prepare_move_vals(self):
        if self._context.get('move_vals'):
            return self.finalize_move_vals(self._context.get('move_vals'))
        move_vals = {
            'ref': self.document_number,
            'line_ids': self._prepare_move_lines(),
            'journal_id': self.bank_id.journal_id.id,
            'date': self.date,
            'narration': self.note or '',
        }
        return self.finalize_move_vals(move_vals)

    @api.multi
    def action_move_create(self):
        account_move = self.env['account.move']
        for record in self:
            ctx = dict(self._context, lang=record.partner_id.lang)
            if record.move_id:
                # Verificar se os dados coincidem ?
                # Calcular uma hash?
                # Se não coincidir recriar se possível.
                # Manipular o contexto?
                continue
            move_vals = record.with_context(ctx)._prepare_move_vals()
            account_move |= record.with_context(
                ctx)._create_account_move(move_vals)
        return account_move

    def _confirm(self):
        to_confirm = self.filtered(lambda f: f.state in 'draft')
        super(FinancialMove, to_confirm).action_confirm()
        self.action_move_create()

    @api.multi
    def action_confirm(self):
        self._confirm()
        # self.action_move_post()
        for record in self.filtered(
                lambda f: f.move_id and f.move_id.state == 'draft'):
            record.move_id.post()
    #
    # Sincronização dos lançamentos contábeis com os financeiros
    #

    def sync_financial_account(self, move_ids):
        moves_to_sync = move_ids.filtered(
            lambda m: m.journal_id.financial_integration)
        move_lines_to_sync = moves_to_sync.line_ids.filtered(
            lambda l: not l.financial_move_ids)
        self.sync_financial_aml(move_lines_to_sync)

    def sync_financial_aml(self, aml):
        for record in aml.filtered(
                lambda r: r.account_id.internal_type in INTERNAL_TYPE_TO_SYNC):
            # only in this cases?
            self.create(self._prepare_from_move(record))

    @staticmethod
    def _prepare_from_move(aml):
        financial_type = FINANCIAL_TYPE_AML[aml.account_id.internal_type]
        financial_type = (
            aml.credit and financial_type['credit'] or
            aml.debit and financial_type['debit']
        )
        return dict(
            date_maturity=aml.date_maturity,
            company_id=(aml.company_id and aml.company_id.id or
                        aml.account_id.company_id and
                        aml.account_id.company_id.id),
            currency_id=(aml.currency_id and aml.currency_id.id or
                         aml.move_id.currency_id and
                         aml.move_id.currency_id.id),
            amount=aml.debit or aml.credit,
            partner_id=aml.partner_id and aml.partner_id.id or False,
            date=aml.date_maturity,
            document_number='/',
            financial_type=financial_type,
            move_id=aml.move_id and aml.move_id.id,
            financial_account_move_line_id=aml.id,
            account_id=aml.account_id.id,
        )

    # def post_account_move(self, name):
    #     self.write({'document_number': name})
    #     self.action_confirm()
    #
    #
    # def _get_document_info(self):
    #     # Some day we can have another documents linked to financials,
    #     # like so / po that are in the budget but dont't have a invoice
    #     return 'account.invoice', \
    #            [x.financial_account_move_line_id.invoice_id.id for x in self]
    #
    # def _create_account_payment(
    #         self, financial_payment_id, amount, bank_id, date):
    #
    #     model, document_ids = self.browse(
    #         financial_payment_id)._get_document_info()
    #
    #     if not document_ids:
    #         return
    #     self.register_payments_model = self.env['account.register.payments']
    #
    #     ctx = {
    #         'active_model': model,
    #         'active_ids': document_ids
    #     }
    #     register_payments = self.register_payments_model.with_context(
    #         ctx
    #     ).create({
    #         'payment_date': date,
    #         'journal_id':
    #             self.env['res.partner.bank'].browse(bank_id).journal_id.id,
    #         'payment_method_id':
    #             self.env.ref('account.account_payment_method_manual_in').id,
    #         'amount': amount,
    #     })
    #
    #     register_payments.create_payment()
