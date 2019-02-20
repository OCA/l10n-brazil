# -*- coding: utf-8 -*-
# Copyright 2018 ABGF BR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import MES_DO_ANO


class HrTelefonia(models.Model):
    _name = 'hr.telefonia'
    _rec_name = 'display_name'

    def _get_display_name(self):
        for record in self:
            display_name = "Registros Telefônicos - {} - {}/{}".format(
                record.company_id.display_name or '',
                dict(MES_DO_ANO).get(record.mes), record.ano
            )
            record.display_name = display_name

    display_name = fields.Char(
        compute='_get_display_name'
    )

    arquivo_ligacoes = fields.Binary(
        string='Arquivo Telefonia (PABX)',
        filters='*.csv',
        require=True,
        copy=False,
    )

    arquivo_ramais = fields.Binary(
        string='Listagem de Ramais',
        filters='*.csv',
        require=True,
        copy=False,
    )

    mes = fields.Selection(
        string=u'Mês Competência',
        selection=MES_DO_ANO,
        require=True,
    )

    ano = fields.Char(
        string=u'Ano Competência',
        required=True,
        size=4,
    )

    ligacoes_id = fields.One2many(
        comodel_name='hr.telefonia.line',
        inverse_name='registro_telefonico_id',
    )

    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )

    @api.multi
    def button_buscar_dono_ligacao(self):
        """
        Conciliar ligacoes
        :return:
        """

        ligacoes_sem_dono_id = \
            self.env['hr.telefonia.line'].search([('employee_id','=',False)])

        for ligacoes_id in ligacoes_sem_dono_id:
            funcionario_id = self.env['hr.employee'].search([
                ('ramais', '=', ligacoes_id.ramal.name)])

            if len(funcionario_id) == 1:
                ligacoes_id.employee_id = funcionario_id

    @api.multi
    def button_import_ramais(self):
        """
        Botao habilitado apenas para quem for do grupo de gerenciamento
        técnico pois ira acontecer apenas uma vez
        :return:
        """

        ramal_obj = self.env['hr.ramal']

        for record in self:
            if record.arquivo_ramais:
                # import csv
                import base64
                arq = base64.b64decode(record.arquivo_ramais)
                linhas = arq.splitlines(True)

                for linha in linhas:

                    l = linha.split(',')

                    email_ramal = l[1].strip()
                    numero_ramal = l[2].strip('\n')

                    funcionario_id = self.env['hr.employee'].search([
                        ('work_email','=',email_ramal)])

                    if funcionario_id:

                        ramal_id = ramal_obj.search([
                            ('name','=', numero_ramal)])

                        if not numero_ramal in \
                               funcionario_id.ramais.mapped('name'):

                            if not ramal_id:
                                ramal_id = ramal_obj.create(
                                    {'name': numero_ramal}
                                )

                            funcionario_id.ramais = [(4, ramal_id.id)]

                    else:
                        print ("Nao encontrado funcionario: " + email_ramal)


    @api.multi
    def button_importar_csv(self):
        """
        Botao para importar ligacoes do arquivo CSV fornecido pelo PABX
        :return:
        """

        ramal_obj = self.env['hr.ramal']

        for record in self:
            if record.arquivo_ligacoes:

                # import csv
                import base64

                arq = base64.b64decode(record.arquivo_ligacoes)
                linhas = arq.splitlines(True)

                for linha in linhas:

                    l = linha.split(';')

                    if len(l) > 7 and len(l[0]) == 4 and float(l[7].replace(',','.')) > 0 :
                        name_ramal = l[0]
                        ramal_id = ramal_obj.search([('name', '=', name_ramal)])
                        
                        if not ramal_id:
                            ramal_id = ramal_obj.create({'name': name_ramal})

                        funcionario_id = self.env['hr.employee'].search([
                            ('ramais', '=', name_ramal)
                        ])

                        data = l[1]
                        numero_discado = l[2]
                        concessionaria = l[3]
                        localidade = l[4]
                        inicio = l[5]
                        duracao = l[6]
                        valor = float(l[7].replace(',','.'))

                        # Verificar se a ligacao ja foi importada
                        existe_ligacao = self.env['hr.telefonia.line'].search([
                            ('ramal', '=', ramal_id.id),
                            ('data', '=', data),
                            ('numero_discado', '=', numero_discado),
                            ('inicio', '=', inicio),
                            ('valor', '=', valor),
                        ])

                        if not existe_ligacao:
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
                                'employee_id': funcionario_id.id
                                        if len(funcionario_id) == 1 else False,
                                'company_id': record.company_id.id or False,
                            }
                            self.env['hr.telefonia.line'].create(vals)


class HrTelefoniaLine(models.Model):
    _name = 'hr.telefonia.line'
    _rec_name = 'display_name'
    _order = 'data desc, hora_inicio desc'

    @api.multi
    def _get_telefonia_line_name(self):
        for record in self:
            title = '{} - {}{}'.format(
                record.ramal.name,
                record.employee_id.name.encode('utf-8') + ' - '
                if record.employee_id else '',
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
        readonly=True,
    )

    employee_id = fields.Many2one(
        string='Empregado',
        comodel_name='hr.employee',
    )

    valor = fields.Float(
        string='Valor',
        readonly=True,
    )

    data = fields.Date(
        string='Data',
        required=True,
        readonly=True,
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
        readonly=True,
    )

    hora_inicio = fields.Datetime(
        string='Hora de Início',
        # states={'validate': [('readonly', True)]},
    )

    inicio = fields.Char(
        string='Inicio',
        required=True,
        readonly=True,
    )

    duracao = fields.Char(
        string='Duração da ligação',
        required=True,
        readonly=True,
    )

    numero_discado = fields.Char(
        string='Numero Discado',
        readonly=True,
    )

    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )

    @api.multi
    @api.depends('ramal', 'employee_id')
    def compute_name(self):
        for record in self:
            if record.employee_id and record.ramal:
                record.name = 'Ligação Ramal: {} '.format(record.ramal.name)

    @api.multi
    def set_validate_ligacoes(self):
        """
        Rotina para atestar ligacoes como particulares ou nao
        depois dessa rotina a ligacao sera bloqueada para edicoes
        :return:
        """
        for record in self:
            # Atesta as ligacoes
            record.state = 'validate'

    @api.multi
    def set_particular(self):
        """
        Setar as ligações para particular
        :return:
        """
        for record in self:
            # record.particular = True
            record.tipo = 'particular'


    @api.multi
    def set_empresa(self):
        """
        Setar as ligações como ligações da empresa
        :return:
        """
        for record in self:
            # record.particular = False
            record.tipo = 'empresa'
