# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api
from openerp.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.multi
    @api.depends('fiscal_classification_id', 'origin')
    def _compute_estimated_taxes(self):
        for template in self:
            template.estimated_taxes = \
                self.env['l10n_br_tax.estimate'].compute_tax_estimate(
                    template)

    estimated_taxes = fields.Float(
        string=u'Impostos estimados',
        compute=_compute_estimated_taxes,
        digits_compute=dp.get_precision('Account'),
        store=False,
    )


