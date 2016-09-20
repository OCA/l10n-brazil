# -*- coding: utf-8 -*-
# Copyright (C) 2013  Florian da Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError

from openerp.addons.l10n_br_account.models.account_invoice import (
    OPERATION_TYPE,
    JOURNAL_TYPE)


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    force_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Forçar Categoria Fiscal',
        domain="[('journal_type', '=', 'sale_refund'),\
                ('fiscal_type', '=', 'product')]")

    @api.multi
    def compute_refund(self, mode='refund'):
        inv_obj = self.env['account.invoice']
        context = dict(self.env.context)

        for send_invoice in inv_obj.browse(context.get('active_ids')):
            result = super(AccountInvoiceRefund, self).compute_refund(mode)
            domain = result['domain']

            ids_domain = [x for x in domain if x[0] == 'id'][0]
            invoice_ids = ids_domain[2]
            for invoice in inv_obj.browse(invoice_ids):

                if not self.force_fiscal_category_id and not \
                        invoice.fiscal_category_id.refund_fiscal_category_id:
                    raise UserError(_("Categoria Fiscal: %s não possui uma "
                                      "catégoria de devolução!") %
                                    invoice.fiscal_category_id.name)

                fiscal_category_id = self.force_fiscal_category_id.id or \
                    invoice.fiscal_category_id.refund_fiscal_category_id.id

                onchange = invoice.onchange_fiscal_category_id(
                    invoice.partner_id.id, invoice.partner_id.id,
                    invoice.company_id.id, fiscal_category_id)

                onchange['value']['fiscal_category_id'] = \
                    fiscal_category_id
                onchange['value']['nfe_purpose'] = '4'

                for line in invoice.invoice_line:

                    if not self.force_fiscal_category_id and not \
                            line.fiscal_category_id.refund_fiscal_category_id:
                        raise UserError(_("Categoria Fiscal: %s não possui"
                                          " uma catégoria de devolução!") %
                                        line.fiscal_category_id.name)

                    line_fiscal_category_id = (line.fiscal_category_id
                                               .refund_fiscal_category_id.id)

                    line_onchange = line.onchange_fiscal_position(
                        invoice.partner_id.id, invoice.company_id.id,
                        line.product_id.id, line_fiscal_category_id,
                        line.account_id.id, line.quantity,
                        line.price_unit, line.discount, line.insurance_value,
                        line.freight_value, line.other_costs_value)
                    line_onchange['value']['fiscal_category_id'] = \
                        line_fiscal_category_id
                    line.write(line_onchange['value'])
                invoice.write(onchange['value'])
            return result

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        result = super(AccountInvoiceRefund, self).fields_view_get(
            cr, uid, view_id, view_type, context, toolbar, submenu)
        if not context:
            context = {}
        type = context.get('type', 'out_invoice')
        journal_type = JOURNAL_TYPE[type]
        type = OPERATION_TYPE[type]
        eview = etree.fromstring(result['arch'])
        fiscal_categ = eview.xpath("//field[@name='fiscal_category_id']")
        for field in fiscal_categ:
            field.set('domain', "[('journal_type', '=', '%s'),\
                                 ('fiscal_type', '=', 'product'),\
                                 ('type', '=', '%s')]" % (journal_type,
                                                          type))
        result['arch'] = etree.tostring(eview)
        return result
