# -*- coding: utf-8 -*-
# @ 2018 KMEE INFORMATICA LTDA - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class L10nBrBaseResConfig(models.TransientModel):
    _inherit = 'l10n_br_base.config.settings'

    check_gtin = fields.Boolean(
        string='Valida EAN/GTIN',
    )

    @api.model
    def get_default_check_gtin(self, field):
        return {
            'check_gtin':
                self.env["ir.config_parameter"].get_param(
                    "l10n_br_base_check_gtin")
        }

    @api.multi
    def set_check_gtin(self):
        for config in self:
            self.env['ir.config_parameter'].set_param(
                "l10n_br_base_check_gtin",
                config.check_gtin or '')
