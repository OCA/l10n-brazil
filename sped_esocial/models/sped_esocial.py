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
    msg_empregador = fields.Char(
        string='Empregador',
        compute='compute_necessita_s1000',
    )

    #
    # Calcula se é necessário criar algum registro S-1000
    #
    @api.depends('empregador_ids')
    def compute_necessita_s1000(self):
        for esocial in self:
            necessita_s1000 = False
            msg_empregador = 'OK'
            if not esocial.empregador_ids:
                msg_empregador = 'Pendente Análise'
            for empregador in esocial.empregador_ids:
                if empregador.situacao_esocial in ['2']:
                    necessita_s1000 = True
                    msg_empregador = 'Pendências não enviadas ao e-Social',
            esocial.necessita_s1000 = necessita_s1000
            esocial.msg_empregador = msg_empregador

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
    msg_estabelecimentos = fields.Char(
        string='Estabelecimentos',
        compute='compute_necessita_s1005',
    )

    # Calcula se é necessário criar algum registro S-1005
    @api.depends('estabelecimento_ids.situacao_esocial')
    def compute_necessita_s1005(self):
        for esocial in self:
            necessita_s1005 = False
            msg_estabelecimentos = False
            for estabelecimento in esocial.estabelecimento_ids:
                if estabelecimento.situacao_esocial in ['2']:
                    necessita_s1005 = True
                    msg_estabelecimentos = 'Pendências não enviadas ao e-Social'
            if not msg_estabelecimentos:
                msg_estabelecimentos = 'OK'
            if esocial.estabelecimento_ids:
                txt = 'Estabelecimento'
                if len(esocial.estabelecimento_ids) > 1:
                    txt += 's'
                msg_estabelecimentos = '{} {} - '.format(len(esocial.estabelecimento_ids), txt) + \
                    msg_estabelecimentos
            esocial.necessita_s1005 = necessita_s1005
            esocial.msg_estabelecimentos = msg_estabelecimentos

    @api.multi
    def importar_estabelecimentos(self):
        self.ensure_one()

        estabelecimentos = self.env['res.company'].search([])
        for estabelecimento in estabelecimentos:
            if estabelecimento.situacao_estabelecimento_esocial not in ['0', '9']:
                sped_estabelecimento = self.env['sped.estabelecimentos'].search([
                    ('company_id', '=', self.company_id.id),
                    ('estabelecimento_id', '=', estabelecimento.id),
                ])
                if not sped_estabelecimento:
                    estabelecimento.atualizar_estabelecimento()
                    sped_estabelecimento = estabelecimento.sped_estabelecimento_id
                self.estabelecimento_ids = [(4, sped_estabelecimento.id)]

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
    msg_rubricas = fields.Char(
        string='Rubricas',
        compute='compute_necessita_s1010',
    )

    # Calcula se é necessário criar algum registro S-1010
    @api.depends('rubrica_ids.situacao_esocial')
    def compute_necessita_s1010(self):
        for esocial in self:
            necessita_s1010 = False
            msg_rubricas = False
            for rubrica in esocial.rubrica_ids:
                if rubrica.situacao_esocial in ['2']:
                    necessita_s1010 = True
                    msg_rubricas = 'Pendências não enviadas ao e-Social'
            if not msg_rubricas:
                msg_rubricas = 'OK'
            if esocial.rubrica_ids:
                txt = 'Rubrica'
                if len(esocial.rubrica_ids) > 1:
                    txt += 's'
                msg_rubricas = '{} {} - '.format(len(esocial.rubrica_ids), txt) + \
                    msg_rubricas
            esocial.necessita_s1010 = necessita_s1010
            esocial.msg_rubricas = msg_rubricas

    @api.multi
    def importar_rubricas(self):
        self.ensure_one()

        # Roda todas as Rubricas que possuem o campo nat_rubr definido (Natureza da Rubrica)
        rubricas = self.env['hr.salary.rule'].search([
            ('nat_rubr', '!=', False),
        ])
        for rubrica in rubricas:

            # Procura o registro intermediário S-1010 correspondente
            s1010 = self.env['sped.esocial.rubrica'].search([
                ('company_id', '=', self.company_id.id),
                ('rubrica_id', '=', rubrica.id),
            ])
            if not s1010:

                # Cria o registro intermediário
                vals = {
                    'company_id': self.company_id.id,
                    'rubrica_id': rubrica.id,
                }
                s1010 = self.env['sped.esocial.rubrica'].create(vals)
                self.rubrica_ids = [(4, s1010.id)]
            else:

                # Adiciona no período o link para o registro S-1010 (se não estiver)
                if s1010.id not in self.rubrica_ids.ids:
                    self.rubrica_ids = [(4, s1010.id)]

            # Gera o registro de transmissão (se for necessário)
            s1010.gerar_registro()

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
    msg_lotacoes_tributarias = fields.Char(
        string='Lotações Tributárias',
        compute='compute_necessita_s1020',
    )

    # Calcula se é necessário criar algum registro S-1020
    @api.depends('lotacao_ids.situacao_esocial')
    def compute_necessita_s1020(self):
        for esocial in self:
            necessita_s1020 = False
            msg_lotacoes_tributarias = False
            for lotacao in esocial.lotacao_ids:
                if lotacao.situacao_esocial in ['2']:
                    necessita_s1020 = True
                    msg_lotacoes_tributarias = 'Pendências não enviadas ao e-Social'
            if not msg_lotacoes_tributarias:
                msg_lotacoes_tributarias = 'OK'
            if esocial.lotacao_ids:
                txt = 'Lotação'
                if len(esocial.lotacao_ids) > 1:
                    txt = 'Lotações'
                msg_lotacoes_tributarias = '{} {} - '.format(len(esocial.lotacao_ids), txt) + \
                    msg_lotacoes_tributarias
            esocial.necessita_s1020 = necessita_s1020
            esocial.msg_lotacoes_tributarias = msg_lotacoes_tributarias

    @api.multi
    def importar_lotacoes(self):
        self.ensure_one()

        lotacoes = self.env['res.company'].search([])
        for lotacao in lotacoes:
            if lotacao.situacao_lotacao_esocial not in ['0', '9']:
                sped_lotacao = self.env['sped.esocial.lotacao'].search([
                    ('company_id', '=', self.company_id.id),
                    ('lotacao_id', '=', lotacao.id),
                ])
                if not sped_lotacao:
                    lotacao.atualizar_lotacao()
                    sped_lotacao = lotacao.sped_estabelecimento_id
                self.lotacao_ids = [(4, sped_lotacao.id)]

    @api.multi
    def criar_s1020(self):
        self.ensure_one()
        for lotacao in self.lotacao_ids:
            lotacao.gerar_registro()

    # Controle de registros S-1030
    cargo_ids = fields.Many2many(
        string='Cargos',
        comodel_name='sped.esocial.cargo',
    )
    necessita_s1030 = fields.Boolean(
        string='Necessita S-1030',
        compute='compute_necessita_s1030',
    )
    msg_cargos = fields.Char(
        string='Cargos',
        compute='compute_necessita_s1030',
    )

    # Calcula se é necessário criar algum registro S-1030
    @api.depends('cargo_ids.situacao_esocial')
    def compute_necessita_s1030(self):
        for esocial in self:
            necessita_s1030 = False
            msg_cargos = False
            for cargo in esocial.cargo_ids:
                if cargo.situacao_esocial in ['2']:
                    necessita_s1030 = True
                    msg_cargos = 'Pendências não enviadas ao e-Social'
            if not msg_cargos:
                msg_cargos = 'OK'
            if esocial.cargo_ids:
                txt = 'Cargo'
                if len(esocial.cargo_ids) > 1:
                    txt += 's'
                msg_cargos = '{} {} - '.format(len(esocial.cargo_ids), txt) + \
                    msg_cargos
            esocial.necessita_s1030 = necessita_s1030
            esocial.msg_cargos = msg_cargos

    @api.multi
    def importar_cargos(self):
        self.ensure_one()

        cargos = self.env['hr.job'].search([
            ('codigo', '!=', False),
        ])
        for cargo in cargos:
            if cargo.situacao_esocial not in ['0', '9']:
                sped_cargo = self.env['sped.esocial.cargo'].search([
                    ('company_id', '=', self.company_id.id),
                    ('cargo_id', '=', cargo.id),
                ])
                if not sped_cargo:
                    cargo.atualizar_cargo()
                    sped_cargo = cargo.sped_cargo_id
                self.cargo_ids = [(4, sped_cargo.id)]

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
    msg_turnos = fields.Char(
        string='Turnos de Trabalho',
        compute='compute_necessita_s1050',
    )

    # Calcula se é necessário criar algum registro S-1050
    @api.depends('turno_trabalho_ids.situacao_esocial')
    def compute_necessita_s1050(self):
        for esocial in self:
            necessita_s1050 = False
            msg_turnos = False
            for turno in esocial.turno_trabalho_ids:
                if turno.situacao_esocial in ['2']:
                    necessita_s1050 = True
                    msg_turnos = 'Pendências não enviadas ao e-Social'
            if not msg_turnos:
                msg_turnos = 'OK'
            if esocial.turno_trabalho_ids:
                txt = 'Turno de Trabalho'
                if len(esocial.turno_trabalho_ids) > 1:
                    txt = 'Turnos de Trabalho'
                msg_turnos = '{} {} - '.format(len(esocial.turno_trabalho_ids), txt) + \
                    msg_turnos
            esocial.necessita_s1050 = necessita_s1050
            esocial.msg_turnos = msg_turnos

    @api.multi
    def importar_turnos_trabalho(self):
        self.ensure_one()

        turnos = self.env['hr.turnos.trabalho'].search([
            ('cod_hor_contrat', '!=', False),
        ])
        for turno in turnos:
            if turno.situacao_esocial not in ['0', '9']:
                sped_turno = self.env['sped.hr.turnos.trabalho'].search([
                    ('company_id', '=', self.company_id.id),
                    ('hr_turnos_trabalho_id', '=', turno.id),
                ])
                if not sped_turno:
                    turno.atualizar_turno()
                    sped_turno = turno.sped_turno_id
                self.turno_trabalho_ids = [(4, sped_turno.id)]

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

    @api.multi
    def importar_remuneracoes(self):
        self.ensure_one()

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
                ('date_start', '<=', periodo.date_stop),
                ('tp_reg_prev', 'in', ['1', False]),  # Somente contratos do tipo RGPS
            ]
            contratos = self.env['hr.contract'].search(domain)
            contratos_validos = []

            # Se algum contrato tiver data de término menor que a data inicial do período, tira ele
            # adiciona o trabalhador na lista de trabalhadores_com_contrato
            for contrato in contratos:
                if not contrato.date_end or contrato.date_end >= periodo.date_stop:
                    contratos_validos.append(contrato.id)

            # Se tiver algum contrato válido, cria o registro s1200
            if contratos_validos:

                # Calcula campos de mês e ano para busca dos payslip
                mes = datetime.strptime(self.periodo_id.date_start, '%Y-%m-%d').month
                ano = datetime.strptime(self.periodo_id.date_start, '%Y-%m-%d').year

                # Trabalhadores autonomos tem holerite separado
                if trabalhador.tipo != 'autonomo':
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


                else:
                    # Busca os payslips de pagamento mensal deste autonomo
                    domain_payslip_autonomo = [
                        ('company_id', 'in', empresas),
                        ('contract_id', 'in', contratos_validos),
                        ('mes_do_ano', '=', mes),
                        ('ano', '=', ano),
                        ('state', 'in', ['verify', 'done']),
                        ('tipo_de_folha', 'in',  ['normal', 'ferias', 'decimo_terceiro']),
                    ]
                    payslips = self.env['hr.payslip.autonomo'].search(domain_payslip_autonomo)

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
                        }

                        # Criar intermediario de acordo com o tipo de employee
                        if trabalhador.tipo != 'autonomo':
                            vals.update(
                                {'payslip_ids': [(6, 0, payslips.ids)]})
                        else:
                            vals.update(
                                {'payslip_autonomo_ids': [(6, 0, payslips.ids)]})

                        s1200 = self.env['sped.esocial.remuneracao'].create(vals)

                    # Se ja existe o registro apenas criar o relacionamento
                    else:
                        s1200.contract_ids = [(6, 0, contratos.ids)]

                        if trabalhador.tipo != 'autonomo':
                            s1200.payslip_ids = [(6, 0, payslips.ids)]
                        else:
                            s1200.payslip_autonomo_ids = [(6, 0, payslips.ids)]

                    # Relaciona o s1200 com o período do e-Social
                    self.remuneracao_ids = [(4, s1200.id)]

                    # Cria o registro de transmissão sped (se ainda não existir)
                    s1200.atualizar_esocial()
            else:

                # Se não tem contrato válido, remove o registro S-1200 (se existir)
                domain = [
                    ('company_id', '=', matriz.id),
                    ('trabalhador_id', '=', trabalhador.id),
                    ('periodo_id', '=', periodo.id),
                ]
                s1200 = self.env['sped.esocial.remuneracao'].search(domain)
                if s1200:
                    s1200.sped_registro.unlink()
                    s1200.unlink()

    # Controle de registros S-1202
    remuneracao_rpps_ids = fields.Many2many(
        string='Remuneração de Servidor (RPPS)',
        comodel_name='sped.esocial.remuneracao.rpps',
    )

    @api.multi
    def importar_remuneracoes_rpps(self):
        self.ensure_one()

        # Buscar Servidores
        servidores = self.env['hr.employee'].search([])

        periodo = self.periodo_id
        matriz  = self.company_id
        empresas = self.env['res.company'].search([('matriz', '=', matriz.id)]).ids
        if matriz.id not in empresas:
            empresas.append(matriz.id)

        # separa somente os trabalhadores com contrato válido neste período e nesta empresa matriz
        # servidores_com_contrato = []
        for servidor in servidores:

            # Localiza os contratos válidos deste trabalhador
            domain = [
                ('employee_id', '=', servidor.id),
                ('company_id', 'in', empresas),
                ('date_start', '<=', periodo.date_stop),
                ('tp_reg_prev', '=', '2'),  # Somente contratos do tipo RPPS
            ]
            contratos = self.env['hr.contract'].search(domain)
            contratos_validos = []

            # Se algum contrato tiver data de término menor que a data inicial do período, tira ele
            # adiciona o trabalhador na lista de trabalhadores_com_contrato
            for contrato in contratos:
                if not contrato.date_end or contrato.date_end >= periodo.date_stop:
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

                # Se tem payslip, cria o registro S-1202
                if payslips:

                    # Verifica se o registro S-1202 já existe, cria ou atualiza
                    domain_s1202 = [
                        ('company_id', '=', matriz.id),
                        ('servidor_id', '=', servidor.id),
                        ('periodo_id', '=', periodo.id),
                    ]
                    s1202 = self.env['sped.esocial.remuneracao.rpps'].search(domain_s1202)
                    if not s1202:
                        vals = {
                            'company_id': matriz.id,
                            'servidor_id': servidor.id,
                            'periodo_id': periodo.id,
                            'contract_ids': [(6, 0, contratos.ids)],
                            'payslip_ids': [(6, 0, payslips.ids)],
                        }
                        s1202 = self.env['sped.esocial.remuneracao.rpps'].create(vals)
                    else:
                        s1202.contract_ids = [(6, 0, contratos.ids)]
                        s1202.payslip_ids = [(6, 0, payslips.ids)]

                    # Relaciona o s1202 com o período do e-Social
                    self.remuneracao_rpps_ids = [(4, s1202.id)]

                    # Cria o registro de transmissão sped (se ainda não existir)
                    s1202.atualizar_esocial()
            else:

                # Se não tem contrato válido, remove o registro S-1202 (se existir)
                domain = [
                    ('company_id', '=', matriz.id),
                    ('servidor_id', '=', servidor.id),
                    ('periodo_id', '=', periodo.id),
                ]
                s1202 = self.env['sped.esocial.remuneracao.rpps'].search(domain)
                if s1202:
                    s1202.sped_registro.unlink()
                    s1202.unlink()

    # Controle de registros S-1210
    pagamento_ids = fields.Many2many(
        string='Pagamentos a Trabalhadores',
        comodel_name='sped.esocial.pagamento',
    )

    @api.multi
    def importar_pagamentos(self):
        self.ensure_one()

        # Buscar Servidores
        beneficiarios = self.env['hr.employee'].search([])

        periodo = self.periodo_id
        matriz  = self.company_id
        empresas = self.env['res.company'].search([('matriz', '=', matriz.id)]).ids
        if matriz.id not in empresas:
            empresas.append(matriz.id)

        # separa somente os trabalhadores com contrato válido neste período e nesta empresa matriz
        # servidores_com_contrato = []
        for beneficiario in beneficiarios:

            # Localiza os contratos válidos deste beneficiário
            domain = [
                ('employee_id', '=', beneficiario.id),
                ('company_id', 'in', empresas),
                ('date_start', '<=', periodo.date_stop),
                ('tp_reg_prev', 'in', ['1', '2', False]),  # Somente contratos com o campo tp_reg_prev definido como 1 ou 2
            ]
            contratos = self.env['hr.contract'].search(domain)
            contratos_validos = []

            # Se algum contrato tiver data de término menor que a data inicial do período, tira ele
            # adiciona o beneficiario na lista de beneficiarios_com_contrato
            for contrato in contratos:
                if not contrato.date_end or contrato.date_end >= periodo.date_stop:
                    contratos_validos.append(contrato.id)

            # Se tiver algum contrato válido, cria o registro s1210
            if contratos_validos:

                # Calcula campos de mês e ano para busca dos payslip
                mes = datetime.strptime(self.periodo_id.date_start, '%Y-%m-%d').month
                ano = datetime.strptime(self.periodo_id.date_start, '%Y-%m-%d').year

                # Trabalhadores autonomos tem holerite separado
                if beneficiario.tipo != 'autonomo':

                    # Busca os payslips de pagamento mensal deste beneficiário
                    domain_payslip = [
                        ('company_id', 'in', empresas),
                        ('contract_id', 'in', contratos_validos),
                        ('mes_do_ano', '=', mes),
                        ('ano', '=', ano),
                        ('state', 'in', ['verify', 'done']),
                        ('tipo_de_folha', 'in', ['normal', 'ferias', 'decimo_terceiro', 'rescisao']),
                    ]
                    payslips = self.env['hr.payslip'].search(domain_payslip)

                else:
                    # Busca os payslips de pagamento mensal deste autonomo
                    domain_payslip_autonomo = [
                        ('company_id', 'in', empresas),
                        ('contract_id', 'in', contratos_validos),
                        ('mes_do_ano', '=', mes),
                        ('ano', '=', ano),
                        ('state', 'in', ['verify', 'done']),
                        ('tipo_de_folha', 'in',
                         ['normal', 'ferias', 'decimo_terceiro', 'rescisao']),
                    ]
                    payslips = self.env['hr.payslip.autonomo'].search(
                        domain_payslip_autonomo)

                # Se tem payslip, cria o registro S-1210
                if payslips:

                    # Verifica se o registro S-1210 já existe, cria ou atualiza
                    domain_s1210 = [
                        ('company_id', '=', matriz.id),
                        ('beneficiario_id', '=', beneficiario.id),
                        ('periodo_id', '=', periodo.id),
                    ]
                    s1210 = self.env['sped.esocial.pagamento'].search(domain_s1210)
                    if not s1210:
                        vals = {
                            'company_id': matriz.id,
                            'beneficiario_id': beneficiario.id,
                            'periodo_id': periodo.id,
                            'contract_ids': [(6, 0, contratos.ids)],
                        }

                        # Criar intermediario de acordo com o tipo de employee
                        if beneficiario.tipo != 'autonomo':
                            vals.update(
                                {'payslip_ids': [(6, 0, payslips.ids)]})
                        else:
                            vals.update(
                                {'payslip_autonomo_ids': [
                                    (6, 0, payslips.ids)]})

                        s1210 = self.env['sped.esocial.pagamento'].create(vals)

                    else:
                        s1210.contract_ids = [(6, 0, contratos.ids)]

                        if beneficiario.tipo != 'autonomo':
                            s1210.payslip_ids = [(6, 0, payslips.ids)]
                        else:
                            s1210.payslip_autonomo_ids = [(6, 0, payslips.ids)]

                    # Relaciona o s1210 com o período do e-Social
                    self.pagamento_ids = [(4, s1210.id)]

                    # Cria o registro de transmissão sped (se ainda não existir)
                    s1210.atualizar_esocial()
            else:

                # Se não tem contrato válido, remove o registro S-1210 (se existir)
                domain = [
                    ('company_id', '=', matriz.id),
                    ('beneficiario_id', '=', beneficiario.id),
                    ('periodo_id', '=', periodo.id),
                ]
                s1210 = self.env['sped.esocial.pagamento'].search(domain)
                if s1210:
                    s1210.sped_registro.unlink()
                    s1210.unlink()

    # Controle de registros S-1299
    fechamento_ids = fields.Many2many(
        string='Fechamento',
        comodel_name='sped.esocial.fechamento',
    )

    @api.multi
    def importar_fechamentos(self):
        self.ensure_one()

        # Calcula os valores do fechamento
        evt_remun = 'S' if self.remuneracao_ids or self.remuneracao_rpps_ids else 'N'
        evt_pgtos = 'S' if self.pagamento_ids else 'N'
        evt_aq_prod = 'N'
        evt_com_prod = 'N'
        evt_contrat_av_np = 'N'
        evt_infocompl_per = 'N'
        comp_sem_movto = False  # TODO Permitir que indique quando não há movimentação
        vals = {
            'company_id': self.company_id.id,
            'periodo_id': self.periodo_id.id,
            'evt_remun': evt_remun,
            'evt_pgtos': evt_pgtos,
            'evt_aq_prod': evt_aq_prod,
            'evt_com_prod': evt_com_prod,
            'evt_contrat_av_np': evt_contrat_av_np,
            'evt_infocompl_per': evt_infocompl_per,
            'comp_sem_movto': comp_sem_movto,
        }

        # Verifica se o registro S-1299 já existe, cria ou atualiza
        domain_s1299 = [
            ('company_id', '=', self.company_id.id),
            ('periodo_id', '=', self.periodo_id.id),
        ]
        s1299 = self.env['sped.esocial.fechamento'].search(domain_s1299)
        if not s1299:
            s1299 = self.env['sped.esocial.fechamento'].create(vals)
        else:
            s1299.write(vals)

        # Relaciona o s1299 com o período do e-Social
        self.fechamento_ids = [(4, s1299.id)]

        # Cria o registro de transmissão sped (se ainda não existir)
        s1299.atualizar_esocial()

    # Controle de registros S-2200
    admissao_ids = fields.Many2many(
        string='Admissões',
        comodel_name='sped.esocial.contrato',
    )
    necessita_s2200 = fields.Boolean(
        string='Necessita S2200',
        compute='compute_necessita_s2200',
    )
    msg_admissoes = fields.Char(
        string='Contratos',
        compute='compute_necessita_s2200',
    )

    # Calcula se é necessário criar algum registro S-2200
    @api.depends('admissao_ids')
    def compute_necessita_s2200(self):
        for esocial in self:
            necessita_s2200 = False
            msg_admissoes = False
            for admissao in esocial.admissao_ids:
                if admissao.situacao_esocial not in ['4']:
                    necessita_s2200 = True
                    msg_admissoes = 'Pendências não enviadas ao e-Social'
            if not msg_admissoes:
                msg_admissoes = 'OK'
            if esocial.admissao_ids:
                txt = 'Contrato Válido'
                if len(esocial.admissao_ids) > 1:
                    txt = 'Contratos Válidos'
                msg_admissoes = '{} {} - '.format(len(esocial.admissao_ids), txt) + \
                    msg_admissoes
            esocial.necessita_s2200 = necessita_s2200
            esocial.msg_admissoes = msg_admissoes

    @api.multi
    def importar_admissao(self):
        self.ensure_one()

        admissao_ids = self.env['sped.esocial.contrato'].search([
            ('company_id', '=', self.company_id.id),
        ])

        for admissao in admissao_ids:
            if admissao.id not in self.admissao_ids.ids:
                self.admissao_ids = [(4, admissao.id)]

    # Controle de registros S-2205
    alteracao_trabalhador_ids = fields.Many2many(
        string='Alterações Trabalhador',
        comodel_name='sped.esocial.alteracao.funcionario',
        relation='periodo_alt_funcionario',
    )
    necessita_s2205 = fields.Boolean(
        string='Necessita S2205',
        compute='compute_necessita_s2205',
    )
    msg_alteracao_trabalhador = fields.Char(
        string='Alterações de Trabalhador',
        compute='compute_necessita_s2205',
    )

    # Calcula se é necessário criar algum registro S-2205
    @api.depends('alteracao_trabalhador_ids')
    def compute_necessita_s2205(self):
        for esocial in self:
            necessita_s2205 = False
            msg_alteracao_trabalhador = False
            for alteracao in esocial.alteracao_trabalhador_ids:
                if alteracao.situacao_esocial not in ['4']:
                    necessita_s2205 = True
            if not msg_alteracao_trabalhador:
                msg_alteracao_trabalhador = 'Nenhuma'
            if esocial.alteracao_trabalhador_ids:
                txt = 'Alteração de Trabalhador não enviada!'
                if len(esocial.alteracao_trabalhador_ids) > 1:
                    txt = 'Alterações de Trabalhador não enviadas!'
                msg_alteracao_trabalhador = '{} {} - '.format(len(esocial.alteracao_trabalhador_ids), txt) + \
                    msg_alteracao_trabalhador
            esocial.necessita_s2205 = necessita_s2205
            esocial.msg_alteracao_trabalhador = msg_alteracao_trabalhador

    @api.multi
    def importar_alteracao_trabalhador(self):
        self.ensure_one()

        alteracao_trabalhador_ids = self.env['sped.esocial.alteracao.funcionario'].search([
            ('company_id', '=', self.company_id.id),
            ('situacao_esocial', 'in', ['1', '2', '3', '5']),
        ])

        self.alteracao_trabalhador_ids = [(6, 0, alteracao_trabalhador_ids.ids)]

    # Controle de registros S-2206
    alteracao_contrato_ids = fields.Many2many(
        string='Alterações Contrato',
        comodel_name='sped.esocial.alteracao.contrato',
        relation='periodo_alt_contrato',
    )
    necessita_s2206 = fields.Boolean(
        string='Necessita S2206',
        compute='compute_necessita_s2206',
    )
    msg_alteracao_contrato = fields.Char(
        string='Alterações de Contrato',
        compute='compute_necessita_s2206',
    )

    # Calcula se é necessário criar algum registro S-2206
    @api.depends('alteracao_contrato_ids')
    def compute_necessita_s2206(self):
        for esocial in self:
            necessita_s2206 = False
            msg_alteracao_contrato = False
            for alteracao in esocial.alteracao_trabalhador_ids:
                if alteracao.situacao_esocial not in ['4']:
                    necessita_s2206 = True
            if not msg_alteracao_contrato:
                msg_alteracao_contrato = 'Nenhuma'
            if esocial.alteracao_contrato_ids:
                txt = 'Alteração de Contrato não enviada!'
                if len(esocial.alteracao_contrato_ids) > 1:
                    txt = 'Alterações de Contrato não enviadas!'
                msg_alteracao_contrato = '{} {} - '.format(len(esocial.alteracao_contrato_ids), txt) + \
                    msg_alteracao_contrato
            esocial.necessita_s2206 = necessita_s2206
            esocial.msg_alteracao_contrato = msg_alteracao_contrato

    @api.multi
    def importar_alteracao_contrato(self):
        self.ensure_one()

        alteracao_contrato_ids = self.env['sped.esocial.alteracao.contrato'].search([
            ('company_id', '=', self.company_id.id),
            ('situacao_esocial', 'in', ['1', '2', '3', '5']),
        ])

        self.alteracao_contrato_ids = [(6, 0, alteracao_contrato_ids.ids)]

    # Outros métodos
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

    @api.multi
    def executa_analise_tabelas(self):
        for esocial in self:
            # Tabelas
            esocial.importar_empregador()               # S-1000
            esocial.importar_estabelecimentos()         # S-1005
            esocial.importar_rubricas()                 # S-1010
            esocial.importar_lotacoes()                 # S-1020
            esocial.importar_cargos()                   # S-1030
            esocial.importar_lotacoes()                 # S-1050

            # Não Periódicos
            esocial.importar_admissao()                 # S-2200
            esocial.importar_alteracao_trabalhador()    # S-2205

    @api.model
    def create(self, vals):

        # Cria o registro
        res = super(SpedEsocial, self).create(vals)

        # Executa os métodos de análise de tabelas
        res.executa_analise_tabelas()

        return res
