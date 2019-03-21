# -*- coding: utf-8 -*-

from odoo import models, fields


class AbstractSpecMixin(models.AbstractModel):
    _description = "Abstract Model"
    _stack_path = ""
    _name = 'abstract.spec.mixin'

    # TODO copy from KMEE ./l10n_br_base/models/sped_base.py, check
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moeda',
        compute='_compute_currency_id',
        default=lambda self: self.env.ref('base.BRL').id,
    )

    def _compute_currency_id(self):
        for item in self:
            item.currency_id = self.env.ref('base.BRL').id
