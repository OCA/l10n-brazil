# -*- coding: utf-8 -*-

from openerp import api, fields, models


class res_config(models.TransientModel):
    _inherit = 'base.config.settings'

    allow_cnpj_multi_ie = fields.Boolean(
        string=u'Permitir o cadastro de Customers com CNPJs iguais',
        default=False,
    )

    @api.model
    def get_default_allow_cnpj_multi_ie(self, field):
        return {
            'allow_cnpj_multi_ie':
            self.env["ir.config_parameter"].get_param(
                "l10n_br_base_allow_cnpj_multi_ie")
        }

    @api.multi
    def set_allow_cnpj_multi_ie(self):
        for config in self:
            self.env['ir.config_parameter'].set_param(
                "l10n_br_base_allow_cnpj_multi_ie",
                config.allow_cnpj_multi_ie or '')
