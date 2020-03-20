# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# Copyright (C) 2020 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    @api.depends('line_ids')
    def _compute_move_template_ids(self):
        for record in self:
            record.move_template_ids = record.line_ids.mapped('move_template_id')

    # the following fields collide with account.invoice fields so we use
    # related field alias to be able to write them through account.invoice
    fiscal_doc_partner_id = fields.Many2one(
        related="partner_id",
        string="Fiscal Doc Partner",
        readonly=False)

    fiscal_doc_date = fields.Datetime(
        related="date",
        string="Fiscal Doc Date",
        readonly=False)

    fiscal_doc_company_id = fields.Many2one(
        related="company_id",
        string="Fiscal Doc Company",
        readonly=False)

    fiscal_doc_currency_id = fields.Many2one(
        related="currency_id",
        string="Fiscal Doc Currency",
        readonly=False)

    fiscal_doc_state = fields.Selection(
        related="state",
        string="Fiscal Doc State",
        readonly=False)

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

            lines = []

            for line in record.line_ids:
                line.move_template_id.generate_move(line, lines)

            ctx['company_id'] = record.company_id.id
            ctx['document'] = record
            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)

            vals = {
                'ref': 'ref',
                'line_ids': lines,
                'journal_id': record.journal_id.id,
                'date': record.date,
                'narration': 'narration',
            }

            move = self.env['account.move'].with_context(
                ctx_nolang).create(vals)
            # move.post()
            vals = {
                'move_id': move.id,
                # 'date': record.date or inv.date_invoice,
                # 'move_name': move.name,
            }
            record.with_context(ctx).write(vals)
