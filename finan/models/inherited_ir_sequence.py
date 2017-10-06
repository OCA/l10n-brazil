# -*- coding: utf-8 -*-
#
# Copyright 2017 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    carteira_nosso_numero = fields.Boolean(
        string='Usada em carteiras/nosso número?',
    )
    carteira_remessa = fields.Boolean(
        string='Usada em carteiras/remessa?',
    )
