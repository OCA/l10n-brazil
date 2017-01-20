# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Luis Felipe Miléo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class SpedDocumento(models.Model):

    _inherit = 'sped.documento'


class SpedDocumentoItem(models.Model):

    _inherit = 'sped.documento.item'

    invoice_line_ids = fields.Many2many(
        'account.invoice.line',
        'account_invoice_line_sped_documento_rel',
        'sped_documento_item_id', 'invoice_line_id',
        string='Sale Order Lines', readonly=True, copy=False
    )
