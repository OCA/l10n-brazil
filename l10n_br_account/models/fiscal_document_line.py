# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    # the following fields collide with account.invoice.line fields so we use
    # related field alias to be able to write them through account.invoice.line
    fiscal_doc_line_name = fields.Text(
        related="name",
        string="Fiscal Doc Name",
        readonly=False)

    fiscal_doc_line_partner_id = fields.Many2one(
        related="partner_id",
        string="Fiscal Doc Partner",
        readonly=False)

    fiscal_doc_line_company_id = fields.Many2one(
        related="company_id",
        string="Fiscal Doc Company",
        readonly=False)

    fiscal_doc_line_currency_id = fields.Many2one(
        related="currency_id",
        string="Fiscal Doc Currency",
        readonly=False)

    fiscal_doc_line_product_id = fields.Many2one(
        related="product_id",
        string="Fiscal Doc Product",
        readonly=False)

    fiscal_doc_line_uom_id = fields.Many2one(
        related="uom_id",
        string="Fiscal Doc UOM",
        readonly=False)

    fiscal_doc_line_quantity = fields.Float(
        related="quantity",
        string="Fiscal Doc Quantity",
        readonly=False)

    fiscal_doc_line_price_unit = fields.Float(
        related="price_unit",
        string="Fiscal Doc Price Unit",
        readonly=False)

    fiscal_doc_line_discount = fields.Monetary(
        related="discount_value",
        string="Fiscal Doc  Discount Value",
        readonly=False)

    move_template_id = fields.Many2one(
        comodel_name='l10n_br_account.move.template',
        string='Move Template',
        related='operation_line_id.move_template_id',
        readonly=True,
    )

    def generate_double_entrie(self, lines, value, template_line):

        if template_line.account_debit_id:
            data = {
                # 'invl_id': self.id,  # FIXME
                'name': self.name.split('\n')[0][:64],
                'narration': template_line.history_id.history,
                'debit': value,
                'currency_id':
                    self.currency_id and self.currency_id.id or False,
                'partner_id': self.partner_id and self.partner_id.id or False,
                'account_id': template_line.account_debit_id.id,
                'product_id': self.product_id and self.product_id.id or False,
                'quantity': self.quantity or 0,
                'product_uom_id': self.uom_id and self.uom_id.id or False,
            }
            lines.append((0, 0, data))

        if template_line.account_credit_id:
            data = {
                # 'invl_id': self.id,  # FIXME
                'name': self.name.split('\n')[0][:64],
                'narration': template_line.history_id.history,
                'credit': value,
                'currency_id':
                    self.currency_id and self.currency_id.id or False,
                'partner_id': self.partner_id and self.partner_id.id or False,
                'account_id': template_line.account_credit_id.id,
                'product_id': self.product_id and self.product_id.id or False,
                'quantity': self.quantity or 0,
                'product_uom_id': self.uom_id and self.uom_id.id or False,
            }
            lines.append((0, 0, data))
