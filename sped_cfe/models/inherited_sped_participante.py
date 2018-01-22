# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.models.sped_base import SpedBase


class SpedParticipante(SpedBase, models.Model):
    _inherit = b'sped.participante'

    codigo_administradora_cartao = fields.Char(
        string="Código da Administradora"
    )

    eh_administradora_cartao = fields.Boolean(
        string="É Administradora de Cartão?"
    )
