# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models, fields
from openerp.addons.l10n_br_account.models.l10n_br_account import \
    L10nBrTaxDefinition

class L10nBrBaseCity(models.Model):
    _inherit = 'l10n_br_base.city'

    @api.multi
    @api.depends('city_tax_definition_line.tax_id')
    def _compute_taxes(self):
        for city in self:
            city_taxes = self.env['account.tax']
            for tax in city.city_tax_definition_line:
                city_taxes += tax.tax_id
            city.city_tax_ids = city_taxes

    city_tax_definition_line = fields.One2many(
        'l10n_br_tax.definition.city',
        'l10n_br_base_city_id',
        'Taxes Definitions'
    )
    city_tax_ids = fields.Many2many(
        'account.tax',
        string='City Taxes',
        compute='_compute_taxes',
        store=True
    )


class L10nBrTaxDefinitionCity(L10nBrTaxDefinition, models.Model):
    _name = 'l10n_br_tax.definition.city'

    l10n_br_base_city_id = fields.Many2one(
        'l10n_br_base.city',
        u'Município'
    )

    _sql_constraints = [
        ('l10n_br_tax_definition_tax_id_uniq',
         'unique (tax_id, l10n_br_base_city_id)',
         u'Imposto já existente para esse município!')
    ]
