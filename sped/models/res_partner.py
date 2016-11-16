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

    is_brazilian_partner = fields.Boolean('Is a Brazilian partner?', compute=_is_brazilian_partner, store=True)

    @api.one
    @api.depends('sped_participante_id', 'sped_empresa_id')
    def _is_brazilian_company(self):
        self.is_brazilian_company = self.sped_participante_id and self.sped_empresa_id

    is_brazilian_company = fields.Boolean('Is a Brazilian company?', compute=_is_brazilian_company, store=True)

    @api.one
    def _original_company_id(self):
        company_ids = self.env['res.company'].search([('partner_id', '=', self.id)])

        if len(company_ids) > 0:
            self.original_company_id = company_ids[0]
        else:
            self.original_company_id = False

    original_company_id = fields.Many2one('res.company', 'Original Company', compute=_original_company_id, store=True, ondelete='cascade')

    @api.one
    def _original_user_id(self):
        user_ids = self.env['res.users'].search([('partner_id', '=', self.id)])

        if len(user_ids) > 0:
            self.original_user_id = user_ids[0]
        else:
            self.original_user_id = False

    original_user_id = fields.Many2one('res.users', 'Original User', compute=_original_user_id, store=True, ondelete='cascade')
