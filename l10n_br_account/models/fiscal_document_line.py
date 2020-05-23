# Copyright (C) 2020 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    move_template_id = fields.Many2one(
        comodel_name='l10n_br_account.move.template',
        string='Move Template',
        related='fiscal_operation_line_id.move_template_id',
        readonly=True,
    )

    def _comment_vals(self):
        return {
            'user': self.env.user,
            'ctx': self._context,
            'doc': self,
        }

    def generate_move(self, move_lines):
        for record in self:
            record.move_template_id.generate_move(obj=record, move_lines=move_lines)

    def generate_double_entrie(self, move_lines, value, template_line):

        history = template_line.history_id.compute_message(self._comment_vals())

        if template_line.account_debit_id:
            data = {
                # 'invl_id': self.id,  # FIXME
                # 'name': self.name.split('\n')[0][:64],
                # 'narration': template_line.history_id.history,
                'name': history or '/',
                'debit': value,
                'currency_id':
                    self.currency_id and self.currency_id.id or False,
                'partner_id': self.partner_id and self.partner_id.id or False,
                'account_id': template_line.account_debit_id.id,
                'product_id': self.product_id and self.product_id.id or False,
                'quantity': self.quantity or 0,
                'product_uom_id': self.uom_id and self.uom_id.id or False,
            }
            move_lines.append((0, 0, data))

        if template_line.account_credit_id:
            data = {
                # 'invl_id': self.id,  # FIXME
                'name': history or '/',
                # 'narration': template_line.history_id.history,
                'credit': value,
                'currency_id':
                    self.currency_id and self.currency_id.id or False,
                'partner_id': self.partner_id and self.partner_id.id or False,
                'account_id': template_line.account_credit_id.id,
                'product_id': self.product_id and self.product_id.id or False,
                'quantity': self.quantity or 0,
                'product_uom_id': self.uom_id and self.uom_id.id or False,
            }
            move_lines.append((0, 0, data))
