# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    sped_documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string=u'Documento Fiscal',
        ondelete='cascade',
    )
    is_brazilian_invoice = fields.Boolean(
        string=u'Is a Brazilian Invoice?',
        compute='_compute_is_brazilian_invoice',
    )
    sped_empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
    )
    sped_operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string=u'Operação',
    )
    sped_participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string=u'Destinatário/Remetente'
    )

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.ensure_one()
        if self.is_brazilian_invoice:
            self.sped_empresa_id = self.company_id.sped_empresa_id

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.ensure_one()
        if self.is_brazilian_invoice:
            if self.sped_participante_id:
                self.sped_participante_id = \
                    self.partner_id.sped_participante_id

    @api.onchange('sped_participante_id')
    def onchange_sped_participante_id(self):
        self.ensure_one()
        self.partner_id = self.sped_participante_id.partner_id

    @api.onchange('sped_empresa_id')
    def onchange_sped_empresa_id(self):
        self.ensure_one()
        self.company_id = self.sped_empresa_id.company_id

    @api.multi
    @api.depends('sped_documento_id', 'company_id')
    def _compute_is_brazilian_invoice(self):
        for invoice in self:
            if self.sped_documento_id:
                invoice.is_brazilian_invoice = True
                continue

            if invoice.company_id.country_id:
                if invoice.company_id.country_id.id == \
                        self.env.ref('base.br').id:
                    invoice.is_brazilian_invoice = True
                    continue

            self.is_brazilian_invoice = False

    @api.multi
    def _check_brazilian_invoice(self, operation):
        pass
        # for invoice in self:
        # if (invoice.is_brazilian_invoice
        # and 'sped_documento_id' not in self._context):
        # if operation == 'create':
        # raise ValidationError('This is a Brazilian Invoice!
        # You should create it through the proper Brazilian Fiscal Document!')
        # elif operation == 'write':
        # raise ValidationError('This is a Brazilian Invoice!
        #  You should change it through the proper Brazilian Fiscal Document!')
        # elif operation == 'unlink':
        # raise ValidationError('This is a Brazilian Invoice!
        # You should delete it through the proper Brazilian Fiscal Document!')

    @api.model
    def create(self, dados):
        invoice = super(AccountInvoice, self).create(dados)
        invoice._check_brazilian_invoice('create')
        return invoice

    @api.model
    def write(self, dados):
        self._check_brazilian_invoice('write')
        res = super(AccountInvoice, self).write(dados)
        return res

    @api.model
    def unlink(self):
        self._check_brazilian_invoice('unlink')
        res = super(AccountInvoice, self).unlink()
        return res

    @api.multi
    def action_move_create(self):
        for invoice in self:
            if not invoice.is_brazilian_invoice:
                super(AccountInvoice, self).action_move_create()
                continue

                # invoice.sped_documento_id.account_move_create()

        return True

        # @api.multi
        # def compute_taxes(self):
        # for invoice in self:
        # if not invoice.is_brazilian_invoice:
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
