# -*- coding: utf-8 -*-
# Copyright 2018 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
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

    @api.multi
    def button_importar_csv(self):
        for record in self:
            if record.arquivo_ligacoes:

                # import csv, sys
                import base64

                arq = base64.b64decode(record.arquivo_ligacoes)
                linhas = arq.splitlines(True)

                for linha in linhas:

                    l = linha.split(';')

                    if len(l) > 7 and len(l[0]) == 4:
                        name_ramal = l[0]
                        ramal = self.env['hr.ramal'].search([('name', '=', name_ramal)])

                        data = l[1]
                        numero_discado = l[2]
                        concessionaria = l[3]
                        localidade = l[4]
                        inicio = l[5]
                        duracao = l[6]
                        valor = l[7]

                        vals = {
                            'ramal': ramal.id if ramal else False,
                            'data': data,
                            'numero_discado': numero_discado,
                            'concessionaria': concessionaria,
                            'localidade': localidade,
                            'inicio': inicio,
                            'duracao': duracao,
                            'registro_telefonico_id': record.id,
                        }

                        self.env['hr.telefonia.line'].create(vals)


class HrTelefoniaLine(models.Model):
    _name = 'hr.telefonia.line'

    ramal = fields.Many2one(
        string='Ramal',
        comodel_name='hr.ramal',
    )

    employee_id = fields.Many2one(
        string='Empregado',
        comodel_name='hr.employee',
    )

    valor = fields.Float(
        string='Valor',
    )

    data = fields.Datetime(
        string='Data e Hora',
        required=True,
    )

    tipo = fields.Selection(
        string='Tipo',
        selection=[
            ('', ''),
            ('particular', 'Particular'),
            ('empresa', 'Empresa')
        ],
        default='empresa',
    )

    registro_telefonico_id = fields.Many2one(
        string='Registro Telefonico',
        comodel_name='hr.telefonia',
        required=True,
    )

    concessionaria = fields.Char(
        string='Concessionária',
    )

    localidade = fields.Char(
        string='Localidade',
    )

    hora_inicio = fields.Datetime(
        string='Hora de Início',
    )

    duracao = fields.Char(
        string='Duração da ligação',
    )
