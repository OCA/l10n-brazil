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

        ramal_obj = self.env['hr.ramal']

        for record in self:
            if record.arquivo_ligacoes:

                # import csv
                import base64

                arq = base64.b64decode(record.arquivo_ligacoes)
                linhas = arq.splitlines(True)

                for linha in linhas:

                    l = linha.split(';')

                    if len(l) > 7 and len(l[0]) == 4:
                        name_ramal = l[0]
                        ramal_id = ramal_obj.search([('name', '=', name_ramal)])
                        
                        if not ramal_id:
                            ramal_id = ramal_obj.create({'name': name_ramal})

                        data = l[1]
                        numero_discado = l[2]
                        concessionaria = l[3]
                        localidade = l[4]
                        inicio = l[5]
                        duracao = l[6]
                        valor = float(l[7].replace(',','.'))

                        vals = {
                            'ramal': ramal_id.id,
                            'data': data,
                            'numero_discado': numero_discado,
                            'concessionaria': concessionaria,
                            'localidade': localidade,
                            'inicio': inicio,
                            'duracao': duracao,
                            'valor': valor,
                            'registro_telefonico_id': record.id,
                            'employee_id': ramal_id.hr_employee_ids[0].id if len(ramal_id.hr_employee_ids) == 1 else False
                        }

                        self.env['hr.telefonia.line'].create(vals)


class HrTelefoniaLine(models.Model):
    _name = 'hr.telefonia.line'
    _rec_name = 'display_name'

    @api.multi
    def _get_telefonia_line_name(self):
        for record in self:
            title = '{} - {}{}'.format(
                record.ramal.name,
                record.employee_id.name + ' - ' if record.employee_id else '',
                record.data
            )
            record.display_name = title

    display_name = fields.Char(
        compute='_get_telefonia_line_name'
    )

    name = fields.Char(
        compute='compute_name',
        string=u'Descrição',
        store=True,
    )

    ramal = fields.Many2one(
        string='Ramal',
        comodel_name='hr.ramal',
        required=True,
        # states={'validate': [('readonly', True)]},
    )

    employee_id = fields.Many2one(
        string='Empregado',
        comodel_name='hr.employee',
        # states={'validate': [('readonly', True)]},
    )

    valor = fields.Float(
        string='Valor',
        # states={'validate': [('readonly', True)]},
    )

    data = fields.Date(
        string='Data e Hora',
        required=True,
        # states={'validate': [('readonly', True)]},
    )

    tipo = fields.Selection(
        string='Tipo',
        selection=[
            ('', ''),
            ('particular', 'Particular'),
            ('empresa', 'Empresa')
        ],
        default='empresa',
        # states={'validate': [('readonly', True)]},
    )

    state = fields.Selection(
        string=u'Situação',
        selection=[
            ('open', 'Em aberto'),
            ('validate', 'Atestado'),
            ('paid', 'Debitado'),
        ],
        default='open',
    )

    payslip_id = fields.Many2one(
        comodel_name='hr.payslip',
        string='Holerite',
    )

    registro_telefonico_id = fields.Many2one(
        string='Registro Telefonico',
        comodel_name='hr.telefonia',
        required=True,
        # states={'validate': [('readonly', True)]},
    )

    concessionaria = fields.Char(
        string='Concessionária',
        # states={'validate': [('readonly', True)]},
    )

    localidade = fields.Char(
        string='Localidade',
        # states={'validate': [('readonly', True)]},
    )

    hora_inicio = fields.Datetime(
        string='Hora de Início',
        # states={'validate': [('readonly', True)]},
    )

    inicio = fields.Char(
        string='Inicio',
        required=True,
        # states={'validate': [('readonly', True)]},
    )

    duracao = fields.Char(
        string='Duração da ligação',
        required=True,
        # states={'validate': [('readonly', True)]},
    )

    numero_discado = fields.Char(
        string='Numero Discado',
        # states={'validate': [('readonly', True)]},
    )

    @api.multi
    @api.depends('ramal', 'employee_id')
    def compute_name(self):
        for record in self:
            if record.employee_id and record.ramal:
                record.name = 'Ligação Ramal: {} ({})'.format(
                    record.ramal.name,record.employee_id[0].name[:14])

    @api.multi
    def set_particular(self):
        """
        Setar as ligações para particular
        :return:
        """
        for record in self:
            record.tipo = 'particular'
            record.state = 'validate'
            # record.employee_id = self.env.user.employee_ids[0]

    @api.multi
    def set_empresa(self):
        """
        Setar as ligações como ligações da empresa
        :return:
        """
        for record in self:
            record.tipo = 'empresa'
            record.state = 'validate'
            # record.employee_id = self.env.user.employee_ids[0]
