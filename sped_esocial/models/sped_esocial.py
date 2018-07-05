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
        comodel_name='sped.estabelecimentos',
        inverse_name='esocial_id',
    )
    lotacao_ids = fields.Many2many(
        string='Lotações Tributárias',
        comodel_name='sped.esocial.lotacao',
    )
    rubrica_ids = fields.Many2many(
        string='Rubricas',
        comodel_name='sped.esocial.rubrica',
        inverse_name='esocial_id',
    )
    # cargo_ids = fields.One2many(
    #     string='Cargos',
    #     comodel_name='sped.esocial.cargo',
    #     inverse_name='esocial_id',
    # )
    # sped_esocial_turnos_trabalho_ids = fields.One2many(
    #     string='sped_esocial_turnos_trabalho_id',
    #     comodel_name='sped.esocial.turnos.trabalho',
    #     inverse_name='esocial_id',
    # )
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
            sped_rubrica_id = rubrica.sped_esocial_rubrica_ids

            if not sped_rubrica_id:
                # Criar uma nova rubrica neste período
                vals = {
                    'rubrica_id': rubrica.id,
                    'company_id': self.company_id.id,
                }
                sped_rubrica_id = self.env['sped.esocial.rubrica'].create(vals)
            self.rubrica_ids = [(4, sped_rubrica_id.id)]

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
    def importar_turnos_trabalho(self):
        self.ensure_one()

        turnos_trabalho = self.env['esocial.turnos.trabalho'].search([])

        for turno in turnos_trabalho:
            if not turno.sped_esocial_turnos_trabalho_ids:
                # Criar um novo documento sped para o turno de trabalho
                vals = {
                    'esocial_id': self.id,
                    'sped_esocial_turnos_trabalho_id': turno.id,
                }
                sped_turno_id = self.env['sped.esocial.turnos.trabalho'].create(
                    vals
                )
                self.sped_esocial_turnos_trabalho_ids = [(4, sped_turno_id.id)]

    @api.multi
    def criar_s1005(self):
        self.ensure_one()
        for estabelecimento in self.estabelecimento_ids:
            if not estabelecimento.sped_s1005_registro:

                # Criar registro
                values = {
                    'tipo': 'esocial',
                    'registro': 'S-1005',
                    'ambiente': self.company_id.esocial_tpAmb,
                    'company_id': self.company_id.id,
                    'evento': 'evtTabEstab',
                    'origem': ('sped.esocial.estabelecimento,%s' % estabelecimento.id),
                }
                sped_s1005_registro = self.env['sped.registro'].create(values)
                estabelecimento.sped_s1005_registro = sped_s1005_registro

    @api.multi
    def criar_s1010(self):
        self.ensure_one()
        for rubrica in self.rubrica_ids:
            rubrica.gerar_registro()

    @api.multi
    def criar_s1020(self):
        self.ensure_one()
        for lotacao in self.lotacao_ids:
            if not lotacao.sped_s1020_registro:

                # Criar registro
                values = {
                    'tipo': 'esocial',
                    'registro': 'S-1020',
                    'ambiente': self.company_id.esocial_tpAmb,
                    'company_id': self.company_id.id,
                    'evento': 'evtTabLotacao',
                    'origem': ('sped.esocial.lotacao,%s' % lotacao.id),
                }
                sped_s1020_registro = self.env['sped.registro'].create(values)
                lotacao.sped_s1020_registro = sped_s1020_registro

    @api.multi
    def criar_s1030(self):
        self.ensure_one()
        for cargo in self.cargo_ids:
            if not cargo.sped_s1030_registro:

                # Criar registro
                values = {
                    'tipo': 'esocial',
                    'registro': 'S-1030',
                    'ambiente': self.company_id.esocial_tpAmb,
                    'company_id': self.company_id.id,
                    'evento': 'evtTabCargo',
                    'origem': ('sped.esocial.cargo,%s' % cargo.id),
                }
                sped_s1030_registro = self.env['sped.registro'].create(values)
                cargo.sped_s1030_registro = sped_s1030_registro

    @api.multi
    def criar_s1050(self):
        self.ensure_one()
        for turno in self.sped_esocial_turnos_trabalho_ids:
            if not turno.sped_s1050_registro:
                # Criar registro
                values = {
                    'tipo': 'esocial',
                    'registro': 'S-1050',
                    'ambiente': self.company_id.esocial_tpAmb,
                    'company_id': self.company_id.id,
                    'evento': 'evtTabHorTur',
                    'origem': ('sped.esocial.turnos.trabalho,%s' % turno.id),
                }
                sped_s1050_registro = self.env['sped.registro'].create(
                    values)
                turno.sped_s1050_registro = sped_s1050_registro

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
