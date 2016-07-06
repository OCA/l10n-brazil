# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.multi
    @api.depends('fiscal_classification_id')
    def _compute_estimated_taxes(self):
        for template in self:
            template.estimated_taxes = \
                self.env['l10n_br_tax.estimate'].compute_tax_estimate(
                    template)

    estimated_taxes = fields.Float(
        string='Impostos estimados',
        compute=_compute_estimated_taxes,
    )


