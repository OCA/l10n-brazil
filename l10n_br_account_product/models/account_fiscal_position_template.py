# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields

from openerp.addons.l10n_br_account_product.models.product import \
    PRODUCT_ORIGIN


class AccountFiscalPositionTemplate(models.Model):
    _inherit = 'account.fiscal.position.template'

    cfop_id = fields.Many2one('l10n_br_account_product.cfop', 'CFOP')
    ind_final = fields.Selection([
        ('0', u'Não'),
        ('1', u'Sim')
    ], u'Operação com Consumidor final', readonly=True,
        states={'draft': [('readonly', False)]}, required=False,
        help=u'Indica operação com Consumidor final.', default='0')


class AccountFiscalPositionTaxTemplate(models.Model):
    _inherit = 'account.fiscal.position.tax.template'

    fiscal_classification_id = fields.Many2one(
        'account.product.fiscal.classification.template', 'NCM')
    cest_id = fields.Many2one('l10n_br_account_product.cest', 'CEST')
    tax_ipi_guideline_id = fields.Many2one(
        'l10n_br_account_product.ipi_guideline', string=u'Enquadramento IPI')
    tax_icms_relief_id = fields.Many2one(
        'l10n_br_account_product.icms_relief', string=u'Desoneração ICMS')
    origin = fields.Selection(PRODUCT_ORIGIN, 'Origem',)
