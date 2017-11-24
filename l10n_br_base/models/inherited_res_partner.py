# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sped_participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Participante',
    )
    sped_empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
    )
    is_brazilian = fields.Boolean(
        string='Is a Brazilian partner?',
        compute='_compute_is_brazilian',
        store=True,
    )
    original_company_id = fields.Many2one(
        comodel_name='res.company',
        string='Original Company',
        compute='_compute_original_company_id',
        store=True,
        ondelete='cascade',
    )
    original_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Original User',
        compute='_compute_original_user_id',
        store=True,
        ondelete='cascade'
    )

    @api.depends('sped_participante_id')
    def _compute_is_brazilian(self):
        for partner in self:
            partner.is_brazilian = partner.sped_participante_id

    def _compute_original_company_id(self):
        for partner in self:
            company_ids = self.env['res.company'].search(
                [('partner_id', '=', partner.id)])

            if len(company_ids) > 0:
                partner.original_company_id = company_ids[0]
            else:
                partner.original_company_id = False

    def _compute_original_user_id(self):
        for partner in self:
            user_ids = self.env['res.users'].search(
                [('partner_id', '=', partner.id)])

            if len(user_ids) > 0:
                partner.original_user_id = user_ids[0]
            else:
                partner.original_user_id = False
