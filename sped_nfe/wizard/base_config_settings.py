# -*- coding: utf-8 -*-
#
# Copyright 2018 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
from odoo import api, models, fields
from odoo.tools import config


class BaseConfigSettings(models.TransientModel):
    _inherit = 'base.config.settings'

    pasta_contabilidade = fields.Char(
        string='Pasta da contabilidade',
        default=config['data_dir']
    )

    @api.multi
    def set_pasta_contabilidade_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'base.config.settings',
            'pasta_contabilidade',
            self.pasta_contabilidade
        )
