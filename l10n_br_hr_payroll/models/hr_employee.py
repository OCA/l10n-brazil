# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from openerp.exceptions import Warning as UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    ramais = fields.Many2many(
        comodel_name='hr.ramal',
        relation='employee_ramal_rel',
        column1='ramal_id',
        column2='employee_id',
        string=u'Ramais'
    )

    parent_id = fields.Many2one(
        compute='_compute_gerente_contrato',
        store=True,
    )

    @api.multi
    @api.depends('contract_ids.gerente_id')
    def _compute_gerente_contrato(self):
        for record in self:
            for contract in record.contract_ids.filtered(
                    lambda rec: rec.date_end is False):
                record.parent_id = contract.gerente_id

    @api.multi
    def write(self, vals):
        # Não permitir alterações do cadastro de funcionario.
        # Apenas permitir pelo menu de alteração contratual.
        # O menu de alteração contratual seta uma variavel de contexto para
        # indicar que a modificação partiu de lá.
        #
        # Se a variavel de alteracaocontratual nao for setada validar alteração
        if not self.env.context.get('alteracaocontratual'):
            for dict_key in ['work_location', 'job_id','manager']:
                if dict_key in vals:
                    # Se a variavel nao foi setada ainda, permitir setar via
                    # cadastro de contratoss, se ja estiver definida disparar
                    # erro informando ao usuário para alterar campo pelo
                    # menu de Alteração contratual.
                    if eval('self.'+dict_key):
                        raise UserError(
                            u'Alteração no campo %s só pode ser '
                            u'realizada através do menu '
                            u'Alterações Contratuais' % dict_key)
        return super(HrEmployee, self).write(vals)
