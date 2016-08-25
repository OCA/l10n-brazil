# -*- coding: utf-8 -*-
# Copyright (C) 2016  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class AccountInvoiceReport(models.Model):

    _inherit = 'account.invoice.report'

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        'Fiscal Category', readonly=True)
    state = fields.Selection(
        selection_add=[
            ('sefaz_export', u'Enviar para Receita'),
            ('sefaz_exception', u'Erro de autorização da Receita'),
            ('sefaz_cancelled', u'Cancelado no Sefaz'),
            ('sefaz_denied', u'Denegada no Sefaz'),
        ])
    internal_number = fields.Char(
        string='Invoice Number',
        size=32,
        readonly=True,
    )
    fiscal_document_electronic = fields.Boolean(
        string='Electronic',
        readonly=True,
    )
    document_serie_id = fields.Many2one(
        'l10n_br_account.document.serie',
        string=u'Série',
        readonly=True
    )
    revenue_expense = fields.Char(
        readonly=True,
        string='Gera Financeiro',
        size=32,
    )

    l10n_br_city_id = fields.Many2one(
        'l10n_br_base.city',
        string='Municipio',
        )
    state_id = fields.Many2one(
        'res.country.state',
        string='Estado',
        required=True
    )

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + (
            ", sub.fiscal_category_id as fiscal_category_id"
            ", sub.internal_number as internal_number"
            ", sub.fiscal_document_electronic as fiscal_document_electronic"
            ", sub.document_serie_id as document_serie_id"
            ", CASE WHEN sub.revenue_expense = 't' THEN 'Gera Financeiro' "
            "ELSE 'Não Gera Financeiro' end as revenue_expense"
            ", sub.l10n_br_city_id as l10n_br_city_id"
            ", sub.state_id as state_id"
        )

    def _sub_select(self):
        return super(AccountInvoiceReport, self)._sub_select() + (
            ", ail.fiscal_category_id as fiscal_category_id"
            ", ai.internal_number as internal_number"
            ", ai.fiscal_document_electronic as fiscal_document_electronic"
            ", ai.document_serie_id as document_serie_id"
            ", ai.revenue_expense as revenue_expense"
            ", partner.l10n_br_city_id as l10n_br_city_id"
            ", partner.state_id as state_id"
        )

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + (
            ", ail.fiscal_category_id"
            ", ai.internal_number"
            ", ai.fiscal_document_electronic"
            ", ai.document_serie_id"
            ", ai.revenue_expense"
            ", partner.l10n_br_city_id"
            ", partner.state_id"
        )
