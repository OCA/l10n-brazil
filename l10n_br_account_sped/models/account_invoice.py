# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    state = fields.Selection(
        selection_add=[('to_br_invoice', u'Faturamento')],
    )

    @api.multi
    def action_sped_document(self):
        documento = self.env['sped.documento']
        documento.create({
            'empresa_id': 1,
            # invoice.company_id.partner_id.sped_participante_id
            'participante_id': 2,  # invoice.partner_id.sped_participante_id
            'emissao': '0',  # Dados da posição fiscal / operação fical
            'modelo': '55',  # Dados da posição fiscal / operação fical
        })

    @api.multi
    def action_sped_documento(self):
        for invoice in self:
            invoice.action_sped_document()
        return self.write({'state': 'to_br_invoice'})

    @api.multi
    def action_invoice_open(self):
        to_open_br_invoices = self.filtered(
            lambda inv: inv.state != 'open' and
            inv.company_id.country_id == self.env.ref('base.br'))
        to_open_not_br_invoices = self.filtered(
            lambda inv: inv.state != 'open' and
            not inv.company_id.country_id == self.env.ref('base.br')
        )
        to_open_br_invoices.action_sped_documento()
        return super(
            AccountInvoice, to_open_not_br_invoices).action_invoice_open()


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    sped_documento_lines = fields.Many2many(
        'sped.documento.item',
        'account_invoice_line_sped_documento_rel',
        'invoice_line_id',
        'sped_documento_item_id',
        string='Sped documento itens',
        copy=False)
