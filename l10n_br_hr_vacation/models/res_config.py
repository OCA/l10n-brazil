# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class HrConfigSettings(models.TransientModel):
    _inherit = 'hr.config.settings'

    programacao_ferias_futuras = fields.Boolean(
        string=u'Programação Férias Futuras',
        help=u'Permitir apontar as férias, mesmo quando nao tenha saldo de '
             u'dias em seu paríodo aquisitivo'
    )

    @api.model
    def get_default_programacao_ferias_futuras(self, fields):
        return {
            'programacao_ferias_futuras':
                self.env["ir.config_parameter"].get_param(
                    "l10n_br_hr_vacation_programacao_ferias_futuras")
        }

    @api.multi
    def set_programacao_ferias_futuras(self):
        self.ensure_one()
        self.env['ir.config_parameter'].set_param(
            "l10n_br_hr_vacation_programacao_ferias_futuras",
            self.programacao_ferias_futuras or ''
        )
