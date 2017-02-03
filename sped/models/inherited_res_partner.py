# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models


class Partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    sped_participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string=u'Participante',
    )
    sped_empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string=u'Empresa')
    is_brazilian_partner = fields.Boolean(
        string=u'Is a Brazilian partner?',
        compute='_compute_is_brazilian_partner',
        store=True,
    )
    is_brazilian_company = fields.Boolean(
        string=u'Is a Brazilian company?',
        compute='_compute_is_brazilian_company',
        store=True,
    )
    original_company_id = fields.Many2one(
        comodel_name='res.company',
        string=u'Original Company',
        compute='_compute_original_company_id',
        store=True,
        ondelete='cascade',
    )
    original_user_id = fields.Many2one(
        comodel_name='res.users',
        string=u'Original User',
        compute='_compute_original_user_id',
        store=True,
        ondelete='cascade'
    )

    @api.depends('sped_participante_id')
    def _compute_is_brazilian_partner(self):
        for partner in self:
            partner.is_brazilian_partner = partner.sped_participante_id

    @api.depends('sped_participante_id', 'sped_empresa_id')
    def _compute_is_brazilian_company(self):
        for partner in self:
            partner.is_brazilian_company = (
                partner.sped_participante_id and
                partner.sped_empresa_id)

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
