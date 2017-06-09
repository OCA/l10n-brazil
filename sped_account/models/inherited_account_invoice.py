# -*- coding: utf-8 -*-
#
# Copyright 2016 KMEE
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.addons.sped_imposto.models.sped_calculo_imposto import (
    SpedCalculoImposto
)


class AccountInvoice(SpedCalculoImposto, models.Model):
    _inherit = 'account.invoice'

    sped_documento_ids = fields.Many2one(
        comodel_name='sped.documento',
        inverse_name='invoice_id',
        string=u'Documentos Fiscais',
    )
    order_line = fields.One2many(
        #
        # Workarrond para termos os mesmos campos nos outros objetos
        #
        'account.invoice.line',
        related='invoice_line_ids',
        string='Order Lines',
        readonly=True,
    )

    def _get_date(self):
        """
        Return the document date
        Used in _amount_all_wrapper
        """
        date = super(AccountInvoice, self)._get_date()
        if self.date_invoice:
            return self.date_invoice
        return date

    @api.one
    @api.depends(
        'invoice_line_ids.price_subtotal',
        'tax_line_ids.amount',
        'currency_id',
        'company_id',
        'date_invoice',
        'type',
        #
        # Brasil
        #
        'invoice_line_ids.vr_nf',
        'invoice_line_ids.vr_fatura',
    )
    def _compute_amount(self):
        if not self.is_brazilian:
            return super(AccountInvoice, self)._compute_amount()
        return self._amount_all_brazil()

    @api.model
    def create(self, dados):
        invoice = super(AccountInvoice, self).create(dados)
        return invoice

    @api.multi
    def action_move_create(self):
        for invoice in self:
            if not invoice.is_brazilian:
                super(AccountInvoice, self).action_move_create()
                continue
                # invoice.sped_documento_id.account_move_create()
        return True
