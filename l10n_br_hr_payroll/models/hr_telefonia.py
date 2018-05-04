# -*- coding: utf-8 -*-
# Copyright 2018 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields
from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import MES_DO_ANO


class HrTelefonia(models.Model):
    _name = 'hr.telefonia'
    _rec_name = 'display_name'

    def _get_display_name(self):
        for record in self:
            display_name = "Registros Telefônicos - {}/{}".format(
                record.mes, record.ano
            )
            record.display_name = display_name

    display_name = fields.Char(
        compute='_get_display_name'
    )

    arquivo_ligacoes = fields.Binary(
        string='Arquivo de retorno',
        filters='*.csv',
        require=True,
        copy=False
    )

    mes = fields.Selection(
        string=u'Mês Competência',
        selection=MES_DO_ANO,
        require=True
    )

    ano = fields.Char(
        string=u'Ano Competência',
        required=True,
        size=4
    )

    ligacoes_id = fields.One2many(
        comodel_name='hr.telefonia.line',
        inverse_name='registro_telefonico_id'
    )


class HrTelefoniaLine(models.Model):
    _name = 'hr.telefonia.line'

    ramal = fields.Many2one(
        string='Ramal',
        comodel_name='hr.ramal',
        required=True
    )

    employee_id = fields.Many2one(
        string='Empregado',
        comodel_name='hr.employee'
    )

    valor = fields.Float(
        string='Valor'
    )

    data = fields.Datetime(
        string='Data e Hora',
        required=True
    )

    tipo = fields.Selection(
        string='Tipo',
        selection=[
            ('particular', 'Particular'),
            ('empresa', 'Empresa')
        ]
    )

    registro_telefonico_id = fields.Many2one(
        string='Registro Telefonico',
        comodel_name='hr.telefonia',
        required=True
    )
