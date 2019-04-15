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

                invoice.fiscal_category_id = (
                    self.force_fiscal_category_id.id or
                    invoice.fiscal_category_id.refund_fiscal_category_id.id)

                invoice._onchange_fiscal()

                invoice_values = {
                    'fiscal_category_id': invoice.fiscal_category_id.id,
                    'fiscal_position_id': invoice.fiscal_position_id.id,
                    'nfe_purpose': '4'
                }

                for line in invoice.invoice_line_ids:
                    if not self.force_fiscal_category_id and not \
                            line.fiscal_category_id.refund_fiscal_category_id:
                        raise UserError(_(u"Categoria Fiscal: %s não possui"
                                          u" uma catégoria de devolução!") %
                                        line.fiscal_category_id.name)

                    line.fiscal_category_id = (
                        self.force_fiscal_category_id.id or
                        line.fiscal_category_id.refund_fiscal_category_id.id)

                    line._onchange_fiscal()

                    line_values = {
                        'fiscal_category_id': line.fiscal_category_id.id,
                        'fiscal_position_id': line.fiscal_position_id.id,
                        'cfop_id': line.fiscal_position_id.cfop_id.id
                    }
                    line.write(line_values)
                invoice.write(invoice_values)
            return result

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):

        result = super(AccountInvoiceRefund, self).fields_view_get(
            view_id, view_type, toolbar, submenu)

        invoice_type = self.env.context.get('type', 'out_invoice')
        journal_type = JOURNAL_TYPE[invoice_type]
        invoice_type = OPERATION_TYPE[type]
        eview = etree.fromstring(result['arch'])
        fiscal_categ = eview.xpath("//field[@name='fiscal_category_id']")
        for field in fiscal_categ:
            field.set('domain', "[('journal_type', '=', '%s'),\
                                 ('fiscal_type', '=', 'product'),\
                                 ('type', '=', '%s')]" % (journal_type,
                                                          invoice_type))
        result['arch'] = etree.tostring(eview)
        return result
