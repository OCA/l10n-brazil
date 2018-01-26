# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class L10nBrTaxDefinitionCompanyProduct(L10nBrTaxDefinition, models.Model):
    _name = 'l10n_br_tax.definition.company.product'

    company_id = fields.Many2one('res.company', 'Empresa')
    tax_ipi_guideline_id = fields.Many2one(
        'l10n_br_account_product.ipi_guideline', string=u'Enquadramento IPI')
    tax_icms_relief_id = fields.Many2one(
        'l10n_br_account_product.icms_relief', string=u'Desoneração ICMS')

    _sql_constraints = [
        ('l10n_br_tax_definition_tax_id_uniq',
         'unique (tax_id, company_id)',
         u'Imposto já existente nesta empresa!')
    ]
