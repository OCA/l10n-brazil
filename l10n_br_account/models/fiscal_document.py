# Copyright (C) 2020 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    @api.depends('line_ids')
    def _compute_move_template_ids(self):
        for record in self:
            record.move_template_ids = record.line_ids.mapped('move_template_id')

    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Account",
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain=[("deprecated", "=", False)],
        help="The partner account used for this document")

    move_template_ids = fields.Many2many(
        comodel_name='l10n_br_account.move.template',
        compute='_compute_move_template_ids',
        readonly=True)

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal')

    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Journal Entry',
        readonly=True,
        index=True,
        copy=False,
        help="Link to the automatically generated Journal Items.")

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        super(FiscalDocument, self)._onchange_fiscal_operation_id()
        if self.fiscal_operation_id.journal_id:
            self.journal_id = self.fiscal_operation_id.journal_id

    def _generate_financial_account_moves(self, move_lines):
        self.financial_ids.generate_move(move_lines)

    def _exec_after_SITUACAO_EDOC_AUTORIZADA(self, old_state, new_state):
        super(FiscalDocument, self)._exec_after_SITUACAO_EDOC_AUTORIZADA(
            old_state, new_state
        )
        if self.journal_id.generate_moves:
            self.action_move_create()

    @api.multi
    def action_move_create(self):
        for record in self:
            if not record.move_template_ids:
                continue

            if record.move_id:
                record.move_id.unlink()

            ctx = dict(self._context, lang=record.partner_id.lang)

            if not record.date:
                raise NotImplementedError

            move_lines = list()

            record._generate_financial_account_moves(move_lines)

            record.line_ids.generate_move(move_lines)

            ctx['company_id'] = record.company_id.id
            ctx['document'] = record
            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)

            vals = {
                'ref': 'ref',
                'line_ids': move_lines,
                'journal_id': record.journal_id.id,
                'date': record.date,
                'narration': 'narration',
            }

            move = self.env['account.move'].with_context(
                ctx_nolang).create(vals)
            move.post()
            vals = {
                'move_id': move.id,
                # 'date': record.date or inv.date_invoice,
                # 'move_name': move.name,
            }
            record.with_context(ctx).write(vals)
