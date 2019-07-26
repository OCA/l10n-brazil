# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.addons.l10n_br_account_product.constantes import (
    CAMPO_DOCUMENTO_FISCAL,
)
from openerp.exceptions import Warning, ValidationError


VALORES_NFE = {
    'cofins_value': 'COFINS própria',
    'csll_value': 'CSLL própria',
    'amount_discount': 'Desconto',
    'icms_dest_value': 'Diferencial de alíquota (ICMS próprio)',
    'amount_freight': 'Frete',
    'icms_value': 'ICMS próprio',
    'icms_st_value': 'ICMS ST',
    'ii_value': 'Imposto de importação',
    'ipi_value': 'IPI',
    'issqn_value': 'ISS próprio',
    'amount_costs': 'Outras despesas acessórias',
    'pis_value': 'PIS próprio',
    'amount_insurance':'Seguro',
    'amount_net': 'Valor Fatura',
    'amount_total': 'Total da NF',
}

TYPE = {
    'out_invoice': 'Fatura de Cliente',
    'in_invoice': 'Fatura de Fornecedor',
    'out_refund': 'Fatura Reembolso Cliente',
    'in_refund': 'Fatura Reembolso Fornecedor',
}


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    name = fields.Char(
        string='Nome',
        compute='_compute_name'
    )

    number = fields.Char(
        string='number',
        compute='_compute_number',
        related=False,
    )

    account_event_entrada_id = fields.Many2one(
        string=u'Evento Contábil Entrada',
        comodel_name='account.event',
        copy=False,
    )

    cofins_value = fields.Float(
        help='Código para roteiro contábil: "cofins_value"',
    )

    cofins_value_wh = fields.Float(
        help='Código para roteiro contábil: "cofins_value_wh"',
    )

    csll_value = fields.Float(
        help='Código para roteiro contábil: "csll_value"',
    )

    csll_value_wh = fields.Float(
        help='Código para roteiro contábil: "csll_value_wh"',
    )

    amount_discount = fields.Float(
        help='Código para roteiro contábil: "amount_discount"',
    )

    icms_dest_value = fields.Float(
        help='Código para roteiro contábil: "icms_dest_value"',
    )

    amount_freight = fields.Float(
        help='Código para roteiro contábil: "amount_freight"',
    )

    icms_value = fields.Float(
        help='Código para roteiro contábil: "icms_value"',
    )

    icms_st_value = fields.Float(
        help='Código para roteiro contábil: "icms_st_value"',
    )

    ii_value = fields.Float(
        help='Código para roteiro contábil: "ii_value"',
    )

    inss_value_wh = fields.Float(
        help='Código para roteiro contábil: "inss_value_wh"',
    )

    ipi_value = fields.Float(
        help='Código para roteiro contábil: "ipi_value"',
    )

    irrf_value_wh = fields.Float(
        help='Código para roteiro contábil: "irrf_value_wh"',
    )

    issqn_value = fields.Float(
        help='Código para roteiro contábil: "issqn_value"',
    )

    issqn_value_wh = fields.Float(
        help='Código para roteiro contábil: "issqn_value_wh"',
    )

    amount_costs = fields.Float(
        help='Código para roteiro contábil: "amount_costs"',
    )

    pis_value = fields.Float(
        help='Código para roteiro contábil: "pis_value"',
    )

    pis_value_wh = fields.Float(
        help='Código para roteiro contábil: "pis_value_wh"',
    )

    amount_insurance = fields.Float(
        help='Código para roteiro contábil: "amount_insurance"',
    )

    amount_net = fields.Float(
        help='Código para roteiro contábil: "amount_net"',
    )

    amount_total = fields.Float(
        help='Código para roteiro contábil: "amount_total"',
    )

    @api.multi
    def _compute_name(self):
        for record in self:
            record.name = '{} - {} - {}'.format(
                TYPE[record.type],
                record.partner_id.name,
                record.internal_number
            )

    @api.depends('internal_number')
    def _compute_number(self):
        for record in self:
            record.number = record.internal_number

    @api.multi
    def _compute_residual(self):
        self.residual = 0.0
        # Each partial reconciliation is considered only once for each invoice it appears into,
        # and its residual amount is divided by this number of invoices
        partial_reconciliations_done = []
        for move in self.move_id:
            for line in move.line_id:
                if line.account_id.type not in ('receivable', 'payable'):
                    continue
                if line.reconcile_partial_id and line.reconcile_partial_id.id in partial_reconciliations_done:
                    continue
                # Get the correct line residual amount
                if line.currency_id == self.currency_id:
                    line_amount = line.amount_residual_currency if line.currency_id else line.amount_residual
                else:
                    from_currency = line.company_id.currency_id.with_context(
                        date=line.date)
                    line_amount = from_currency.compute(line.amount_residual,
                                                        self.currency_id)
                # For partially reconciled lines, split the residual amount
                if line.reconcile_partial_id:
                    partial_reconciliation_invoices = set()
                    for pline in line.reconcile_partial_id.line_partial_ids:
                        if pline.invoice and self.type == pline.invoice.type:
                            partial_reconciliation_invoices.update(
                                [pline.invoice.id])
                    line_amount = self.currency_id.round(
                        line_amount / len(partial_reconciliation_invoices))
                    partial_reconciliations_done.append(
                        line.reconcile_partial_id.id)
                self.residual += line_amount
        self.residual = max(self.residual, 0.0)

    @api.depends(
        'move_id.line_id.reconcile_id.line_id',
        'move_id.line_id.reconcile_partial_id.line_partial_ids',
    )
    def _compute_receivables(self):
        lines = self.env['account.move.line']
        for move in self.move_id:
            for line in move.line_id:
                if line.account_id.id == self.account_id.id and \
                        line.account_id.type in ('receivable', 'payable') and \
                        self.journal_id.revenue_expense:
                    lines |= line
        self.move_line_receivable_id = (lines).sorted()

    @api.depends(
        'move_id.line_id.reconcile_id.line_id',
        'move_id.line_id.reconcile_partial_id.line_partial_ids',
    )
    def _compute_payments(self):
        partial_lines = lines = self.env['account.move.line']
        for move in self.move_id:
            for line in move.line_id:
                if line.account_id != self.account_id:
                    continue
                if line.reconcile_id:
                    lines |= line.reconcile_id.line_id
                elif line.reconcile_partial_id:
                    lines |= line.reconcile_partial_id.line_partial_ids
                partial_lines += line
        self.payment_ids = (lines - partial_lines).sorted()

    @api.depends(
        'move_id.line_id.account_id',
        'move_id.line_id.reconcile_id.line_id',
        'move_id.line_id.reconcile_partial_id.line_partial_ids',
    )
    def _compute_move_lines(self):
        # Give Journal Items related to the payment reconciled to this invoice.
        # Return partial and total payments related to the selected invoice.
        self.move_lines = self.env['account.move.line']
        if not self.move_id:
            return
        data_lines = []
        for move in self.move_id:
            data_lines += move.line_id.filtered(
                lambda l: l.account_id == self.account_id)
        partial_lines = self.env['account.move.line']
        for data_line in data_lines:
            if data_line.reconcile_id:
                lines = data_line.reconcile_id.line_id
            elif data_line.reconcile_partial_id:
                lines = data_line.reconcile_partial_id.line_partial_ids
            else:
                lines = self.env['account.move.line']
            partial_lines += data_line
            self.move_lines = lines - partial_lines

    @api.multi
    def action_cancel(self):
        payment_line_obj = self.env['payment.line']
        for inv in self:
            pl_line_ids = []
            for move in inv.move_id:
                if move and move.line_id:
                    inv_mv_lines = [x.id for x in move.line_id]
                    pl_line_ids = payment_line_obj.search(
                        [('move_line_id', 'in', inv_mv_lines)])
                if pl_line_ids:
                    pay_line = payment_line_obj.browse(pl_line_ids)
                    payment_order_name = ','.join(
                        map(lambda x: x.order_id.reference, pay_line)
                    )
                    raise Warning(
                        _('Error!'),
                        _(
                            "You cannot cancel an invoice which has already "
                            "been imported in a payment order. Remove it from "
                            "the following payment order : {}.".format(
                                payment_order_name)
                        )
                    )

        move = self.move_id

        self.write({'state': 'cancel', 'move_id': False})
        if move:
            move.button_cancel()

        return True

    def _get_invoice_event_data(self):
        vals = {}

        # vals['company_id'] = self.company_id.id
        vals['ref'] = 'NF-e: {} - {}'.format(
            self.partner_id.name, self.internal_number)
        if not self.account_event_entrada_id:
            vals['ref'] += ' (Entrada)'
        else:
            vals['ref'] += ' (Pagamento)'
        vals['data'] = self.date_hour_invoice.split(' ')[0]
        vals['origem'] = '{},{}'.format('account.invoice', self.id)

        if self.fiscal_category_id.account_event_template_id:
            vals['account_event_template_id'] = \
                self.fiscal_category_id.account_event_template_id.id

        return vals

    def _get_invoice_move_line_data(self):
        lines = []
        vals = {}
        for info in CAMPO_DOCUMENTO_FISCAL:
            info_name = info[0]
            if self[info_name]:
                vals = {
                    'code': info_name,
                    'valor': self[info_name],
                    'name': info[1],
                }

                if self.type in ['out_invoice', 'out_refund'] and \
                        info_name == 'amount_net':
                    if self.type in ['out_invoice', 'out_refund']:
                        if self.partner_id.property_account_receivable:
                            vals['conta_debito_exclusivo_id'] = \
                                self.partner_id.property_account_receivable.id
                    else:
                        if self.partner_id.property_account_payable:
                            vals['conta_credito_exclusivo_id'] = \
                                self.partner_id.property_account_payable.id

                lines.append(vals)
                vals = {}

        for line in self.invoice_line:
            vals = {
                'code': line.product_id.codigo_contabil,
                'valor': line.price_total,
                'name': line.product_id.name,
            }
            lines.append(vals)
            vals = {}

        lines.append(vals)

        return lines

    @api.multi
    def action_move_create(self):
        for inv in self:
            if not inv.invoice_line:
                raise ValidationError(
                    _('No Invoice Lines!'),
                    _('Please create some invoice lines.')
                )

            if inv.move_id:
                inv.move_id.button_return()
                inv.move_id.unlink()

            if not inv.period_id:
                inv.period_id = self.env['account.period'].find(
                    inv.date_hour_invoice)[0]

            if not inv.account_event_entrada_id:
                account_event_data = inv._get_invoice_event_data()
                account_event_line_data = inv._get_invoice_move_line_data()

                account_event_id = self.env['account.event'].create(
                    account_event_data
                )
                account_event_id.gerar_eventos(account_event_line_data)

                inv.account_event_entrada_id = account_event_id
            else:
                account_event_data = inv._get_invoice_event_data()
                account_event_line_data = inv._get_invoice_move_line_data()

                account_event_id = self.env['account.event'].create(
                    account_event_data
                )
                account_event_id.gerar_eventos(account_event_line_data)

                inv.account_event_pagamento_id = account_event_id

                account_invoice_tax = self.env['account.invoice.tax']
                compute_taxes = account_invoice_tax.compute(
                    inv.with_context(lang=inv.partner_id.lang))
                inv.check_tax_lines(compute_taxes)

    @api.multi
    def gerar_contabilidade(self):
        for inv in self:
            inv.action_move_create()

    @api.multi
    def button_create_financial_move(self):
        for record in self:
            if not record.payment_term:
                raise Warning(
                    "É necessário escolher a condição de pagamento!"
                )
            record.action_financial_create()

    @api.multi
    def action_financial_create(self):
        """ Cria o lançamento financeiro do documento fiscal
        :return:
        """
        for documento in self:
            if documento.state not in 'open':
                continue

            documento.financial_ids.unlink()

            for duplicata in documento.duplicata_ids:
                dados = duplicata.prepara_financial_move()
                self.env['financial.move'].create(dados)

    def get_linhas_evento_contabeis(self, valor_pago):
        linhas = []

        proporcional = valor_pago/self.amount_net

        for parametro_nota in CAMPO_DOCUMENTO_FISCAL:
            if '_wh' not in parametro_nota[0] and self[parametro_nota[0]]:
                vals = {
                    'name': parametro_nota[1],
                    'code': parametro_nota[0],
                    'valor': self[parametro_nota[0]] * proporcional,
                }

                if parametro_nota[0] == 'amount_net':
                    if self.type == 'out_invoice' and self.partner_id.property_account_receivable:
                        vals['conta_credito_exclusivo_id'] = \
                                self.partner_id.property_account_receivable.id
                    else:
                        vals['conta_debito_exclusivo_id'] = \
                            self.partner_id.property_account_payable.id

                linhas.append((0, 0, vals))

        return linhas
