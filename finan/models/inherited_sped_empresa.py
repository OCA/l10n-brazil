# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

try:
    from pybrasil.data import hoje

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedEmpresa(models.Model):
    _inherit = 'sped.empresa'

    carteira_id = fields.Many2one(
        string='Carteira Padrão',
        comodel_name='finan.carteira',
    )

    carteira_ids = fields.Many2many(
        string='Carteiras Permitidas',
        comodel_name='finan.carteira',
    )

    data_referencia_financeira = fields.Date(
        string='Data de referência financeira',
    )

    def cron_atualiza_data_referencia_financeira(self):
        for empresa in self.env['sped.empresa'].search([]):
            empresa.data_referencia_financeira = str(hoje())
