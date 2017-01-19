# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    sped_documento_lines = fields.Many2many(
        'sped.documento.item',
        'account_invoice_line_sped_documento_rel',
        'invoice_line_id',
        'sped_documento_item_id',
        string='Sped documento itens',
        copy=False)
