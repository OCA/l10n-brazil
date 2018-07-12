# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from datetime import datetime


class SpedEsocial(models.Model):
    _name = 'sped.esocial'
    _description = 'Eventos Periódicos e-Social'
    _rec_name = 'nome'
    _order = "nome DESC"
    _sql_constraints = [
        ('periodo_company_unique', 'unique(periodo_id, company_id)', 'Este período já existe para esta empresa !')
    ]

    nome = fields.Char(
        string='Nome',
        compute='_compute_nome',
        store=True,
    )
    nome_readonly = fields.Char(
        string='Nome',
        compute='_compute_readonly',
    )
    periodo_id = fields.Many2one(
        string='Período',
        comodel_name='account.period',
    )
    periodo_id_readonly = fields.Many2one(
        string='Período',
        comodel_name='account.period',
        compute='_compute_readonly',
    )
    date_start = fields.Date(
        string='Início do Período',
        related='periodo_id.date_start',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    company_id_readonly = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
        compute='_compute_readonly',
    )
    situacao = fields.Selection(
        string='Situação',
        selection=[
            ('1', 'Aberto'),
            ('2', 'Precisa Retificar'),
            ('3', 'Fechado')
        ],
        default='1',
        #compute='_compute_situacao',
        store=True,
    )

    # Controle dos registros S-1000
    empregador_ids = fields.Many2many(
        string='Empregadores',
        comodel_name='sped.empregador',
    )
    necessita_s1000 = fields.Boolean(
        string='Necessita S-1000(s)',
        compute='compute_necessita_s1000',
    )

    #
    # Calcula se é necessário criar algum registro S-1000
    #
    @api.depends('empregador_ids.situacao_esocial')
    def compute_necessita_s1000(self):
        for esocial in self:
            necessita_s1000 = False
            for empregador in esocial.empregador_ids:
                if empregador.situacao_esocial in ['2']:
                    necessita_s1000 = True
            esocial.necessita_s1000 = necessita_s1000

    @api.multi
    def importar_empregador(self):
        self.ensure_one()

        empregadores = self.env['sped.empregador'].search([
            ('company_id', '=', self.company_id.id),
        ])
        for empregador in empregadores:
            if empregador.id not in self.empregador_ids.ids:
                if empregador.situacao_esocial != '9':
                    self.empregador_ids = [(4, empregador.id)]

    # Cria o registro S-1000
    @api.multi
    def criar_s1000(self):
        self.ensure_one()
        for empregador in self.empregador_ids:
            empregador.atualizar_esocial()

    #
    # Controle dos registros S-1005
    #
    estabelecimento_ids = fields.Many2many(
        string='Estabelecimentos',
        comodel_name='sped.estabelecimentos',
    )
    necessita_s1005 = fields.Boolean(
        string='Necessita S-1005(s)',
        compute='compute_necessita_s1005',
    )

    # Calcula se é necessário criar algum registro S-1005
    @api.depends('estabelecimento_ids.situacao_esocial')
    def compute_necessita_s1005(self):
        for esocial in self:
            necessita_s1005 = False
            for estabelecimento in esocial.estabelecimento_ids:
                if estabelecimento.situacao_esocial in ['2']:
                    necessita_s1005 = True
            esocial.necessita_s1005 = necessita_s1005

    @api.multi
    def importar_estabelecimentos(self):
        self.ensure_one()

        estabelecimentos = self.env['sped.estabelecimentos'].search([
            ('company_id', '=', self.company_id.id),
        ])
        for estabelecimento in estabelecimentos:
            if estabelecimento.id not in self.estabelecimento_ids.ids:
                if estabelecimento.situacao_esocial != '9':
                    self.estabelecimento_ids = [(4, estabelecimento.id)]

    # Cria os registros S-1005
    @api.multi
    def criar_s1005(self):
        self.ensure_one()
        for estabelecimento in self.estabelecimento_ids:
            estabelecimento.atualizar_esocial()

    # Controle de registros S-1010
    rubrica_ids = fields.Many2many(
        string='Rubricas',
        comodel_name='sped.esocial.rubrica',
        inverse_name='esocial_id',
    )
    necessita_s1010 = fields.Boolean(
        string='Necessita S-1010(s)',
        compute='compute_necessita_s1010',
    )

    # Calcula se é necessário criar algum registro S-1010
    @api.depends('rubrica_ids.situacao_esocial')
    def compute_necessita_s1010(self):
        for esocial in self:
            necessita_s1010 = False
            for rubrica in esocial.rubrica_ids:
                if rubrica.situacao_esocial in ['2']:
                    necessita_s1010 = True
            esocial.necessita_s1010 = necessita_s1010

    @api.multi
    def importar_rubricas(self):
        self.ensure_one()

        rubricas = self.env['sped.esocial.rubrica'].search([
            ('company_id', '=', self.company_id.id),
        ])
        for rubrica in rubricas:
            if rubrica.id not in self.rubrica_ids.ids:
                if rubrica.situacao_esocial != '9':
                    self.rubrica_ids = [(4, rubrica.id)]

    @api.multi
    def criar_s1010(self):
        self.ensure_one()
        for rubrica in self.rubrica_ids:
            rubrica.gerar_registro()

    # Controle de registros S-1020
    lotacao_ids = fields.Many2many(
        string='Lotações Tributárias',
        comodel_name='sped.esocial.lotacao',
    )
    necessita_s1020 = fields.Boolean(
        string='Necessita S-1020',
        compute='compute_necessita_s1020',
    )

    # Calcula se é necessário criar algum registro S-1020
    @api.depends('lotacao_ids.situacao_esocial')
    def compute_necessita_s1020(self):
        for esocial in self:
            necessita_s1020 = False
            for lotacao in esocial.lotacao_ids:
                if lotacao.situacao_esocial in ['2']:
                    necessita_s1020 = True
            esocial.necessita_s1020 = necessita_s1020

    @api.multi
    def importar_lotacoes(self):
        self.ensure_one()

        lotacoes = self.env['sped.esocial.lotacao'].search([
            ('company_id', '=', self.company_id.id),
        ])
        for lotacao in lotacoes:
            if lotacao.id not in self.lotacao_ids.ids:
                if lotacao.situacao_esocial != '9':
                    self.lotacao_ids = [(4, lotacao.id)]

        # lotacoes = self.env['res.company'].search([
        #     '|',
        #     ('id', '=', self.company_id.id),
        #     ('matriz', '=', self.company_id.id),
        # ])
        #
        # for lotacao in lotacoes:
        #     incluir = True
        #     for empresa in self.lotacao_ids:
        #         if empresa.lotacao_id == lotacao:
        #             incluir = False
        #
        #     if incluir:
        #         # Criar uma nova lotacao neste período
        #         vals = {
        #             'company_id': self.company_id.id,
        #             'lotacao_id': lotacao.id,
        #         }
        #         lotacao_id = self.env['sped.esocial.lotacao'].create(vals)
        #         self.lotacao_ids = [(4, lotacao_id.id)]

    @api.multi
    def criar_s1020(self):
        self.ensure_one()
        for lotacao in self.lotacao_ids:
            lotacao.gerar_registro()

    # Calcula se é necessário criar algum registro S-1020
    @api.depends('lotacao_ids.situacao_esocial')
    def compute_necessita_s1020(self):
        for esocial in self:
            necessita_s1020 = False
            for lotacao in esocial.lotacao_ids:
                if lotacao.situacao_esocial in ['2']:
                    necessita_s1020 = True
            esocial.necessita_s1020 = necessita_s1020

    # Controle de registros S-1030
    cargo_ids = fields.Many2many(
        string='Cargos',
        comodel_name='sped.esocial.cargo',
    )
    necessita_s1030 = fields.Boolean(
        string='Necessita S-1030',
        compute='compute_necessita_s1030',
    )

    # Calcula se é necessário criar algum registro S-1030
    @api.depends('cargo_ids.situacao_esocial')
    def compute_necessita_s1030(self):
        for esocial in self:
            necessita_s1030 = False
            for cargo in esocial.cargo_ids:
                if cargo.situacao_esocial in ['2']:
                    necessita_s1030 = True
            esocial.necessita_s1030 = necessita_s1030

    @api.multi
    def importar_cargos(self):
        self.ensure_one()

        cargos = self.env['sped.esocial.cargo'].search([
            ('company_id', '=', self.company_id.id),
        ])
        for cargo in cargos:
            if cargo.id not in self.cargo_ids.ids:
                if cargo.situacao_esocial != '9':
                    self.cargo_ids = [(4, cargo.id)]

    # Criar registros S-1030
    @api.multi
    def criar_s1030(self):
        self.ensure_one()
        for cargo in self.cargo_ids:
            cargo.gerar_registro()

    # Controle de registros S-1050
    turno_trabalho_ids = fields.Many2many(
        string='Turnos de Trabalho',
        comodel_name='sped.hr.turnos.trabalho',
    )
    necessita_s1050 = fields.Boolean(
        string='Necessita S-1050',
        compute='compute_necessita_s1050',
    )

    # Calcula se é necessário criar algum registro S-1050
    @api.depends('turno_trabalho_ids.situacao_esocial')
    def compute_necessita_s1050(self):
        for esocial in self:
            necessita_s1050 = False
            for turno in esocial.turno_trabalho_ids:
                if turno.situacao_esocial in ['2']:
                    necessita_s1050 = True
            esocial.necessita_s1050 = necessita_s1050

    @api.multi
    def importar_turnos_trabalho(self):
        self.ensure_one()

        turnos_trabalho_ids = self.env['sped.hr.turnos.trabalho'].search([
            ('company_id', '=', self.company_id.id),
        ])

        for turno_trabalho in turnos_trabalho_ids:
            if turno_trabalho.id not in self.turno_trabalho_ids.ids:
                if turno_trabalho.situacao_esocial != '9':
                    self.turno_trabalho_ids = [(4, turno_trabalho.id)]

    # Criar registros S-1050
    @api.multi
    def criar_s1050(self):
        self.ensure_one()
        for turno in self.turno_trabalho_ids:
            turno.gerar_registro()

    # Controle de registros S-1200
    remuneracao_ids = fields.Many2many(
        string='Remuneração de Trabalhador',
        comodel_name='sped.esocial.remuneracao',
    )

    # Controle de registros S-1202
    remuneracao_rpps_ids = fields.Many2many(
        string='Remuneração de Servidor (RPPS)',
        comodel_name='sped.esocial.remuneracao.rpps',
    )

    @api.multi
    def importar_remuneracoes(self):
        self.ensure_one()

        # TODO
        # Buscar todos os hr.payslip do período e marcar quais hr.employees tiveram quaisquer hr.payslip
        # Adicionar no sped.esocial.remuneracao um registro para cada employee com hr.payslip
        # Atualizar os campos do sped.esocial.remuneracao caso tenha havido algum hr.payslip ou hr.contract novo
        # Levar em consideração a empresa matriz e todas as filiais
        # Ignorar o código abaixo

        # Buscar Trabalhadores
        trabalhadores = self.env['hr.employee'].search([])

        periodo = self.periodo_id
        matriz  = self.company_id
        empresas = self.env['res.company'].search([('matriz', '=', matriz.id)]).ids
        if matriz.id not in empresas:
            empresas.append(matriz.id)

        # separa somente os trabalhadores com contrato válido neste período e nesta empresa matriz
        # trabalhadores_com_contrato = []
        for trabalhador in trabalhadores:

            # Localiza os contratos válidos deste trabalhador
            domain = [
                ('employee_id', '=', trabalhador.id),
                ('company_id', 'in', empresas),
                ('date_start', '<=', periodo.date_start),
            ]
            contratos = self.env['hr.contract'].search(domain)
            contratos_validos = []

            # Se algum contrato tiver data de término menor que a data inicial do período, tira ele
            # adiciona o trabalhador na lista de trabalhadores_com_contrato
            for contrato in contratos:
                if not contrato.date_end or contrato.date_end >= periodo.date_stop:

                    # TODO Separar os tipos de contratos que importam para o S-1200 somente
                    # trabalhadores_com_contrato.append(trabalhador)
                    contratos_validos.append(contrato.id)

            # Se tiver algum contrato válido, cria o registro s1200
            if contratos_validos:

                # Calcula campos de mês e ano para busca dos payslip
                mes = datetime.strptime(self.periodo_id.date_start, '%Y-%m-%d').month
                ano = datetime.strptime(self.periodo_id.date_start, '%Y-%m-%d').year

                # Busca os payslips de pagamento mensal deste trabalhador
                domain_payslip = [
                    ('company_id', 'in', empresas),
                    ('contract_id', 'in', contratos_validos),
                    ('mes_do_ano', '=', mes),
                    ('ano', '=', ano),
                    ('state', 'in', ['verify', 'done']),
                    ('tipo_de_folha', 'in', ['normal', 'ferias', 'decimo_terceiro']),
                ]
                payslips = self.env['hr.payslip'].search(domain_payslip)

                # Se tem payslip, cria o registro S-1200
                if payslips:

                    # Verifica se o registro S-1200 já existe, cria ou atualiza
                    domain_s1200 = [
                        ('company_id', '=', matriz.id),
                        ('trabalhador_id', '=', trabalhador.id),
                        ('periodo_id', '=', periodo.id),
                    ]
                    s1200 = self.env['sped.esocial.remuneracao'].search(domain_s1200)
                    if not s1200:
                        vals = {
                            'company_id': matriz.id,
                            'trabalhador_id': trabalhador.id,
                            'periodo_id': periodo.id,
                            'contract_ids': [(6, 0, contratos.ids)],
                            'payslip_ids': [(6, 0, payslips.ids)],
                        }
                        s1200 = self.env['sped.esocial.remuneracao'].create(vals)
                    else:
                        s1200.contract_ids = [(6, 0, contratos.ids)]
                        s1200.payslip_ids = [(6, 0, payslips.ids)]

                    # Relaciona o s1200 com o período do e-Social
                    self.remuneracao_ids = [(4, s1200.id)]

                    # Cria o registro de transmissão sped (se ainda não existir)
                    s1200.atualizar_esocial()

    @api.multi
    def importar_remuneracoes_rpps(self):
        self.ensure_one()

        # TODO
        # Buscar todos os hr.payslip do período e marcar quais hr.employees tiveram quaisquer hr.payslip
        # Adicionar no sped.esocial.remuneracao um registro para cada employee com hr.payslip
        # Atualizar os campos do sped.esocial.remuneracao caso tenha havido algum hr.payslip ou hr.contract novo
        # Levar em consideração a empresa matriz e todas as filiais
        # Ignorar o código abaixo

        # Buscar Trabalhadores
        trabalhadores = self.env['hr.employee'].search([])

        periodo = self.periodo_id
        matriz  = self.company_id
        empresas = self.env['res.company'].search([('matriz', '=', matriz.id)]).ids
        if matriz.id not in empresas:
            empresas.append(matriz.id)

        # separa somente os trabalhadores com contrato válido neste período e nesta empresa matriz
        # trabalhadores_com_contrato = []
        for trabalhador in trabalhadores:

            # Localiza os contratos válidos deste trabalhador
            domain = [
                ('employee_id', '=', trabalhador.id),
                ('company_id', 'in', empresas),
                ('date_start', '<=', periodo.date_start),
            ]
            contratos = self.env['hr.contract'].search(domain)
            contratos_validos = []

            # Se algum contrato tiver data de término menor que a data inicial do período, tira ele
            # adiciona o trabalhador na lista de trabalhadores_com_contrato
            for contrato in contratos:
                if not contrato.date_end or contrato.date_end >= periodo.date_stop:

                    # TODO Separar os tipos de contratos que importam para o S-1200 somente
                    # trabalhadores_com_contrato.append(trabalhador)
                    contratos_validos.append(contrato.id)

            # Se tiver algum contrato válido, cria o registro s1200
            if contratos_validos:

                # Calcula campos de mês e ano para busca dos payslip
                mes = datetime.strptime(self.periodo_id.date_start, '%Y-%m-%d').month
                ano = datetime.strptime(self.periodo_id.date_start, '%Y-%m-%d').year

                # Busca os payslips de pagamento mensal deste trabalhador
                domain_payslip = [
                    ('company_id', 'in', empresas),
                    ('contract_id', 'in', contratos_validos),
                    ('mes_do_ano', '=', mes),
                    ('ano', '=', ano),
                    ('state', 'in', ['verify', 'done']),
                    ('tipo_de_folha', 'in', ['normal', 'ferias', 'decimo_terceiro']),
                ]
                payslips = self.env['hr.payslip'].search(domain_payslip)

                # Se tem payslip, cria o registro S-1200
                if payslips:

                    # Verifica se o registro S-1200 já existe, cria ou atualiza
                    domain_s1202 = [
                        ('company_id', '=', matriz.id),
                        ('trabalhador_id', '=', trabalhador.id),
                        ('periodo_id', '=', periodo.id),
                    ]
                    s1202 = self.env['sped.esocial.remuneracao'].search(domain_s1200)
                    if not s1202:
                        vals = {
                            'company_id': matriz.id,
                            'trabalhador_id': trabalhador.id,
                            'periodo_id': periodo.id,
                            'contract_ids': [(6, 0, contratos.ids)],
                            'payslip_ids': [(6, 0, payslips.ids)],
                        }
                        s1202 = self.env['sped.esocial.remuneracao'].create(vals)
                    else:
                        s1202.contract_ids = [(6, 0, contratos.ids)]
                        s1202.payslip_ids = [(6, 0, payslips.ids)]

                    # Relaciona o s1202 com o período do e-Social
                    self.remuneracao_ids = [(4, s1202.id)]

                    # Cria o registro de transmissão sped (se ainda não existir)
                    s1202.atualizar_esocial()

    @api.multi
    def get_esocial_vigente(self, company_id=False):
        """
        Buscar o esocial vigente, se não existir um criar-lo
        :return:
        """
        if not company_id:
            raise ValidationError('Não existe o registro de uma empresa!')
        # Buscar o periodo vigente
        periodo_atual_id = self.env['account.period'].find()
        esocial_id = self.search([
            ('periodo_id', '=', periodo_atual_id.id),
            ('company_id', '=', company_id.id)
        ])

        if esocial_id:
            return esocial_id

        esocial_id = self.create(
            {
                'periodo_id': periodo_atual_id.id,
                'company_id': company_id.id,
            }
        )

        return esocial_id

    @api.depends('periodo_id', 'company_id', 'nome')
    def _compute_readonly(self):
        for esocial in self:
            esocial.nome_readonly = esocial.nome
            esocial.periodo_id_readonly = esocial.periodo_id
            esocial.company_id_readonly = esocial.company_id

    @api.depends('periodo_id', 'company_id')
    def _compute_nome(self):
        for esocial in self:
            nome = esocial.periodo_id.name
            if esocial.company_id:
                nome += '-' + esocial.company_id.name
            if esocial.periodo_id:
                nome += ' (' + esocial.periodo_id.name + ')'
            esocial.nome = nome
