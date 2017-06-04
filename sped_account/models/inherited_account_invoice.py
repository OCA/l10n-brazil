# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.addons.l10n_br_base.constante_tributaria import *


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    is_brazilian_invoice = fields.Boolean(
        string=u'Is a Brazilian Invoice?',
        compute='_compute_is_brazilian_invoice',
    )
    sped_empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
    )
    sped_participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string=u'Destinatário/Remetente'
    )
    sped_operacao_produto_id = fields.Many2one(
        comodel_name='sped.operacao',
        string=u'Operação Fiscal (produtos)',
        domain=[('modelo', 'in', MODELO_FISCAL_EMISSAO_PRODUTO)],
    )
    sped_operacao_servico_id = fields.Many2one(
        comodel_name='sped.operacao',
        string=u'Operação Fiscal (serviços)',
        domain=[('modelo', 'in', MODELO_FISCAL_EMISSAO_SERVICO)],
    )
    sped_documento_ids = fields.Many2one(
        comodel_name='sped.documento',
        inverse_name='invoice_id',
        string=u'Documentos Fiscais',
    )
    condicao_pagamento_id = fields.Many2one(
        comodel_name='account.payment.term',
        string='Condição de pagamento',
        domain=[('forma_pagamento', '!=', False)],
    )
    invoice_line_brazil_ids = fields.One2many(
        comodel_name='account.invoice.line.brazil',
        inverse_name='invoice_id',
        string='Linhas da Fatura',
    )

    @api.depends('sped_documento_ids', 'company_id', 'partner_id')
    def _compute_is_brazilian_invoice(self):
        for invoice in self:
            if invoice.company_id.country_id:
                if invoice.company_id.country_id.id == \
                        self.env.ref('base.br').id:
                    invoice.is_brazilian_invoice = True

                    if invoice.partner_id.sped_participante_id:
                        invoice.sped_participante_id = \
                            invoice.partner_id.sped_participante_id

                    if invoice.company_id.sped_empresa_id:
                        invoice.sped_empresa_id = \
                            invoice.company_id.sped_empresa_id

                    continue

            invoice.is_brazilian_invoice = False

    @api.onchange('sped_participante_id')
    def _onchange_sped_participante_id(self):
        self.ensure_one()
        self.partner_id = self.sped_participante_id.partner_id

    @api.onchange('sped_empresa_id')
    def _onchange_sped_empresa_id(self):
        self.ensure_one()
        self.company_id = self.sped_empresa_id.company_id

    @api.onchange('condicao_pagamento_id')
    def _onchange_condicao_pagamento_id(self):
        self.ensure_one()
        self.payment_term_id = self.condicao_pagamento_id

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount',
                 'currency_id', 'company_id', 'date_invoice', 'type',
                 'invoice_line_brazil_ids.vr_nf',
                 'invoice_line_brazil_ids.vr_fatura')
    def _compute_amount(self):
        if not self.is_brazilian_invoice:
            return super(AccountInvoice, self)._compute_amount()

        #
        # Tratamos os impostos brasileiros;
        # amount_untaxed é equivalente ao valor dos produtos
        #
        self.amount_untaxed = \
            sum(item.vr_produtos for item in self.invoice_line_brazil_ids)
        #
        # amount_tax são os imposto que são somados no valor total da NF;
        # no nosso caso, não só impostos, mas todos os valores que entram
        # no total da NF: outras despesas acessórias, frete etc.
        # E, como o amount_total é o valor DA FATURA, não da NF, somamos este
        # primeiro, e listamos o valor dos impostos considerando valores
        # acessórios, e potencias retenções de imposto que estejam
        # reduzindo o valor
        #
        self.amount_total = \
            sum(item.vr_fatura for item in self.invoice_line_brazil_ids)

        self.amount_tax = self.amount_total - self.amount_untaxed
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and \
            self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = \
                currency_id.compute(self.amount_total,
                                    self.company_id.currency_id)
            amount_untaxed_signed = \
                currency_id.compute(self.amount_untaxed,
                                    self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign
        
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

    # @api.model
    # def create(self, dados):
    #     invoice = super(AccountInvoice, self).create(dados)
    #     invoice._check_brazilian_invoice('create')
    #     return invoice
    #
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
