# -*- coding: utf-8 -*-
# Copyright 2018 ABGF - Hendrix Costa <hendrix.costa@abgf.gov.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    gerente_titular = fields.Many2one(
        string='Gerente Titular',
        comodel_name='hr.employee',
        help='Gerente no momento da criação do Holiday',
        compute='_compute_gerente_titular',
        inverse='_inverse_gerente_titular',
        store=True,
    )

    @api.multi
    def _inverse_gerente_titular(self):
        """
        Desbloquear campo readonly
        """
        pass

    @api.multi
    @api.depends('department_id')
    def _compute_gerente_titular(self):
        """
        Calcular quem é o gerente levando em consideração as substituicoes
        cadastradas no sistema
        """
        for record in self:
            if record.department_id and record.data_inicio:
                record.gerente_titular = record.department_id.\
                    get_manager_titular(record.data_inicio, record.employee_id)
            elif record.type == 'add':
                record.gerente_titular = record.department_id.manager_id

    @api.multi
    def holidays_confirm(self):
        """
        Sobrescrever função do core para levar em consideração o campo que
        identifica o gerente substituto
        """
        for record in self:
            if record.employee_id and record.gerente_titular and \
                    record.gerente_titular.user_id:
                record.message_subscribe_users(
                    user_ids=[record.gerente_titular.user_id.id],
                    subtype_ids=None)
            record.write({'state': 'confirm'})

    @api.multi
    def write(self, vals):
        """
        Método write foi sobrescrito pois a validacao do core, forçava ser
        oficial do RH para conseguir editar o holidays
        :param vals:
        :return:
        """
        holidays_id = super(HrHolidays, self).write(vals)

        # Quando validar o holidays, verificar se precisa criar substituicao
        if vals.get('state') and vals.get('state') in ['validate']:
            # Verificar se o funcionario do holiday, eh gerente de
            # algum departamento
            department_ids = self.env['hr.department'].search([
                ('manager_id', '=', self.employee_id.id),
            ])
            # Se for gestor de algum departamento
            if department_ids:
                # Criar registro de substituicao
                for department_id in department_ids:
                    vals = {
                        'department_id': department_id.id,
                        'data_inicio': self.data_inicio,
                        'data_fim': self.data_fim,
                        'funcionario_titular': department_id.manager_id.id,
                        'funcionario_substituto':
                            department_id.manager_substituto_id.id,
                        'holiday_id': self.id,
                    }
                    substituicao_id = self.env['hr.substituicao'].create(vals)
        return holidays_id
