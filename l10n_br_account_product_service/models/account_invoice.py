# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api, _
from openerp.exceptions import RedirectWarning

from .l10n_br_account_product_service import PRODUCT_FISCAL_TYPE


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def _get_fiscal_type(self):
        return self.env.context.get('fiscal_type', '')

    @api.model
    @api.returns('l10n_br_account.fiscal_category')
    def _default_fiscal_category(self):
        DEFAULT_FCATEGORY_PRODUCT = {
            'in_invoice': 'in_invoice_fiscal_category_id',
            'out_invoice': 'out_invoice_fiscal_category_id',
            'in_refund': 'in_refund_fiscal_category_id',
            'out_refund': 'out_refund_fiscal_category_id'
        }

        DEFAULT_FCATEGORY_SERVICE = {
            'in_invoice': 'in_invoice_service_fiscal_category_id',
            'out_invoice': 'out_invoice_service_fiscal_category_id'
        }

        default_fo_category = {
            'product': DEFAULT_FCATEGORY_PRODUCT,
            'service': DEFAULT_FCATEGORY_SERVICE
        }

        invoice_type = self._context.get('type', 'out_invoice')
        invoice_fiscal_type = self._context.get('fiscal_type', 'product')
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company[default_fo_category[invoice_fiscal_type][invoice_type]]

    @api.model
    def _default_fiscal_document(self):
        invoice_fiscal_type = self.env.context.get('fiscal_type', 'product')
        if invoice_fiscal_type in ('product', 'service'):
            fiscal_invoice_id = invoice_fiscal_type + '_invoice_id'

            company = self.env['res.company'].browse(
                self.env.user.company_id.id)
            return company[fiscal_invoice_id]

    @api.model
    def _default_fiscal_document_serie(self):
        invoice_fiscal_type = self.env.context.get('fiscal_type', 'product')
        if invoice_fiscal_type in ('product', 'service'):
            fiscal_document_serie = self.env['l10n_br_account.document.serie']
            company = self.env['res.company'].browse(
                self.env.user.company_id.id)

            if invoice_fiscal_type == 'product':
                fiscal_document_series = [doc_serie for doc_serie in
                                          company.document_serie_product_ids if
                                          doc_serie.fiscal_document_id.id ==
                                          company.product_invoice_id.id and
                                          doc_serie.active]
                if fiscal_document_series:
                    fiscal_document_serie = fiscal_document_series[0]
            else:
                fiscal_document_serie = company.document_serie_service_id
            return fiscal_document_serie

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        context = self.env.context
        fiscal_document_code = context.get('fiscal_document_code')
        active_id = context.get('active_id')
        nfe_form = ('l10n_br_account_product.'
                    'l10n_br_account_product_nfe_form')
        nfe_tree = ('l10n_br_account_product.'
                    'l10n_br_account_product_nfe_tree')
        nfe_views = {'form': nfe_form, 'tree': nfe_tree}

        nfse_form = ('l10n_br_account_service.'
                     'l10n_br_account_service_nfse_form')
        nfse_tree = ('l10n_br_account_service.'
                     'l10n_br_account_service_nfse_tree')
        nfse_views = {'form': nfse_form, 'tree': nfse_tree}

        if active_id:
            invoice = self.browse(active_id)
            fiscal_document_code = invoice.fiscal_document_id.code

        if fiscal_document_code == '55':
            if nfe_views.get(view_type):
                view_id = self.env.ref(nfe_views.get(view_type)).id

        if fiscal_document_code == 'XX':
            if nfse_views.get(view_type):
                view_id = self.env.ref(nfse_views.get(view_type)).id

        return super(AccountInvoice, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)

    @api.onchange('fiscal_document_id')
    def onchange_fiscal_document_id(self):
        serie = False
        if self.fiscal_type in ('product', 'service'):
            if self.issuer == '0':
                if self.fiscal_type == 'product':
                    series = [doc_serie for doc_serie in
                              self.company_id.document_serie_product_ids if
                              doc_serie.fiscal_document_id.id ==
                              self.fiscal_document_id.id and doc_serie.active]
                    if series:
                        serie = series[0]
                else:
                    serie = self.company_id.document_serie_service_id

                if not serie:
                    action = self.env.ref(
                        'l10n_br_account.'
                        'action_l10n_br_account_document_serie_form')
                    msg = _(u'Você deve ter uma série de documento fiscal'
                            u' para este documento fiscal.')
                    raise RedirectWarning(
                        msg, action.id, _(u'Criar uma nova série'))
                self.document_serie_id = serie

    fiscal_type = fields.Selection(
        PRODUCT_FISCAL_TYPE,
        'Tipo Fiscal',
        default=_get_fiscal_type
    )
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal',
        readonly=True, states={'draft': [('readonly', False)]},
        default=_default_fiscal_category)
    document_serie_id = fields.Many2one(
        'l10n_br_account.document.serie', string=u'Série',
        domain="[('fiscal_document_id', '=', fiscal_document_id),\
        ('company_id','=',company_id)]", readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_document_serie)
    fiscal_document_id = fields.Many2one(
        'l10n_br_account.fiscal.document', string='Documento', readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_document)
