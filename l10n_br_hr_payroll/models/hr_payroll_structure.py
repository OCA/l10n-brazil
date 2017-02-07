# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import fields, models


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    ferias = fields.Many2one(
        comodel_name='hr.payroll.structure',
        string='Férias',
        domain=[('tipo_estrutura', '=', 'ferias')],
    )

    tipo_estrutura = fields.Selection(
        selection=[
            ('normal', 'Folha Normal'),
            ('ferias', 'Fériass'),
            ('adiantamento_13', 'Adiantamento do 13º'),
            ('segunda_parcela_13', 'Segunda Parcela do 13º'),
            ('recisao', 'Recisão'),
        ],
        string='Tipo de Estrutura de Salários',
    )
