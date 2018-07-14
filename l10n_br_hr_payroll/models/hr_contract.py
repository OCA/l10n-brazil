# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp import exceptions
from datetime import datetime, timedelta
from ..constantes import CATEGORIA_TRABALHADOR, CATEGORIA_TRABALHADOR_SEFIP


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _rec_name = 'nome_contrato'

    categoria_sefip = fields.Selection(
        selection=CATEGORIA_TRABALHADOR_SEFIP,
        compute='_compute_categoria_sefip',
        store=True,
    )

    categoria = fields.Selection(
        selection=CATEGORIA_TRABALHADOR,
        string="Categoria do Contrato",
        required=True,
        default='101',
    )

    tipo = fields.Selection(
        string='Tipo de vínculo com funcionário',
        selection=[
            ('autonomo', 'Autônomo'),
            ('funcionario', 'Funcionário'),
            ('terceirizado', 'Terceirizado'),
        ],
        default='funcionario',
        help='Tipo basedo no tipo de vínculo com funcionário, '
             'campo utilizado para separação de views.',
    )

    name = fields.Char(
        required=False,
    )

    codigo_contrato = fields.Char(
        string='Codigo de Identificacao',
        required=True,
        default="/",
        readonly=True
    )

    is_editable = fields.Boolean(
        string="Pode Alterar ?",
        compute="_is_editable",
        default=True,
        store=True,
    )
    payslip_ids_confirmados = fields.One2many(
        "hr.payslip",
        "contract_id",
        "Holerites Confirmados",
        domain=[
            ('state', '!=', 'draft'),
            ('is_simulacao', '=', False)
        ]
    )

    @api.multi
    @api.depends('payslip_ids_confirmados', 'payslip_ids_confirmados.state')
    def _is_editable(self):
        for contrato in self:
            if len(contrato.payslip_ids_confirmados) != 0:
                contrato.is_editable = False
            else:
                contrato.is_editable = True

    @api.model
    def create(self, vals):
        if vals.get('codigo_contrato', '/') == '/':
            vals['codigo_contrato'] = self.env['ir.sequence'].get(self._name)
            return super(HrContract, self).create(vals)

    @api.depends('employee_id')
    def _compute_nome_contrato(self):
        for contrato in self:
            nome = contrato.employee_id.name
            matricula = contrato.codigo_contrato
            nome_contrato = '[%s] %s' % (matricula, nome)
            contrato.nome_contrato = nome_contrato if nome else ''

    nome_contrato = fields.Char(
        default="[mat] nome - inicio - fim",
        compute="_compute_nome_contrato",
        store=True
    )

    @api.multi
    def _buscar_salario_vigente_periodo(
            self, data_inicio, data_fim, inicial=False, final=False):
        contract_change_obj = self.env['l10n_br_hr.contract.change']

        #
        # Checa se há alterações contratuais em estado Rascunho
        # Não continua se houver
        #
        change = contract_change_obj.search([
            ('contract_id', '=', self.id),
            ('change_type', '=', 'remuneracao'),
            ('state', '=', 'draft'),
        ], order="change_date DESC",
        )
        if change:
            raise exceptions.ValidationError(
                "Há alteração de remuneração em estado Rascunho "
                "neste contrato, por favor exclua a alteração "
                "contratual ou Aplique-a para torná-la efetiva "
                "antes de calcular um holerite!"
            )

        # Busca todas as alterações de remuneração deste contrato
        #
        change = contract_change_obj.search([
            ('contract_id', '=', self.id),
            ('change_type', '=', 'remuneracao'),
            ('state', '=', 'applied'),
        ], order="change_date DESC",
        )

        # Calcular o salário proporcional dentro do período especificado
        # Pega o salário do contrato caso nunca tenha havido uma alteração
        # contratual
        #
        salario_medio = self.wage
        for i in range(len(change)):

            # Dentro deste período houve alteração contratual ?
            #
            if data_inicio <= change[i].change_date <= data_fim:
                i_2 = i + 1
                data_mudanca = \
                    datetime.strptime(change[i].change_date, "%Y-%m-%d")
                d_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
                d_fim = datetime.strptime(data_fim, "%Y-%m-%d")
                d_fim = d_fim.replace(day=30)

                dias = (d_fim - d_inicio) + timedelta(days=1)

                # Se a alteração salarial for exatamente no primeiro dia do
                # período do holerite, Considere o salário no período inteiro
                #
                if data_mudanca == d_inicio:
                    # if i_2 in range(len(change)):
                    salario_medio = change[i].wage
                    salario_dia_1 = change[i].wage / dias.days
                    salario_dia_2 = change[i].wage / dias.days
                else:

                    # Calcula o número de dias dentro do período e quantos dias
                    # são de cada lado da alteração contratual
                    #
                    dias_2 = (dias.days - data_mudanca.day) + 1
                    dias_1 = data_mudanca.day - d_inicio.day

                    # Calcula cada valor de salário nos dias em com valores
                    # diferentes
                    #
                    salario_dia_2 = change[i].wage / dias.days
                    if i_2 in range(len(change)):
                        salario_dia_1 = change[i_2].wage / dias.days
                    else:
                        salario_dia_1 = change[i].wage / dias.days
                    salario_medio_2 = salario_dia_2 * dias_2
                    salario_medio_1 = salario_dia_1 * dias_1

                    # Soma os 2 lados e temos o salário proporcional dentro
                    # do período
                    #
                    salario_medio = salario_medio_2 + salario_medio_1

                # Se for para buscar o salário inicial
                #
                if inicial:
                    salario_medio = salario_dia_1 * dias.days

                # Se for para buscar o salário final
                #
                if final:
                    salario_medio = salario_dia_2 * dias.days

                break

            # Houve alteração contratual anterior ao período atual
            #
            elif change[i].change_date < data_inicio:
                salario_medio = change[i].wage
                break

        return salario_medio

    @api.multi
    def _salario_dia(self, data_inicio, data_fim):
        return self._salario_mes_proporcional(
            data_inicio, data_fim) / 30

    @api.multi
    def _salario_hora(self, data_inicio, data_fim):
        wage = self._salario_mes_proporcional(data_inicio, data_fim)
        hours_total = 220 if not self.monthly_hours else self.monthly_hours
        return wage / hours_total

    @api.multi
    def _salario_mes(self, data_inicio, data_fim):
        return self._buscar_salario_vigente_periodo(
            data_inicio, data_fim)

    @api.multi
    def _salario_mes_proporcional(self, data_inicio, data_fim):
        return self._buscar_salario_vigente_periodo(
            data_inicio, data_fim)

    @api.multi
    def _salario_mes_inicial(self, data_inicio, data_fim):
        return self._buscar_salario_vigente_periodo(
            data_inicio, data_fim, inicial=True)

    @api.multi
    def _salario_mes_final(self, data_inicio, data_fim):
        return self._buscar_salario_vigente_periodo(
            data_inicio, data_fim, final=True)

    specific_rule_ids = fields.One2many(
        comodel_name='hr.contract.salary.rule',
        inverse_name='contract_id',
        string=u"Rúbricas específicas",
        ondelete='cascade',
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

    indicativo_de_admissao = fields.Selection(
        string=u"Indicativo da admissão",
        selection=[
            ('1', '1-Normal'),
            ('2', '2-Decorrente de Ação Fiscal'),
            ('3', '3-Decorrente de Decisão Judicial'),
        ],
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
        string=u"Tempo em dias do 2º período de experiência"
    )

    data_segunda_experiencia = fields.Date(
        string=u"Início da segunda experiência"
    )

    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Departamento/Lotação',
        related=False,
        readonly=False,
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
        string="CNPJ do empregador"
    )

    matricula_anterior = fields.Char(
        string="Matrícula"
    )

    data_admissao_anterior = fields.Date(
        string="Data de admissão no vínculo"
    )

    observacoes_vinculo_anterior = fields.Text(
        string="Observações do vínculo"
    )

    # Vínculo cedente
    cnpj_empregador_cedente = fields.Char(
        string="CNPJ do empregador"
    )

    matricula_cedente = fields.Char(
        string="Matrícula"
    )

    data_admissao_cedente = fields.Date(
        string="Data de admissão no vínculo"
    )

    adiantamento_13_cedente = fields.Float(
        string=u"Antecipação de 13º na Orgiem R$",
        default=0.0,
    )

    contribuicao_inss_ids = fields.One2many(
        string='Contribuições INSS',
        comodel_name='hr.contribuicao.inss.vinculos',
        inverse_name='contrato_id',
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
    conta_bancaria_id = fields.Many2one(
        string="Conta bancaria",
        comodel_name='res.partner.bank',
    )
    matricula = fields.Char(
        string='Matrícula',
        required=True,
        help="e-Social: S-2299 - matricula"
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


class HrContribuicaoInssVinculos(models.Model):
    _name = "hr.contribuicao.inss.vinculos"

    contrato_id = fields.Many2one(
        string='Contrato',
        comode_name='hr.contract',
        required=True,
    )
    tipo_inscricao_vinculo = fields.Selection(
        string='Tipo do Vínculo',
        selection=[
            ('1', 'CNPJ'),
            ('2', 'CPF'),
        ],
        required=True,
        help='e-Social: S-2299 - tpInsc',
    )
    cnpj_cpf_vinculo = fields.Char(
        string='CNPJ/CPF Vínculo',
        required=True,
        size=17,
        help='e-Social: S-2299 - nrInsc',
    )
    cod_categ_vinculo = fields.Char(
        string='Cód Categoria',
        size=3,
        required=True,
    )
    valor_remuneracao_vinculo = fields.Float(
        string='Remuneração Bruto',
        required=True,
        help='e-Social: S-2299 - vlrRemunOE'
    )
    valor_alicota_vinculo = fields.Float(
        string='Valor Pago',
        required=True,
    )
    period_id = fields.Many2one(
        string='Competência',
        comodel_name='account.period',
        required=True,
    )

    @api.model
    def create(self, vals):
        self._valida_valores_unicos(vals)
        return super(HrContribuicaoInssVinculos, self).create(vals)

    @api.multi
    def write(self, vals):
        self._valida_valores_unicos(vals)
        return super(HrContribuicaoInssVinculos, self).write(vals)

    @api.multi
    def _valida_valores_unicos(self, vals):
        domain = [
            (
                'cnpj_cpf_vinculo', '=',
                vals.get('cnpj_cpf_vinculo') or self.cnpj_cpf_vinculo
            ),
            ('period_id', '=', vals.get('period_id') or self.period_id.id),
        ]
        vinculo_ids = self.search(domain)
        if vinculo_ids:
            raise exceptions.Warning(
                'Só é possível uma entrada por vínculo no período selecionado!'
            )
