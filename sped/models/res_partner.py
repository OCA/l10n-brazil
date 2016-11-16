# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _


class Partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    sped_participante_id = fields.Many2one('sped.participante', 'Participante')
    sped_empresa_id = fields.Many2one('sped.empresa', 'Empresa')

    @api.one
    @api.depends('sped_participante_id')
    def _is_brazilian_partner(self):
        self.is_brazilian_partner = self.sped_participante_id

    is_brazilian_partner = fields.Boolean('Is a Brazilian partner?', compute=_is_brazilian_partner)

    @api.one
    @api.depends('sped_participante_id', 'sped_empresa_id')
    def _is_brazilian_company(self):
        self.is_brazilian_company = self.sped_participante_id and self.sped_empresa_id

    is_brazilian_company = fields.Boolean('Is a Brazilian company?', compute=_is_brazilian_company)
