# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class HrConfigSettings(models.TransientModel):
    _inherit = 'hr.config.settings'

    ferias_proporcionais = fields.Boolean(
        string=u'Férias Proporcionais no Holerite',
        help=u'Calcular as férias proporcionalmente no holerite.'
    )

    @api.model
    def get_default_ferias_proporcionais(self, fields):
        return {
            'ferias_proporcionais':
                self.env["ir.config_parameter"].get_param(
                    "l10n_br_hr_payroll_ferias_proporcionais")
        }

    @api.multi
    def set_ferias_proporcionais(self):
        self.ensure_one()
        self.env['ir.config_parameter'].set_param(
            "l10n_br_hr_payroll_ferias_proporcionais",
            self.ferias_proporcionais or ''
        )
