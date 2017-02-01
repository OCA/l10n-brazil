# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class Company(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    sped_participante_id = fields.Many2one(
        'sped.participante', 'Participante', related='partner_id.sped_participante_id')
    sped_empresa_id = fields.Many2one(
        'sped.empresa', 'Empresa', related='partner_id.sped_empresa_id')
    is_brazilian_partner = fields.Boolean('Is a Brazilian partner?', related='partner_id.sped_participante_id.is_brazilian_partner',
                                          store=True)
    is_brazilian_company = fields.Boolean('Is a Brazilian company?', related='partner_id.sped_participante_id.is_brazilian_company',
                                          store=True)
