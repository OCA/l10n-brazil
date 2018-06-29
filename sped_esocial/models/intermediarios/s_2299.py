# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, models, fields


class SpedHrRescisao(models.Model):
    _name = "sped.hr.rescisao"

    name = fields.Char(
        string='name',
    )
    esocial_id = fields.Many2one(
        string="e-Social",
        comodel_name="sped.esocial",
        required=True,
    )
    sped_hr_rescisao_id = fields.Many2one(
        string="Rescisão Trabalhista",
        comodel_name="hr.payroll",
        required=True,
    )
    sped_s2200_registro = fields.Many2one(
        string='Registro S-1050',
        comodel_name='sped.transmissao',
    )
    situacao_s2200 = fields.Selection(
        string="Situação S-1050",
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        related="sped_s2200_registro.situacao",
        readonly=True,
    )
