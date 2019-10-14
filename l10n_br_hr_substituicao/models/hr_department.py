# -*- coding: utf-8 -*-
# Copyright 2018 ABGF - Hendrix Costa <hendrix.costa@abgf.gov.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class L10nBrHrDepartment(models.Model):
    _inherit = "hr.department"

    manager_substituto_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Substituto',
        help='Gerente do departamento na falta do gerente oficial.',
    )

    def get_manager_titular(
            self, data_referencia=fields.Date.today(), employee_id=False):
        """
        Função para definir quem é o gerente do departamento de acordo com a
        data de referencia para levar em consideração possíveis substituições.
        O funcionario deverá ser passado como parametro para ser possível
        identificar se o próprio funcionário é o gestor do seu dpto. Em Casos
        positivos chamar a mesma função do departamento pai.
        :return: Gestor do departamento em determinada data
        """
        hr_substituicao_obj = self.env['hr.substituicao']

        gerente_id = self.manager_id

        # Verificar se tem substituição para departamento naquele dia
        substituicao_id = hr_substituicao_obj.search([
            ('department_id', '=', self.id),
            ('data_inicio', '<=', data_referencia),
            ('data_fim', '>=', data_referencia),
        ], limit=1)

        if substituicao_id:

            gerente_id = substituicao_id.funcionario_substituto

            # Verificar se substituto nao esta de folga
            holiday_ids = self.env['hr.holidays'].search([
                ('employee_id', '=', gerente_id.id),
                ('data_inicio', '<=', data_referencia),
                ('data_fim', '>=', data_referencia),
                ('state','=','validate'),
                ('type',' = ','remove'),
                ('tipo', '!=', 'compensacao'),
            ], limit=1)

            # Se substituto estiver de folga,
            # retornar gerente do departamento superior
            if holiday_ids:
                return self.parent_id.get_manager_titular(
                data_referencia, employee_id)

        # Se o gerente do departamento for o proprio usuario consultado
        if employee_id == gerente_id or employee_id == self.manager_id:
            return self.parent_id.get_manager_titular(
                data_referencia, employee_id)

        return gerente_id
