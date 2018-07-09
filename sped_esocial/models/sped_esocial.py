# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError


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

        # rubricas = self.env['hr.salary.rule'].search([
        #     ('nat_rubr', '!=', False),
        # ])
        #
        # for rubrica in rubricas:
        #     sped_rubrica_id = rubrica.sped_esocial_rubrica_ids
        #
        #     if not sped_rubrica_id:
        #         # Criar uma nova rubrica neste período
        #         vals = {
        #             'rubrica_id': rubrica.id,
        #             'company_id': self.company_id.id,
        #         }
        #         sped_rubrica_id = self.env['sped.esocial.rubrica'].create(vals)
        #     self.rubrica_ids = [(4, sped_rubrica_id.id)]

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

        # cargos = self.env['hr.job'].search([])
        #
        # for cargo in cargos:
        #
        #     # Criar um novo cargo neste período
        #     vals = {
        #         'company_id': self.company_id.id,
        #         'cargo_id': cargo.id,
        #     }
        #     cargo_id = self.env['sped.esocial.cargo'].create(vals)
        #     self.cargo_ids = [(4, cargo_id.id)]

    # Criar registros S-1030
    @api.multi
    def criar_s1030(self):
        self.ensure_one()
        for cargo in self.cargo_ids:
            cargo.gerar_registro()

    # Controle de registros S-1050
    turno_trabalho_ids = fields.Many2many(
        string='sped_esocial_turnos_trabalho_id',
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
            for turno in esocial.cargo_ids:
                if turno.situacao_esocial in ['2']:
                    necessita_s1050 = True
            esocial.necessita_s1050 = necessita_s1050

    @api.multi
    def importar_turnos_trabalho(self):
        self.ensure_one()

        turnos_trabalho = self.env['esocial.turnos.trabalho'].search([])

        for turno in turnos_trabalho:
            if not turno.turno_trabalho_ids:
                # Criar um novo documento sped para o turno de trabalho
                vals = {
                    'company_id': self.company_id.id,
                    'sped_esocial_turnos_trabalho_id': turno.id,
                }
                sped_turno_id = self.env['sped.hr.turnos.trabalho'].create(
                    vals
                )
                self.turno_trabalho_ids = [(4, sped_turno_id.id)]

    # Criar registros S-1050
    @api.multi
    def criar_s1050(self):
        self.ensure_one()
        for turno in self.turno_trabalho_ids:
            turno.gerar_registro()

    # @api.multi
    # def unlink(self):
    #     for esocial in self:
    #         if esocial.situacao not in ['1']:
    #             raise ValidationError("Não pode excluir um Período e-Social que já tem algum processamento!")
    #
    #         # Checa se algum registro já foi transmitido
    #         for estabelecimento in esocial.estabelecimento_ids:
    #             if estabelecimento.requer_s1005 and estabelecimento.situacao_s1005 in ['2', '4']:
    #                 raise ValidationError("Não pode excluir um Período e-Social que já tem algum processamento!")

    # @api.depends('estabelecimento_ids')
    # def _compute_situacao(self):
    #     for esocial in self:
    #
    #         situacao = '1'
    #
    #         # Verifica se está fechado ou aberto
    #         # situacao = '3' if efdreinf.situacao_R2099 == '4' else '1'
    #
    #         # # Checa se tem algum problema que precise ser retificado
    #         # for estabelecimento in esocial.estabelecimento_ids:
    #         #     if estabelecimento.requer_
    #         #     if estabelecimento.situacao_R2010 == '5':
    #         #         situacao = '2'  # Precisa Retificar
    #
    #         # Atualiza o campo situacao
    #         esocial.situacao = situacao

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

