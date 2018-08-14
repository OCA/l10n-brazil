# -*- coding: utf-8 -*-
# Copyright 2018 ABGF - Hendrix Costa <hendrix.costa@abgf.gov.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class L10nBrHrDepartment(models.Model):
    _inherit = "hr.department"

    manager_substituto_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Substituto',
    )

    @api.multi
    def get_manager_titular(self, data_referencia=fields.Date.today()):
        """

        :param data_referencia:
        :return:
        """
        self.ensure_one()
        hr_substituicao_obj = self.env['hr.substituicao']

        substituicao_id = hr_substituicao_obj.search([
            ('department_id', '=', self.id),
            ('data_inicio', '<=', data_referencia),
            ('data_fim', '>=', data_referencia),
        ], limit=1)

        return substituicao_id.funcionario_substituto or self.manager_id
