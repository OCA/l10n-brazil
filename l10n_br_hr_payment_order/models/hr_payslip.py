# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    payment_mode_id = fields.Many2one(
        comodel_name='payment.mode', string="Payment Mode",
        domain="[('type', '=', type)]")

    @api.multi
    def onchange_partner_id(
            self, type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False):
        res = super(AccountInvoice, self).onchange_partner_id(
            type, partner_id, date_invoice=date_invoice,
            payment_term=payment_term, partner_bank_id=partner_bank_id,
            company_id=company_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            if type == 'in_invoice':
                res['value']['payment_mode_id'] = \
                    partner.supplier_payment_mode.id
            elif type == 'out_invoice':
                res['value']['payment_mode_id'] = \
                    partner.customer_payment_mode.id
                # Do not change the default value of partner_bank_id if
                # partner.customer_payment_mode is False
                if partner.customer_payment_mode.bank_id:
                    res['value']['partner_bank_id'] = \
                        partner.supplier_payment_mode.bank_id.id
        else:
            res['value']['payment_mode_id'] = False
        return res

    @api.multi
    def _prepare_new_payment_order(self):
        self.ensure_one()
        vals = {'payment_mode_id': self.payment_mode_id.id}
        # other important fields are set by the inherit of create
        # in account_payment_order.py
        return vals

    @api.multi
    def create_account_payment_line(self):
        apoo = self.env['account.payment.order']
        aplo = self.env['account.payment.line']
        result_payorder_ids = []
        action_payment_type = 'debit'
        for inv in self:
            if inv.state != 'open':
                raise UserError(_(
                    "The invoice %s is not in Open state") % inv.number)
            if not inv.payment_mode_id:
                raise UserError(_(
                    "No Payment Mode on invoice %s") % inv.number)
            if not inv.move_id:
                raise UserError(_(
                    "No Journal Entry on invoice %s") % inv.number)
            if not inv.payment_order_ok:
                raise UserError(_(
                    "The invoice %s has a payment mode '%s' "
                    "which is not selectable in payment orders."))
            payorders = apoo.search([
                ('payment_mode_id', '=', inv.payment_mode_id.id),
                ('state', '=', 'draft')])
            if payorders:
                payorder = payorders[0]
                new_payorder = False
            else:
                payorder = apoo.create(inv._prepare_new_payment_order())
                new_payorder = True
            result_payorder_ids.append(payorder.id)
            action_payment_type = payorder.payment_type
            count = 0
            for line in inv.move_id.line_ids:
                if line.account_id == inv.account_id and not line.reconciled:
                    paylines = aplo.search([
                        ('move_line_id', '=', line.id),
                        ('state', '!=', 'cancel')])
                    if not paylines:
                        line.create_payment_line_from_move_line(payorder)
                        count += 1
            if count:
                if new_payorder:
                    inv.message_post(_(
                        '%d payment lines added to the new draft payment '
                        'order %s which has been automatically created.')
                        % (count, payorder.name))
                else:
                    inv.message_post(_(
                        '%d payment lines added to the existing draft '
                        'payment order %s.')
                        % (count, payorder.name))
            else:
                raise UserError(_(
                    'No Payment Line created for invoice %s because '
                    'it already exists or because this invoice is '
                    'already paid.') % inv.number)
        action = self.env['ir.actions.act_window'].for_xml_id(
            'account_payment_order',
            'account_payment_order_%s_action' % action_payment_type)
        if len(result_payorder_ids) == 1:
            action.update({
                'view_mode': 'form,tree,pivot,graph',
                'res_id': payorder.id,
                'views': False,
                })
        else:
            action.update({
                'view_mode': 'tree,form,pivot,graph',
                'domain': "[('id', 'in', %s)]" % result_payorder_ids,
                'views': False,
                })
        return action