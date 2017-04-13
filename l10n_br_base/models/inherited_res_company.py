# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia -
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import fields, models


class Company(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    sped_participante_id = fields.Many2one(
        comdodel_name='sped.participante',
        string=u'Participante',
        related='partner_id.sped_participante_id'
    )
    sped_empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string=u'Empresa',
        related='partner_id.sped_empresa_id'
    )
    is_brazilian_partner = fields.Boolean(
        string=u'Is a Brazilian partner?',
        related='partner_id.sped_participante_id.is_brazilian_partner',
        store=True
    )
    is_brazilian_company = fields.Boolean(
        string=u'Is a Brazilian company?',
        related='partner_id.sped_participante_id.is_brazilian_company',
        store=True
    )
