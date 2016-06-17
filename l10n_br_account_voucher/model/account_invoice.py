# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2016 - TODAY Fernando Marcato - Kmee                          #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        super(AccountInvoice, self).invoice_validate()
        for object in self.env['account.invoice'].search(
                [('id', '=', self.id)]):
            if (not object.journal_id.revenue_expense
                and object.journal_id.automatic_conciliation
                and object.fiscal_category_id.property_journal ==
                    object.journal_id
                and object.state == 'open'
                and object.company_id.id ==
                    self.env.user.company_id.id
                and object.journal_id.conciliation_journal):
                voucher_obj = self.env['account.voucher']
                context = {}
                context.update({
                    'invoice_id': object.id,
                    'invoice_type': object.type,
                    'type': object.type in (
                        'out_invoice', 'out_refund')
                            and 'receipt' or 'payment',
                    'payment_expected_currency': object.currency_id.id,
                    'default_partner_id': self.env['res.partner'].
                        _find_accounting_partner(object.partner_id).id,
                    'default_amount': object.type in (
                        'out_refund', 'in_refund') and -object.residual
                                      or object.residual,
                    'default_reference': object.name,
                    'default_type': object.type in (
                        'out_invoice', 'out_refund')
                                    and 'receipt' or 'payment',
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
