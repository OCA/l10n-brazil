# -*- coding: utf-8 -*-
# (c) 2016 Kmee - Fernando Marcato
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _check_rules(self, object):
        """
        This rules are here to determine if the invoice has no commercial
        value and to allow the code to pass if the rules validate.
        Returns: true or false
        """
        if (not object.journal_id.revenue_expense and
                object.journal_id.automatic_conciliation and
                (object.fiscal_category_id.property_journal ==
                 object.journal_id) and
                object.state == 'open' and
                object.company_id.id == self.env.user.company_id.id and
                object.journal_id.conciliation_journal):
            return True
        return False

    @api.multi
    def invoice_validate(self):
        super(AccountInvoice, self).invoice_validate()
        for object in self.env['account.invoice'].search(
                [('id', '=', self.id)]):
            if (self._check_rules(object)):
                voucher_obj = self.env['account.voucher']
                context = {}
                context.update({
                    'invoice_id': object.id,
                    'invoice_type': object.type,
                    'type': (object.type in ('out_invoice', 'out_refund') and
                             'receipt' or 'payment'),
                    'payment_expected_currency': object.currency_id.id,
                    'default_partner_id':
                        self.env['res.partner']._find_accounting_partner(
                            object.partner_id).id,
                    'default_amount': (object.type in ('out_refund',
                                                       'in_refund'
                                                       ) and
                                       object.residual or
                                       object.residual),
                    'default_reference': object.name,
                    'default_type': object.type in (
                        'out_invoice', 'out_refund'
                    ) and 'receipt' or 'payment',
                    'default_journal_id':
                        object.journal_id.conciliation_journal.id
                })
                default_keys = [vdk for vdk in voucher_obj._defaults.keys()]
                vals = voucher_obj.with_context(
                    context).default_get(default_keys)
                onchange_date_vals = voucher_obj.with_context(
                    context).onchange_date(
                    date=vals['date'],
                    currency_id=vals['currency_id'],
                    payment_rate_currency_id=vals['payment_rate_currency_id'],
                    amount=vals['amount'],
                    company_id=vals['company_id']
                )['value']
                vals.update(onchange_date_vals)
                onchange_partner_vals = voucher_obj.with_context(
                    context).onchange_partner_id(
                    vals['partner_id'],
                    vals['journal_id'],
                    vals['amount'],
                    vals['currency_id'],
                    vals['type'],
                    False
                )['value']
                vals.update(onchange_partner_vals)
                onchange_amount_vals = voucher_obj.with_context(
                    context).onchange_amount(
                    vals['amount'],
                    vals['payment_rate'],
                    vals['partner_id'],
                    vals['journal_id'],
                    vals['currency_id'],
                    vals['type'],
                    vals['date'],
                    vals['payment_rate_currency_id'],
                    vals['company_id'],
                )['value']
                vals.update(onchange_amount_vals)
                onchange_journal_vals = voucher_obj.with_context(
                    context).onchange_journal(
                    vals['journal_id'],
                    vals['line_cr_ids'],
                    False,
                    vals['partner_id'],
                    vals['date'],
                    vals['amount'],
                    vals['type'],
                    vals['company_id'],
                )['value']
                vals.update(onchange_journal_vals)
                vals['line_cr_ids'] = [(0, 0, x) for x in vals['line_cr_ids']]
                vals['line_dr_ids'] = [(0, 0, x) for x in vals['line_dr_ids']]
                voucher_id = voucher_obj.with_context(context).create(vals)
                voucher_id.button_proforma_voucher()
