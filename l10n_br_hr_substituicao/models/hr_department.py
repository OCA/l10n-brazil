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

    @api.multi
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
        self.ensure_one()
        hr_substituicao_obj = self.env['hr.substituicao']

        substituicao_id = hr_substituicao_obj.search([
            ('department_id', '=', self.id),
            ('data_inicio', '<=', data_referencia),
            ('data_fim', '>=', data_referencia),
        ], limit=1)

        gerente_id = substituicao_id.funcionario_substituto or self.manager_id

        if employee_id == gerente_id:
            return self.parent_id.get_manager_titular(
                data_referencia, employee_id)

        return gerente_id
