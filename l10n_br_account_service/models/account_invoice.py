# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree

from openerp import models, fields, api, _

from openerp.addons.l10n_br_account.models.account_invoice import (
    OPERATION_TYPE)

from .l10n_br_account_service import (
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_DEFAULT)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def _default_fiscal_document(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.service_invoice_id

    @api.model
    def _default_fiscal_document_serie(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.document_serie_service_id

    @api.model
    @api.returns('l10n_br_account.fiscal_category')
    def _default_fiscal_category(self):
        DEFAULT_FCATEGORY_SERVICE = {
            'in_invoice': 'in_invoice_service_fiscal_category_id',
            'out_invoice': 'out_invoice_service_fiscal_category_id',
            'in_refund': 'out_invoice_service_fiscal_category_id',
            'out_refund': 'in_invoice_service_fiscal_category_id'
        }
        default_fo_category = {'service': DEFAULT_FCATEGORY_SERVICE}
        invoice_type = self._context.get('type', 'out_invoice')
        invoice_fiscal_type = self._context.get('fiscal_type', 'service')
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company[default_fo_category[invoice_fiscal_type][invoice_type]]

    fiscal_type = fields.Selection(
        PRODUCT_FISCAL_TYPE,
        'Tipo Fiscal',
        default=PRODUCT_FISCAL_TYPE_DEFAULT
    )
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        'Categoria Fiscal',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_category
    )
    fiscal_document_id = fields.Many2one(
        'l10n_br_account.fiscal.document',
        'Documento',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_document
    )
    fiscal_document_electronic = fields.Boolean(
        related='fiscal_document_id.electronic'
    )
    document_serie_id = fields.Many2one(
        'l10n_br_account.document.serie',
        u'Série',
        domain="[('fiscal_document_id', '=', fiscal_document_id),\
        ('company_id','=',company_id)]",
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_document_serie
    )

    @api.onchange('fiscal_document_id')
    def onchange_fiscal_document_id(self):
        self.document_serie_id = self.company_id.document_serie_service_id

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        context = self.env.context
        active_id = context.get('active_id')
        fiscal_document_code = context.get('fiscal_document_code')
        nfse_form = ('l10n_br_account_service.'
                     'l10n_br_account_service_nfse_form')
        nfse_tree = ('l10n_br_account_service.'
                     'l10n_br_account_service_nfse_tree')
        nfse_views = {'form': nfse_form, 'tree': nfse_tree}

        if active_id and context.get('active_model') == 'account.invoice':
            invoice = self.browse(active_id)
            fiscal_document_code = invoice.fiscal_document_id.code

        if nfse_views.get(view_type) and fiscal_document_code == u'XX':
            view_id = self.env.ref(nfse_views.get(view_type)).id

        return super(AccountInvoice, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)

    @api.multi
    def open_fiscal_document(self):
        """return action to open NFS-e form"""
        result = super(AccountInvoice, self).open_fiscal_document()
        result['name'] = _('NFS-e')
        return result


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    # TODO migrate to new API
    def fields_view_get(self, cr, uid, view_id=None, view_type=False,
                        context=None, toolbar=False, submenu=False):

        result = super(AccountInvoiceLine, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)

        if context is None:
            context = {}

        if view_type == 'form':
            eview = etree.fromstring(result['arch'])

            if 'type' in context.keys():
                cfops = eview.xpath("//field[@name='cfop_id']")
                for cfop_id in cfops:
                    cfop_id.set('domain', "[('type','=','%s')]" % (
                        OPERATION_TYPE[context['type']],))
                    cfop_id.set('required', '1')

            if context.get('fiscal_type', False) == 'service':

                cfops = eview.xpath("//field[@name='cfop_id']")
                for cfop_id in cfops:
                    cfop_id.set('invisible', '1')
                    cfop_id.set('required', '0')

            result['arch'] = etree.tostring(eview)

        return result
