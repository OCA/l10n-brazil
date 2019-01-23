# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields

from odoo.addons.l10n_br_account.models.l10n_br_account_tax_definition import (
    L10nBrTaxDefinition
)


class L10nBrTaxDefinitionCompanyProduct(L10nBrTaxDefinition):

    cst_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cst',
        string=u'CST',
        domain="[('tax_group_id', '=', tax_group_id)]")

    tax_ipi_guideline_id = fields.Many2one(
        comodel_name='l10n_br_account_product.ipi_guideline',
        string=u'Enquadramento IPI')

    tax_icms_relief_id = fields.Many2one(
        comodel_name='l10n_br_account_product.icms_relief',
        string=u'Desoneração ICMS')

    cest_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cest',
        string=u'CEST')
