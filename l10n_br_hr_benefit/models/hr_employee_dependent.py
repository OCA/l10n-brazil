# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from openerp import api, fields, models, _


class HrEmployeeDependent(models.Model):
    _name = b'hr.employee.dependent'
    _inherit = ['hr.employee.dependent', 'mail.thread', 'ir.needaction_mixin']

    @api.multi
    def _compute_beneficios(self):
        for record in self:
            record.benefit_ids = self.env['hr.contract.benefit'].search(
                    [('beneficiary_id', '=', record.partner_id.id)]
                )

    benefit_ids = fields.Many2many(
        comodel_name='hr.contract.benefit',
        string='Benefícios ativos',
        readonly=True,
        compute='_compute_beneficios',
        track_visibility='onchange',
    )
    state = fields.Selection(
        selection=[
            ('to approve', 'A aprovar'),
            ('approved', 'Aprovada'),
        ],
        track_visibility='onchange',
        default='to approve'
    )
    partner_id = fields.Many2one(
        track_visibility='onchange',
    )
    employee_id = fields.Many2one(
        track_visibility='onchange',
    )
    dependent_dob = fields.Date(
        track_visibility='onchange',
    )
    dependent_type_id = fields.Many2one(
        track_visibility='onchange',
    )
    pension_benefits = fields.Float(
        track_visibility='onchange',
    )
    dependent_verification = fields.Boolean(
        track_visibility='onchange',
    )
    health_verification = fields.Boolean(
        track_visibility='onchange',
    )
    dependent_gender = fields.Selection(
        track_visibility='onchange',
    )
    have_alimony = fields.Boolean(
        track_visibility='onchange',
    )
    partner_id_bank_ids = fields.One2many(
        track_visibility='onchange',
    )
    dep_sf = fields.Boolean(
        track_visibility='onchange',
    )
    inc_trab = fields.Boolean(
        track_visibility='onchange',
    )
    inc_trab_inss_file = fields.Binary(
        track_visibility='onchange',
    )
    precisa_cpf = fields.Boolean(
        track_visibility='onchange',
    )
    relative_file = fields.Binary(
        track_visibility='onchange',
    )

    @api.multi
    def button_approve(self):
        for record in self:
            record.state = 'approved'

    @api.multi
    def button_to_approve(self):
        for record in self:
            record.state = 'to approve'


    # has_changes = fields.Boolean(
    #     string='Existem alterações?',
    #     default=True,
    #     track_visibility='onchange',
    # )
    # exception_message = fields.Char(
    #     string='Mensagem de rejeição',
    #     track_visibility='onchange',
    # )
    #
    # @api.multi
    # def write(self, vals):
    #     if self.env.user == self.employee_id.user_id:
    #         vals.update(dict(has_changes=True))
    #     result = super(HrEmployeeDependent, self).write(vals)
    #     return result
    #
    # @api.multi
    # @api.onchange('has_changes')
    # def _onchange_has_changes(self):
    #     for record in self:
    #         if record.has_changes and record.state in ['approved', 'exception']:
    #             record.state = 'has changes'
    #
    # @api.multi
    # def button_send_to_approval(self):
    #     for record in self:
    #         record.state = 'to approve'
    #
    # @api.multi
    # def button_approve(self):
    #     for record in self:
    #         record.state = 'approved'
    #         record.has_changes = False
    #
    # @api.multi
    # def button_exception(self):
    #     for record in self:
    #         record.has_changes = False
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'wizard.benefit.exception.cause',
    #         'view_mode': 'form',
    #         'view_type': 'form',
    #         'res_id': False,
    #         'target': 'new',
    #     }
    #
    # @api.multi
    # def button_back_to_approve(self):
    #     for record in self:
    #         if record.state in 'exception':
    #             record.state = 'has changes'
