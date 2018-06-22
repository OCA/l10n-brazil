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
    estabelecimento_ids = fields.One2many(
        string='Estabelecimentos',
        comodel_name='sped.esocial.estabelecimento',
        inverse_name='esocial_id',
    )
    lotacao_ids = fields.One2many(
        string='Lotações Tributárias',
        comodel_name='sped.esocial.lotacao',
        inverse_name='esocial_id',
    )
    rubrica_ids = fields.One2many(
        string='Rubricas',
        comodel_name='sped.esocial.rubrica',
        inverse_name='esocial_id',
    )
    cargo_ids = fields.One2many(
        string='Cargos',
        comodel_name='sped.esocial.cargo',
        inverse_name='esocial_id',
    )
    situacao = fields.Selection(
        string='Situação',
        selection=[
            ('1', 'Aberto'),
            ('2', 'Precisa Retificar'),
            ('3', 'Fechado')
        ],
        compute='_compute_situacao',
        store=True,
    )

    # @api.multi
    # def unlink(self):
    #     for esocial in self:
    #         if esocial.situacao not in ['1']:
    #             raise ValidationError("Não pode excluir um Período e-Social que já tem algum processamento!")
    #
    #         # Checa se algum registro já foi transmitido
    #         for estabelecimento in esocial.estabelecimento_ids:
    #             if estabelecimento.requer_S1005 and estabelecimento.situacao_S1005 in ['2', '4']:
    #                 raise ValidationError("Não pode excluir um Período e-Social que já tem algum processamento!")

    @api.depends('estabelecimento_ids')
    def _compute_situacao(self):
        for esocial in self:

            situacao = '1'

            # Verifica se está fechado ou aberto
            # situacao = '3' if efdreinf.situacao_R2099 == '4' else '1'

            # # Checa se tem algum problema que precise ser retificado
            # for estabelecimento in esocial.estabelecimento_ids:
            #     if estabelecimento.requer_
            #     if estabelecimento.situacao_R2010 == '5':
            #         situacao = '2'  # Precisa Retificar

            # Atualiza o campo situacao
            esocial.situacao = situacao

    @api.depends('periodo_id', 'company_id', 'nome')
    def _compute_readonly(self):
        for esocial in self:
            esocial.nome_readonly = esocial.nome
            esocial.periodo_id_readonly = esocial.periodo_id
            esocial.company_id_readonly = esocial.company_id

    @api.depends('periodo_id', 'company_id')
    def _compute_nome(self):
        for efdreinf in self:
            nome = efdreinf.periodo_id.name
            if efdreinf.company_id:
                nome += '-' + efdreinf.company_id.name
            efdreinf.nome = nome

    @api.multi
    def importar_estabelecimentos(self):
        self.ensure_one()

        # estabelecimentos = [self.company_id]
        estabelecimentos = self.env['res.company'].search([
            '|',
            ('id', '=', self.company_id.id),
            ('matriz', '=', self.company_id.id),
        ])
        # estabelecimentos.append(empresas)

        for estabelecimento in estabelecimentos:
            incluir = True
            for empresa in self.estabelecimento_ids:
                if empresa.estabelecimento_id == estabelecimento:
                    incluir = False

            if incluir:
                # Criar um novo estabelecimento neste período
                vals = {
                    'esocial_id': self.id,
                    'estabelecimento_id': estabelecimento.id,
                }
                estabelecimento_id = self.env['sped.esocial.estabelecimento'].create(vals)
                self.estabelecimento_ids = [(4, estabelecimento_id.id)]

    @api.multi
    def importar_rubricas(self):
        self.ensure_one()

        rubricas = self.env['hr.salary.rule'].search([
            ('nat_rubr', '!=', False),
        ])

        for rubrica in rubricas:

            # Criar uma nova rubrica neste período
            vals = {
                'esocial_id': self.id,
                'rubrica_id': rubrica.id,
            }
            rubrica_id = self.env['sped.esocial.rubrica'].create(vals)
            self.rubrica_ids = [(4, rubrica_id.id)]

    @api.multi
    def importar_lotacoes(self):
        self.ensure_one()

        lotacoes = self.env['res.company'].search([
            '|',
            ('id', '=', self.company_id.id),
            ('matriz', '=', self.company_id.id),
        ])

        for lotacao in lotacoes:
            incluir = True
            for empresa in self.lotacao_ids:
                if empresa.lotacao_id == lotacao:
                    incluir = False

            if incluir:
                # Criar uma nova lotacao neste período
                vals = {
                    'esocial_id': self.id,
                    'lotacao_id': lotacao.id,
                }
                lotacao_id = self.env['sped.esocial.lotacao'].create(vals)
                self.lotacao_ids = [(4, lotacao_id.id)]

    @api.multi
    def importar_cargos(self):
        self.ensure_one()

        cargos = self.env['hr.job'].search([])

        for cargo in cargos:

            # Criar um novo cargo neste período
            vals = {
                'esocial_id': self.id,
                'cargo_id': cargo.id,
            }
            cargo_id = self.env['sped.esocial.cargo'].create(vals)
            self.cargo_ids = [(4, cargo_id.id)]

    @api.multi
    def criar_S1005(self):
        self.ensure_one()
        for estabelecimento in self.estabelecimento_ids:
            if not estabelecimento.sped_S1005_registro:

                # Criar registro
                values = {
                    'tipo': 'esocial',
                    'registro': 'S-1005',
                    'ambiente': self.company_id.esocial_tpAmb,
                    'company_id': self.company_id.id,
                    'evento': 'evtTabEstab',
                    'origem': ('sped.esocial.estabelecimento,%s' % estabelecimento.id),
                }
                sped_S1005_registro = self.env['sped.transmissao'].create(values)
                estabelecimento.sped_S1005_registro = sped_S1005_registro

    @api.multi
    def criar_S1010(self):
        self.ensure_one()
        for rubrica in self.rubrica_ids:
            if not rubrica.sped_S1010_registro:

                # Criar registro
                values = {
                    'tipo': 'esocial',
                    'registro': 'S-1010',
                    'ambiente': self.company_id.esocial_tpAmb,
                    'company_id': self.company_id.id,
                    'evento': 'evtTabRubrica',
                    'origem': ('sped.esocial.rubrica,%s' % rubrica.id),
                }
                sped_S1010_registro = self.env['sped.transmissao'].create(values)
                rubrica.sped_S1010_registro = sped_S1010_registro

    @api.multi
    def criar_S1020(self):
        self.ensure_one()
        for lotacao in self.lotacao_ids:
            if not lotacao.sped_S1020_registro:

                # Criar registro
                values = {
                    'tipo': 'esocial',
                    'registro': 'S-1020',
                    'ambiente': self.company_id.esocial_tpAmb,
                    'company_id': self.company_id.id,
                    'evento': 'evtTabLotacao',
                    'origem': ('sped.esocial.lotacao,%s' % lotacao.id),
                }
                sped_S1020_registro = self.env['sped.transmissao'].create(values)
                lotacao.sped_S1020_registro = sped_S1020_registro

    @api.multi
    def criar_S1030(self):
        self.ensure_one()
        for cargo in self.cargo_ids:
            if not cargo.sped_S1030_registro:

                # Criar registro
                values = {
                    'tipo': 'esocial',
                    'registro': 'S-1030',
                    'ambiente': self.company_id.esocial_tpAmb,
                    'company_id': self.company_id.id,
                    'evento': 'evtTabCargo',
                    'origem': ('sped.esocial.cargo,%s' % cargo.id),
                }
                sped_S1030_registro = self.env['sped.transmissao'].create(values)
                cargo.sped_S1030_registro = sped_S1030_registro
