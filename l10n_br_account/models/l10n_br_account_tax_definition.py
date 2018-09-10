# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields


class L10nBrTaxDefinitionTemplate(object):
    _name = 'l10n_br_tax.definition.template'

    tax_template_id = fields.Many2one(
        comodel_name='account.tax.template',
        string=u'Imposto',
        required=True)

    tax_group_id = fields.Many2one(
        string=u'Tax Group Related',
        related='tax_template_id.tax_group_id',
        readony=True)


class L10nBrTaxDefinition(object):
    _name = 'l10n_br_tax.definition'

    tax_id = fields.Many2one(
        comodel_name='account.tax',
        string='Imposto',
        required=True)

    tax_group_id = fields.Many2one(
        string=u'Tax Group Related',
        related='tax_id.tax_group_id',
        readony=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        string=u'Company',
        related='tax_id.company_id',
        store=True,
        readonly=True)
