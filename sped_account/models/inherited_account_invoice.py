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
    brazil_line_ids = fields.One2many(
        comodel_name='account.invoice.line.brazil',
        inverse_name='invoice_id',
        string='Linhas da Fatura',
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
        'invoice_line_ids.brazil_line_id.vr_nf',
        'invoice_line_ids.brazil_line_id.vr_fatura',
    )
    def _compute_amount(self):
        if not self.is_brazilian:
            return super(AccountInvoice, self)._compute_amount()
        return self._amount_all_brazil()

    @api.model
    def create(self, dados):
        invoice = super(AccountInvoice, self).create(dados)
        return invoice

    # @api.model
    # def write(self, dados):
    #     self._check_brazilian_invoice('write')
    #     res = super(AccountInvoice, self).write(dados)
    #     return res
    #
    # @api.model
    # def unlink(self):
    #     self._check_brazilian_invoice('unlink')
    #     res = super(AccountInvoice, self).unlink()
    #     return res

    @api.multi
    def action_move_create(self):
        for invoice in self:
            if not invoice.is_brazilian:
                super(AccountInvoice, self).action_move_create()
                continue

                # invoice.sped_documento_id.account_move_create()

        return True

        # @api.multi
        # def compute_taxes(self):
        # for invoice in self:
        # if not invoice.is_brazilian:
        # super(AccountInvoice, self).compute_taxes()
        # continue

        ##
        # Fazemos aqui a sincronia entre os impostos do sped_documento e o
        # account_invoice_tax
        ##
        # account_tax = self.env['account.tax']
        # account_invoice_tax = self.env['account.invoice.tax']

        # ctx = dict(self._context)
        # for invoice in self:
        # Delete non-manual tax lines
        # self._cr.execute("DELETE FROM account_invoice_tax WHERE
        # invoice_id=%s AND manual is False", (invoice.id,))
        # self.invalidate_cache()

        # Generate one tax line per tax, however many invoice
        # lines it's applied to
        # tax_grouped = invoice.get_taxes_values()

        # Create new tax lines
        # for tax in tax_grouped.values():
        # account_invoice_tax.create(tax)

        # dummy write on self to trigger recomputations
        # return self.with_context(ctx).write({'invoice_line_ids': []})

        # @api.multi
        # def get_taxes_values(self):
        # tax_grouped = {}
        # for line in self.invoice_line_ids:
        # price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        # taxes = line.invoice_line_tax_ids.compute_all(price_unit,
        # self.currency_id, line.quantity, line.product_id,
        #  self.partner_id)['taxes']
        # for tax in taxes:
        # val = self._prepare_tax_line_vals(line, tax)
        # key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

        # if key not in tax_grouped:
        # tax_grouped[key] = val
        # else:
        # tax_grouped[key]['amount'] += val['amount']
        # tax_grouped[key]['base'] += val['base']
        # return tax_grouped
