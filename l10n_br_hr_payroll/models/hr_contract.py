# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from openerp import api, fields, models
from openerp import exceptions
from pybrasil.data import formata_data

from ..constantes import CATEGORIA_TRABALHADOR_SEFIP


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _rec_name = 'nome_contrato'

    categoria_sefip = fields.Selection(
        selection=CATEGORIA_TRABALHADOR_SEFIP,
        compute='_compute_categoria_sefip',
        inverse='_inverse_categoria_sefip',
        store=True,
    )

    gerar_sefip = fields.Boolean(
        string=u"Gerar Sefip?",
        default=True,
    )

    # categoria = fields.Selection(
    #     selection=CATEGORIA_TRABALHADOR,
    #     string="Categoria do Contrato",
    #     required=True,
    #     default='101',
    # )

    category_id = fields.Many2one(
        comodel_name='hr.contract.category',
        string="Categoria do Contrato",
        required=True,
        ondelete="restrict",
    )

    category_code = fields.Char(
        string="Código da Categoria de Contrato",
        related='category_id.code',
        readonly=True,
    )

    type_id = fields.Many2one(
        comodel_name='hr.contract.type',
        required=False,
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

    payslip_autonomo_ids_confirmados = fields.One2many(
        comodel_name="hr.payslip.autonomo",
        inverse_name="contract_id",
        string="Holerites Confirmados",
        domain=[
            ('state', '!=', 'draft'),
            ('is_simulacao', '=', False),
        ]
    )

    # Desativar o required para contratos de autonomos que nao eh obrigatório
    wage = fields.Float(
        required=False,
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

    @api.depends('employee_id', 'matricula', 'date_start', 'date_end')
    def _compute_nome_contrato(self):
        for contrato in self:
            if contrato.employee_id and contrato.matricula:
                nome = contrato.employee_id.name
                nome_contrato = '[%s] %s' % (contrato.matricula, nome)
                contrato.nome_contrato = nome_contrato if nome else ''
            if contrato.tipo == 'autonomo' and \
                    contrato.employee_id and contrato.date_start:
                nome = contrato.employee_id.name
                nome_contrato = '%s - [%s]' % \
                                (nome, formata_data(contrato.date_start))
                contrato.nome_contrato = nome_contrato if nome else ''
                if contrato.date_end:
                    nome_contrato = nome_contrato.replace(
                        ']', ' - ' + formata_data(contrato.date_end) + ']')
                    contrato.nome_contrato = nome_contrato

    nome_contrato = fields.Char(
        default="[mat] nome - inicio - fim",
        compute="_compute_nome_contrato",
        store=True,
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
            ('change_type', '=', 'lotacao-local')
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
        domain="[('state', '=', 'ativo')]",
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
        string="CNPJ do empregador",
        help = 'e-Social: S2300 - cnpjCednt',
    )

    matricula_cedente = fields.Char(
        string="Matrícula no cedente",
        help = 'e-Social: S2300 - matricCed',
    )

    data_admissao_cedente = fields.Date(
        string="Data de admissão no vínculo",
        help='e-Social: S2300 - dtAdmCed',
    )

    tpRegTrab = fields.Selection(
        string="Tipo de regime trabalhista no cedente",
        selection=[
            (1, 'CLT - Consolidação das Leis de Trabalho e'
                ' legislações trabalhistas específicas'),
            (2, 'Estatutário.'),
        ],
        help='e-Social: S2300 - tpRegTrab',
    )

    tpRegPrev = fields.Selection(
        string="Tipo de regime previdenciário",
        selection=[
            (1, 'Regime Geral da Previdência Social - RGPS'),
            (2, 'Regime Próprio de Previdência Social - RPPS'),
            (3, 'Regime de Previdência Social no Exterior'),
        ],
        help='e-Social: S2300 - tpRegPrev',
    )

    infOnus = fields.Selection(
        string="Ônus da cessão/requisição",
        selection=[
            (1, 'Ônus do Cedente'),
            (2, 'Ônus do Cessionário'),
            (3, 'Ônus do Cedente e Cessionário'),
        ],
        help='e-Social: S2300 - categOrig',
    )

    # categoria_cedente = fields.Selection(
    #     selection=CATEGORIA_TRABALHADOR,
    #     string="Categoria do Contrato no cedente",
    #     help='e-Social: S2300 - categOrig',
    # )

    assignor_category_id = fields.Many2one(
        comodel_name='hr.contract.category',
        string="Categoria do Contrato no cedente",
        help='e-Social: S2300 - categOrig',
        ondelete="restrict",
    )

    funcionario_cedido = fields.Boolean(
        string=u'Funcionário cedido?'
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

    # Aba Afastamentos
    ocorrencia_add_ids = fields.One2many(
        comodel_name='hr.holidays',
        inverse_name='contrato_id',
        string="Ocorrências (add)",
        domain = [('type', '=', 'add'), ('tipo', 'not in', ['ferias', 'compensacao'])],
    )

    ocorrencia_remove_ids = fields.One2many(
        comodel_name='hr.holidays',
        inverse_name='contrato_id',
        string="Ocorrências",
        domain=[('type', '=', 'remove'), ('tipo', 'not in', ['ferias', 'compensacao'])],
    )

    conta_bancaria_id = fields.Many2one(
        string="Conta bancaria",
        comodel_name='res.partner.bank',
    )
    matricula = fields.Char(
        string='Matrícula',
        help="e-Social: S-2299 - matricula",
        default=lambda self: self.get_default_matricula(),
    )

    gerente_id = fields.Many2one(
        string='Gerente',
        comodel_name='hr.employee',
        compute='compute_gerente_id',
        store=True,
    )

    hr_payroll_type_ids = fields.Many2many(
        comodel_name="hr.payroll.type",
        relation='hr_contract_hr_payroll_type_rel',
        column1='hr_contract_id',
        column2='hr_payroll_type_id',
        string='Compor qual tipo de Lote?',
        help='Indica se a busca de contratos do lote de holerites, deverá '
             'relacionar esse contrato.',
    )

    @api.multi
    def _inverse_categoria_sefip(self):
        for record in self:
            pass

    @api.multi
    @api.depends('category_id')
    def _compute_categoria_sefip(self):

        for record in self:
            if record.category_id.code in ('701', '702', '703'):
                #
                # Autônomo
                #
                record.categoria_sefip = '13'
            elif record.category_id.code == '721':
                #
                # Pró-labore
                #
                record.categoria_sefip = '05'
            elif record.category_id.code in ['722','723']:
                #
                # Pró-labore 2
                #
                record.categoria_sefip = '11'
            elif record.category_id.code == '103':
                #
                # Aprendiz
                #
                record.categoria_sefip = '07'
            else:
                record.categoria_sefip = '01'

    def get_default_matricula(self):
        """
        """
        ultima_matricula = self.search([
            ('matricula','!=',False)], limit=1, order='matricula desc'
        )
        matricula = '0' + str(int(ultima_matricula.matricula) + 1)
        return matricula

    @api.depends('department_id')
    @api.multi
    def compute_gerente_id(self):
        """
        :return:
        """
        for record in self:
            record.gerente_id = record.department_id.manager_id
            if record.gerente_id == record.employee_id:
                record.gerente_id = record.department_id.parent_id.manager_id
