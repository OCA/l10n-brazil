# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from datetime import datetime


class HrContract(models.Model):

    _inherit = 'hr.contract'
    _rec_name = 'nome_contrato'

    codigo_contrato = fields.Char(
        string='Codigo de Identificacao',
        required=True,
        default="/",
        readonly=True
    )

    @api.model
    def create(self, vals):
        if vals.get('codigo_contrato', '/') == '/':
            vals['codigo_contrato'] = self.env['ir.sequence'].get(self._name)
            return super(HrContract, self).create(vals)

    @api.depends('employee_id', 'date_start')
    def _compute_nome_contrato(self):
        for contrato in self:
            nome = contrato.employee_id.name
            inicio_contrato = contrato.date_start
            fim_contrato = contrato.date_end

            if inicio_contrato:
                inicio_contrato = datetime.strptime(inicio_contrato,
                                                    '%Y-%m-%d')
                inicio_contrato = inicio_contrato.strftime('%d/%m/%y')

            if fim_contrato:
                fim_contrato = datetime.strptime(fim_contrato, '%Y-%m-%d')
                fim_contrato = fim_contrato.strftime('%d/%m/%y')
                if fim_contrato > fields.Date.today():
                    fim_contrato = "- D. %s" % fim_contrato
                else:
                    fim_contrato = "- %s" % fim_contrato
            else:
                fim_contrato = ''
            matricula = contrato.codigo_contrato
            nome_contrato = '[%s] %s - %s %s' % (matricula,
                                                 nome, inicio_contrato,
                                                 fim_contrato)
            contrato.nome_contrato = nome_contrato if nome else ''

    nome_contrato = fields.Char(
        default="[mat] nome - inicio - fim",
        compute="_compute_nome_contrato",
        store=True
    )

    @api.multi
    def _buscar_salario_vigente_periodo(self, data_inicio, data_fim):
        contract_change_obj = self.env['l10n_br_hr.contract.change']
        change = contract_change_obj.search(
            [
                ('change_date', '>=', data_inicio),
                ('change_date', '<=', data_fim),
                ('wage', '>', 0),
            ],
            order="change_date DESC",
            limit=1,
        )
        return change.wage

    @api.multi
    def _salario_dia(self, data_inicio, data_fim):
        if data_inicio >= self.date_start and \
                (data_fim <= self.date_end or not self.date_end):
            return self.wage/30
        else:
            return self._buscar_salario_vigente_periodo(
                data_inicio, data_fim)/30

    @api.multi
    def _salario_hora(self, data_inicio, data_fim):
        if data_inicio >= self.date_start and \
                (data_fim <= self.date_end or not self.date_end):
            return self.wage/(
                220 if not self.monthly_hours else self.monthly_hours
            )
        else:
            return self._buscar_salario_vigente_periodo(
                data_inicio, data_fim)/(
                220 if not self.monthly_hours else self.monthly_hours
            )

    @api.multi
    def _salario_mes(self, data_inicio, data_fim):
        if data_inicio >= self.date_start and \
                (data_fim <= self.date_end or not self.date_end):
            return self.wage
        else:
            return self._buscar_salario_vigente_periodo(data_inicio, data_fim)

    specific_rule_ids = fields.One2many(
        comodel_name='hr.contract.salary.rule',
        inverse_name='contract_id',
        string=u"Rúbricas específicas",
    )
    change_salary_ids = fields.One2many(
        comodel_name='l10n_br_hr.contract.change',
        inverse_name='contract_id',
        string=u"Remuneração",
        domain=[
            ('change_type', '=', 'remuneracao')
        ],
    )
    change_workdays_ids = fields.One2many(
        comodel_name='l10n_br_hr.contract.change',
        inverse_name='contract_id',
        string=u"Jornada",
        domain=[
            ('change_type', '=', 'jornada')
        ],
    )
    change_job_ids = fields.One2many(
        comodel_name='l10n_br_hr.contract.change',
        inverse_name='contract_id',
        string=u"Atividade/Cargo",
        domain=[
            ('change_type', '=', 'cargo-atividade')
        ],
    )
    change_labor_union_ids = fields.One2many(
        comodel_name='l10n_br_hr.contract.change',
        inverse_name='contract_id',
        string=u"Filiação Sindical",
        domain=[
            ('change_type', '=', 'filiacao-sindical')
        ],
    )
    change_place_ids = fields.One2many(
        comodel_name='l10n_br_hr.contract.change',
        inverse_name='contract_id',
        string=u"Lotação/Local de trabalho",
        domain=[
            ('change_type', '=', 'filiacao-sindical')
        ],
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.user.company_id or '',
    )

    # Admissão
    tipo_do_contrato = fields.Selection(
        selection=[],
        string="Tipo do contrato"
    )

    tipo_de_admissao = fields.Selection(
        selection=[],
        string="Tipo de admissão"
    )

    indicativo_de_admissao = fields.Selection(
        selection=[('transferencia', u'Trasferência'),
                   ('normal', u'Normal')],
        string="Indicativo da admissão"
    )

    contrato_transferido = fields.Selection(
        selection=[],
        string="Contrato transferido"
    )

    data_da_transferencia = fields.Date(
        string="Data da transferencia"
    )

    seguro_desemprego = fields.Boolean(
        string="Em Seguro Desemprego?"
    )

    primeiro_emprego = fields.Boolean(
        string="Primeiro emprego?"
    )

    primeira_experiencia = fields.Integer(
        string="Tempo em dias do 1º período de experiência"
    )

    data_primeira_experiencia = fields.Date(
        string="Início da primeira experiência"
    )

    segunda_experiencia = fields.Integer(
        string="Tempo em dias do 2º período de experiência"
    )

    data_segunda_experiencia = fields.Date(
        string="Início da segunda experiência"
    )

    # Lotação
    departamento_lotacao = fields.Many2one(
        string="Departamento/lotação",
        comodel_name='hr.department'
    )

    lotacao_cliente_fornecedor = fields.Selection(
        selection=[],
        string="Lotação/cliente/fornecedor"
    )

    # Jornada
    tipo_de_jornada = fields.Selection(
        selection=[],
        string="Tipo de jornada de trabalho"
    )

    jornada_seg_sex = fields.Selection(
        selection=[],
        string="Jornada padrão de segunda a sexta-feira"
    )

    jornada_sab = fields.Selection(
        selection=[],
        string="Jornada no sábado"
    )

    # Aba Vínculos Anteriores e cedentes
    # Vínculo anterior
    cnpj_empregador_anterior = fields.Char(
        string="CNPJ do empregador anterior"
    )

    matricula_anterior = fields.Char(
        string="Matrícula anterior"
    )

    data_admissao_anterior = fields.Date(
        string="Data de admissão no vínculo anterior"
    )

    observacoes_vinculo_anterior = fields.Text(
        string="Observações do vínculo anterior"
    )

    # Vínculo cedente
    cnpj_empregador_cedente = fields.Char(
        string="CNPJ do empregador cedente"
    )

    matricula_cedente = fields.Char(
        string="Matrícula cedente"
    )

    data_admissao_cedente = fields.Date(
        string="Data de admissão no vínculo cedente"
    )

    onus_vinculo_cedente = fields.Selection(
        selection=[],
        string="Ônus para o cedente"
    )

    # Aba Saúde ocupacional
    data_atestado_saude = fields.Date(
        string="Data do atestado de saúde ocupacional"
    )

    numero_crm = fields.Integer(
        string="CRM nº"
    )

    nome_medico_encarregado = fields.Char(
        string="Nome do médico encarregado"
    )

    estado_crm = fields.Selection(
        selection=[],
        string="Estado do CRM"
    )

    # Tree Exames
    exame_ids = fields.One2many(
        comodel_name='hr.exame.medico',
        inverse_name='contract_id',
        string="Exames"
    )

    # Aba Processo judicial
    numero_processo = fields.Integer(
        string="Nº processo judicial"
    )

    nome_advogado_autor = fields.Char(
        string="Advogado do autor do processo"
    )

    nome_advogado_empresa = fields.Char(
        string="Advogado da empresa"
    )

    observacoes_processo = fields.Text(
        string="Observações do processo judicial"
    )

    # Aba Cursos e treinamentos
    curso_ids = fields.One2many(
        comodel_name='hr.curso',
        inverse_name='contract_id',
        string="Cursos"
    )

    # Aba Afastamentos
    afastamento_ids = fields.One2many(
        comodel_name='hr.holidays',
        inverse_name='contrato_id',
        string="Afastamentos"
    )


class Exame(models.Model):
    _name = 'hr.exame.medico'

    name = fields.Char(
        string="Exame"
    )

    data_do_exame = fields.Date(
        string="Data do exame"
    )

    data_de_validade = fields.Date(
        string="Data de validade"
    )

    contract_id = fields.Many2one(
        comodel_name='hr.contract',
    )


class Curso(models.Model):
    _name = 'hr.curso'

    name = fields.Char(
        string="Curso"
    )

    carga_horaria = fields.Integer(
        string="Carga horária"
    )

    inicio_curso = fields.Date(
        string="Início"
    )

    fim_curso = fields.Date(
        string="Encerramento"
    )

    situacao = fields.Selection(
        selection=[],
        string="Situação"
    )

    contract_id = fields.Many2one(
        comodel_name='hr.contract',
    )


class HrHoliday(models.Model):
    _inherit = 'hr.holidays'

    rubrica = fields.Char(
        string="Rubrica"
    )

    periodo = fields.Char(
        string="Data de afastamento"
    )

    valor_inss = fields.Float(
        string="Valor INSS"
    )


class HrContractSalaryUnit(models.Model):
    _inherit = 'hr.contract.salary.unit'

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if name == 'Monthly':
                name = 'Por mês'
            elif name == 'Biweekly':
                name = 'Por 15 dias'
            elif name == 'Weekly':
                name = 'Por semana'
            elif name == 'Daily':
                name = 'Por dia'
            elif name == 'Hourly':
                name = 'Por hora'
            elif name == 'Task':
                name = 'Por tarefa'
            elif name == 'Others':
                name = 'Outros'
            elif record['code']:
                name = record['code'] + ' - ' + name
            result.append((record['id'], name))
        return result
