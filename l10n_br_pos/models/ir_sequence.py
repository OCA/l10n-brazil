# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.exceptions import Warning as UserError


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    @api.multi
    def _interpolate_value(self, value):
        self.ensure_one()
        d = self._interpolation_dict_context(context=self.env.context)
        try:
            prefix = self._interpolate(self.prefix, d)
            suffix = self._interpolate(self.suffix, d)
        except ValueError:
            raise UserError(_('Invalid prefix or suffix for sequence \'%s\'') %
                            (seq.get('name'),))
        return "{prefix}{value:0>{padding}}{suffix}".format(
            value=value, prefix=prefix, suffix=suffix, padding=self.padding,
        )
