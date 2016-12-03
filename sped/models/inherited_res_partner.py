# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class Partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    sped_participante_id = fields.Many2one('sped.participante', 'Participante')
    sped_empresa_id = fields.Many2one('sped.empresa', 'Empresa')

    @api.multi
    @api.depends('sped_participante_id')
    def _compute_is_brazilian_partner(self):
        for partner in self:
            partner.is_brazilian_partner = partner.sped_participante_id

    is_brazilian_partner = fields.Boolean('Is a Brazilian partner?', compute='_compute_is_brazilian_partner',
                                          store=True)

    @api.multi
    @api.depends('sped_participante_id', 'sped_empresa_id')
    def _compute_is_brazilian_company(self):
        for partner in self:
            partner.is_brazilian_company = partner.sped_participante_id and partner.sped_empresa_id

    is_brazilian_company = fields.Boolean('Is a Brazilian company?', compute='_compute_is_brazilian_company',
                                          store=True)

    @api.multi
    def _compute_original_company_id(self):
        for partner in self:
            company_ids = self.env['res.company'].search([('partner_id', '=', partner.id)])

            if len(company_ids) > 0:
                partner.original_company_id = company_ids[0]
            else:
                partner.original_company_id = False

    original_company_id = fields.Many2one('res.company', 'Original Company', compute='_compute_original_company_id',
                                          store=True, ondelete='cascade')

    @api.multi
    def _compute_original_user_id(self):
        for partner in self:
            user_ids = self.env['res.users'].search([('partner_id', '=', partner.id)])

            if len(user_ids) > 0:
                partner.original_user_id = user_ids[0]
            else:
                partner.original_user_id = False

    original_user_id = fields.Many2one('res.users', 'Original User', compute='_compute_original_user_id', store=True,
                                       ondelete='cascade')
