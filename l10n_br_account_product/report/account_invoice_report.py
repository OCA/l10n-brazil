# -*- coding: utf-8 -*-
# Copyright (C) 2016  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields

from openerp.addons import decimal_precision as dp
from ..models.l10n_br_account_product import PRODUCT_FISCAL_TYPE


class AccountInvoiceReport(models.Model):

    _inherit = "account.invoice.report"

    issuer = fields.Selection(
        [('0', u'Emissão própria'),
         ('1', 'Terceiros')],
        string='Emitente',
        readonly=True
    )
    fiscal_type = fields.Selection(
        PRODUCT_FISCAL_TYPE,
        'Tipo Fiscal'
    )
    cfop_id = fields.Many2one(
        'l10n_br_account_product.cfop',
        'CFOP',
        readonly=True
    )
    icms_value = fields.Float(
        'Valor ICMS',
        required=True,
        digits=dp.get_precision('Account'),
    )
    icms_st_value = fields.Float(
        'Valor ICMS ST',
        required=True,
        digits=dp.get_precision('Account'),
    )
    ipi_value = fields.Float(
        'Valor IPI',
        required=True,
        digits=dp.get_precision('Account'),
    )
    pis_value = fields.Float(
        'Valor PIS',
        required=True,
        digits=dp.get_precision('Account'),
    )
    cofins_value = fields.Float(
        'Valor COFINS',
        required=True,
        digits=dp.get_precision('Account'),
    )
    ii_value = fields.Float(
        'Valor II',
        required=True,
        digits=dp.get_precision('Account'),
    )
    total_with_taxes = fields.Float(
        'Total com Impostos',
        required=True,
        digits=dp.get_precision('Account'),
    )

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + (
            ", sub.issuer as issuer"
            ", sub.fiscal_type as fiscal_type"
            ", sub.cfop_id as cfop_id"
            ", sub.icms_value as icms_value"
            ", sub.icms_st_value as icms_st_value"
            ", sub.ipi_value as ipi_value"
            ", sub.pis_value as pis_value"
            ", sub.cofins_value as cofins_value"
            ", sub.ii_value as ii_value"
            ", sub.total_with_taxes as total_with_taxes"
        )

    def _sub_select(self):
        return super(
            AccountInvoiceReport, self)._sub_select() + (
                ", ai.issuer "
                ", ai.fiscal_type "
                ", ail.cfop_id as cfop_id"
                ", SUM(ail.icms_value) as icms_value"
                ", SUM(ail.icms_st_value) as icms_st_value"
                ", SUM(ail.ipi_value) as ipi_value"
                ", SUM(ail.pis_value) as pis_value"
                ", SUM(ail.cofins_value) as cofins_value"
                ", SUM(ail.ii_value) as ii_value"
                ", SUM("
                "ail.price_subtotal + ail.ipi_value + "
                "ail.icms_st_value + ail.freight_value + "
                "ail.insurance_value + ail.other_costs_value) "
                "as total_with_taxes"
        )

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + (
            ", ai.issuer"
            ", ai.fiscal_type"
            ", ail.cfop_id"
        )
