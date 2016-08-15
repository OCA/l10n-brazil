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
        return self.env.context.get('fiscal_type',
                                    'product')

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
        fiscal_invoice_id = invoice_fiscal_type + '_invoice_id'

        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company[fiscal_invoice_id]

    @api.model
    def _default_fiscal_document_serie(self):
        invoice_fiscal_type = self.env.context.get('fiscal_type', 'product')
        fiscal_document_serie = self.env['l10n_br_account.document.serie']
        company = self.env['res.company'].browse(self.env.user.company_id.id)

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

    @api.onchange('fiscal_document_id')
    def onchange_fiscal_document_id(self):
        serie = False
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
                msg = _(u'Você deve ser uma série de documento fiscal'
                        u'para este documento fiscal.')
                raise RedirectWarning(
                    msg, action.id, _(u'Criar uma nova série'))
            self.document_serie_id = serie

    fiscal_type = fields.Selection(PRODUCT_FISCAL_TYPE,
                                   'Tipo Fiscal',
                                   required=True,
                                   default=_get_fiscal_type)
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
