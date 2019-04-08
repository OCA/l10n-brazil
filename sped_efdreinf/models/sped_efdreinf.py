# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError


class SpedEfdReinf(models.Model):
    _name = 'sped.efdreinf'
    _description = u'Eventos Periódicos EFD/Reinf'
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
        string='Prestador(es) de Serviço',
        comodel_name='sped.efdreinf.estabelecimento',
        inverse_name='efdreinf_id',
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
    tem_registros = fields.Boolean(
        string='Tem Registros?',
        compute='compute_tem_registros',
        store=True,
    )
    registro_ids = fields.Many2many(
        string='Registros para Transmitir',
        comodel_name='sped.registro',
        relation='sped_efdreinf_sped_registro_todos_rel',
        column1='sped_efdreinf_id',
        column2='sped_registro_id',
    )
    tem_erros = fields.Boolean(
        string='Tem Erros?',
        compute='compute_erro_ids',
        store=True,
    )
    erro_ids = fields.Many2many(
        string='Registros com Erros',
        comodel_name='sped.registro',
        relation='sped_efdreinf_sped_registro_erros_rel',
        column1='sped_efdreinf_id',
        column2='sped_registro_id',
        compute='compute_erro_ids',
        store=True,
    )
    pode_fechar = fields.Boolean(
        string='Pode Fechar?',
        compute='compute_erro_ids',
    )
    pode_transmitir = fields.Boolean(
        string='Pode Transmitir?',
        compute='compute_erro_ids',
    )
    registros = fields.Integer(
        string='Registros neste Período',
        compute='compute_erro_ids',
    )
    transmitidos = fields.Integer(
        string='Sucesso',
        compute='compute_erro_ids',
    )
    em_transmissao = fields.Integer(
        string='Em Transmissão',
        compute='compute_erro_ids',
    )
    erros = fields.Integer(
        string='Erros',
        compute='compute_erro_ids',
    )

    @api.depends('registro_ids.situacao')
    def compute_erro_ids(self):
        for periodo in self:
            registros = []
            transmitidos = 0
            em_transmissao = 0
            pode_fechar = False
            pode_transmitir = False
            for registro in periodo.registro_ids:
                if registro.situacao == '3':
                    registros.append(registro.id)
                elif registro.situacao == '4':
                    transmitidos += 1
                elif registro.situacao in ['1', '2']:
                    for lote in registro.lote_ids:
                        if lote.situacao in ['1', '2']:
                            em_transmissao += 1
            periodo.erro_ids = [(6, 0, registros)]
            periodo.tem_erros = True if registros else False
            periodo.registros = len(periodo.registro_ids)
            periodo.transmitidos = transmitidos
            periodo.em_transmissao = em_transmissao
            periodo.erros = len(periodo.erro_ids)
            if periodo.registros == (periodo.transmitidos + periodo.em_transmissao):
                if not periodo.sped_r2099_registro and periodo.registros == periodo.transmitidos:
                    pode_fechar = True
            else:
                pode_transmitir = True
            periodo.pode_fechar = pode_fechar
            periodo.pode_transmitir = pode_transmitir

    @api.depends('registro_ids')
    def compute_tem_registros(self):
        for periodo in self:
            periodo.tem_registros = True if periodo.registro_ids else False

    @api.multi
    def compute_registro_ids(self):
        for efdreinf in self:

            # Identifica a lista de registros relacionados com este período
            # Ela deve incluir todos os registros de tabelas com pendência neste momento,
            # todos os registros não-periódicos pendentes transmissão
            # e o registros periódicos relacionados
            registros = []

            # Estabelecimentos (R-2010)
            for estabelecimento in efdreinf.estabelecimento_ids:
                # Identifica o registro a ser transmitido
                if estabelecimento.sped_r2010_registro.situacao in ['1', '3']:
                    registros.append(estabelecimento.sped_r2010_registro.id)
                else:
                    for registro in estabelecimento.sped_r2010_retificacao:
                        if registro.situacao in ['1', '3']:
                            registros.append(registro.id)

            # Reabertura (R-2098)
            if efdreinf.sped_r2098_registro.situacao in ['1', '3']:
                registros.append(
                    efdreinf.sped_r2098_registro.sped_inclusao.id)

            # Fechamento (R-2099)
            if efdreinf.sped_r2099_registro.situacao in ['1', '3']:
                registros.append(efdreinf.sped_r2099_registro.sped_inclusao.id)

            # Popula a lista de registros
            regs = efdreinf.registro_ids.ids
            for registro in registros:
                if registro not in regs:
                    regs.append(registro)
            efdreinf.registro_ids = [(6, 0, regs)]
            efdreinf.tem_registros = True if efdreinf.registro_ids else False

    # R-2099 - Fechamento
    evt_serv_tm = fields.Boolean(
        string='Tomou Serviços com Retenção de Contr.Prev.?',
        compute='_compute_r2099',
        store=True,
    )
    evt_serv_pr = fields.Boolean(
        string='Proveu Serviços com Retenção de Contr.Prev.?',
        compute='_compute_r2099',
        store=True,
    )
    evt_ass_desp_rec = fields.Boolean(
        string='Recebeu recursos como Assoc.Desportiva?',
        compute='_compute_r2099',
        store=True,
    )
    evt_ass_desp_rep = fields.Boolean(
        string='Repassou recursos para Assoc.Desportiva?',
        compute='_compute_r2099',
        store=True,
    )
    evt_com_prod = fields.Boolean(
        string='Produtor Rural comercializou Produção?',
        compute='_compute_r2099',
        store=True,
    )
    evt_cprb = fields.Boolean(
        string='Apurou Contr.Prev. sobre Receita Bruta?',
        compute='_compute_r2099',
        store=True,
    )
    evt_pgtos = fields.Boolean(
        string='Efetuou pagamentos diversos ?',
        compute='_compute_r2099',
        store=True,
    )
    comp_sem_movto_id = fields.Many2one(
        string='Primeira Competência à partir do qual não houve movimento',
        comodel_name='account.period',
    )
    pode_sem_movto = fields.Boolean(
        string='Pode sem Movimento?',
        compute='_compute_r2099',
        store=True,
    )
    pode_fechar = fields.Boolean(
        string='Pode Fechar?',
        compute='_compute_r2099',
    )

    # Registro R-2098
    sped_r2098_registro = fields.Many2one(
        string='Registro R-2098',
        comodel_name='sped.efdreinf.reabertura.eventos.periodicos',
    )
    situacao_r2098 = fields.Selection(
        string='Situação R-2098',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        related='sped_r2098_registro.situacao',
        readonly=True,
    )

    # Registro R-2099
    sped_r2099 = fields.Boolean(
        string='Fechamento EFD/Reinf',
        compute='_compute_r2099',
    )
    sped_r2099_registro = fields.Many2one(
        string='Registro R-2099',
        comodel_name='sped.efdreinf.fechamento.eventos.periodicos',
    )
    situacao_r2099 = fields.Selection(
        string='Situação R-2099',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        related='sped_r2099_registro.situacao',
        readonly=True,
    )

    @api.multi
    def unlink(self):
        for efdreinf in self:
            if efdreinf.situacao not in ['1']:
                raise ValidationError("Não pode excluir um Período EFD/Reinf que já tem algum processamento!")

            # Checa se algum registro já foi transmitido
            for estabelecimento in efdreinf.estabelecimento_ids:
                if estabelecimento.situacao_r2010 not in ['1', '3']:
                    raise ValidationError("Não pode excluir um Período EFD/Reinf que já tem algum processamento!")

    @api.depends('estabelecimento_ids')
    def _compute_situacao(self):
        for efdreinf in self:
            # Verifica se está fechado ou aberto
            situacao = '3' if efdreinf.situacao_r2099 == '4' else '1'

            # Checa se tem algum problema que precise ser retificado
            for estabelecimento in efdreinf.estabelecimento_ids:
                if estabelecimento.situacao_r2010 == '5':
                    situacao = '2'  # Precisa Retificar

            # Atualiza o campo situacao
            efdreinf.situacao = situacao

    @api.depends('periodo_id', 'company_id', 'estabelecimento_ids')
    def _compute_r2099(self):
        for efdreinf in self:
            efdreinf.sped_r2099 = True if efdreinf.sped_r2099_registro else False
            efdreinf.evt_serv_tm = True if efdreinf.estabelecimento_ids else False
            efdreinf.evt_serv_pr = False  # TODO
            efdreinf.evt_ass_desp_rec = False  # TODO
            efdreinf.evt_ass_desp_rep = False  # TODO
            efdreinf.evt_com_prod = False  # TODO
            efdreinf.evt_cprb = False  # TODO
            efdreinf.evt_pgtos = False  # TODO

            if (efdreinf.evt_serv_tm or
                efdreinf.evt_serv_pr or
                efdreinf.evt_ass_desp_rec or
                efdreinf.evt_ass_desp_rep or
                efdreinf.evt_com_prod or
                efdreinf.evt_cprb or
                efdreinf.evt_pgtos):
                efdreinf.pode_sem_movto = False
            else:
                efdreinf.pode_sem_movto = True

            # Roda todos os registros calculados para ver se todos já foram transmitidos
            pode_fechar = True
            contador = 0
            for estabelecimento in efdreinf.estabelecimento_ids:
                contador += 1
                if estabelecimento.situacao_r2010 != '4':
                    pode_fechar = False

            # Se não tem movimento precisa definir um período inicial sem movimento antes
            if contador == 0 and not efdreinf.comp_sem_movto_id:
                pode_fechar = False

            # Popula se pode fechar o movimento deste período
            efdreinf.pode_fechar = pode_fechar

    @api.depends('periodo_id', 'company_id', 'nome')
    def _compute_readonly(self):
        for efdreinf in self:
            efdreinf.nome_readonly = efdreinf.nome
            efdreinf.periodo_id_readonly = efdreinf.periodo_id
            efdreinf.company_id_readonly = efdreinf.company_id

    @api.depends('periodo_id', 'company_id')
    def _compute_nome(self):
        for efdreinf in self:
            nome = efdreinf.periodo_id.name
            if efdreinf.company_id:
                nome += '-' + efdreinf.company_id.name
            efdreinf.nome = nome

    @api.multi
    def importar_movimento(self):
        self.ensure_one()

        data_hora_inicial = self.periodo_id.date_start + ' 00:00:00'
        data_hora_final = self.periodo_id.date_stop + ' 23:59:59'
        cnpj_base = self.company_id.cnpj_cpf[0:10]

        # Limpar dados anteriores que não tenham registro SPED
        for estabelecimento in self.estabelecimento_ids:
            if not estabelecimento.sped_r2010_registro:
                estabelecimento.unlink()

        empresas = self.env['res.company'].search([])

        # Roda 1 empresa por vez (cada empresa é um Estabelecimento no EFD/Reinf)
        for empresa in empresas:

            if empresa.cnpj_cpf[0:10] != cnpj_base:
                continue

            nfs_busca = self.get_fornecedores_notas_entrada(
                data_hora_final, data_hora_inicial)
            for nf in nfs_busca:

                if nf.company_id != empresa or nf.inss_value_wh == 0:
                    continue

                if nf.company_id == empresa:

                    # Define o próximo prestador_id
                    prestador_id = nf.partner_id
                    ind_cprb = False  # TODO Colocar no parceiro o campo de indicador de CPRB

                    # Acha o registro do prestador
                    domain = [
                        ('efdreinf_id', '=', self.id),
                        ('estabelecimento_id', '=', empresa.id),
                        ('prestador_id', '=', prestador_id.id),
                        ('periodo_id', '=', self.periodo_id.id)
                    ]
                    estabelecimento_id = self.env['sped.efdreinf.estabelecimento'].search(domain)

                    # Cria o registro se ele não existir
                    if not estabelecimento_id:
                        vals = {
                            'efdreinf_id': self.id,
                            'estabelecimento_id': empresa.id,
                            'prestador_id': prestador_id.id,
                            'periodo_id': self.periodo_id.id,
                            'ind_cprb': ind_cprb,
                        }
                        estabelecimento_id = self.env['sped.efdreinf.estabelecimento'].create(vals)
                        self.estabelecimento_ids = [(4, estabelecimento_id.id)]

    def get_fornecedores_notas_entrada(self, data_hora_final,
                                       data_hora_inicial):
        # Identificar NFs de entrada do período com retenção de INSS nesta empresa
        domain = [
            ('state', 'in', ['open', 'paid']),
            ('type', '=', 'in_invoice'),
            ('date_hour_invoice', '>=', data_hora_inicial),
            ('date_hour_invoice', '<=', data_hora_final),
        ]
        nfs_busca = self.env['account.invoice'].search(domain,
                                                       order='partner_id')
        return nfs_busca

    @api.multi
    def criar_r2010(self):
        self.ensure_one()

        for estabelecimento in self.estabelecimento_ids:
            if not estabelecimento.sped_r2010_registro:

                values = {
                    'tipo': 'efdreinf',
                    'registro': 'R-2010',
                    'ambiente': self.company_id.tpAmb,
                    'company_id': self.company_id.id,
                    'evento': 'evtServTom',
                    'origem': (
                            'sped.efdreinf.estabelecimento,%s' %
                            estabelecimento.id
                    ),
                    'origem_intermediario': (
                            'sped.efdreinf.estabelecimento,%s' %
                            estabelecimento.id
                    ),
                }

                sped_r2010_registro = self.env['sped.registro'].create(values)
                estabelecimento.sped_r2010_registro = sped_r2010_registro

    @api.multi
    def criar_r2099(self):
        self.ensure_one()

        for efdreinf in self:
            # Se o registro intermediário do R-2099 não existe, criá-lo
            if not self.sped_r2099_registro:
                self.sped_r2099_registro = \
                    self.env['sped.efdreinf.fechamento.eventos.periodicos'].create({
                        'company_id': self.company_id.id,
                        'periodo_id': self.periodo_id.id,
                        'reinf_competencia_id': self.id,
                    })

            # Processa cada tipo de operação do R-2099
            # O que realmente precisará ser feito é tratado no método do registro intermediário
            self.sped_r2099_registro.criar_registro()

    @api.multi
    def criar_r2098(self):
        self.ensure_one()

        for efdreinf in self:
            # Se o registro intermediário do R-2098 não existe, criá-lo
            if not self.sped_r2098_registro:
                self.sped_r2098_registro = \
                    self.env[
                        'sped.efdreinf.reabertura.eventos.periodicos'].create({
                        'company_id': self.company_id.id,
                        'periodo_id': self.periodo_id.id,
                        'reinf_competencia_id': self.id,
                    })
            else:
                self.sped_r2098_registro.sped_inclusao = False
            # Processa cada tipo de operação do R-2098
            # O que realmente precisará ser feito é tratado no método do registro intermediário
            self.sped_r2098_registro.criar_registro()

    @api.multi
    def executa_analise(self):
        for efdreinf in self:

            # Periódicos
            efdreinf.importar_movimento()
            efdreinf.estabelecimento_ids.calcular_valores_impostos()
            efdreinf.criar_r2010()

            # Calcula os registros para transmitir
            efdreinf.compute_registro_ids()

    @api.model
    def create(self, vals):

        # Cria o registro
        res = super(SpedEfdReinf, self).create(vals)

        # Executa os métodos de análise de tabelas
        res.executa_analise()

        return res

    @api.multi
    def transmitir_periodo(self):
        self.ensure_one()

        # Cria os lotes de transmissão
        wizard = self.env['sped.criacao.wizard'].create({})
        lotes = wizard.popular(self.registro_ids)
        wizard.lote_ids = [(6, 0, lotes)]
        wizard.criar_lotes()
        self.env['sped.lote'].transmitir_lotes_preparados()

    @api.multi
    def importar_fechamentos(self):
        self.ensure_one()

        # Verifica se o registro R-2099 já existe, cria ou atualiza
        if not self.sped_r2099_registro:
            self.criar_r2099()

        if self.sped_r2098_registro.sped_inclusao:
            self.sped_r2098_registro.sped_inclusao = False

        # Recalcula os registros
        self.compute_registro_ids()

    @api.multi
    def importar_reabertura(self):
        self.ensure_one()

        # Verifica se o registro R-2099 já existe, cria ou atualiza
        if not self.sped_r2098_registro:
            self.criar_r2098()

        self.sped_r2098_registro.sped_inclusao = False
        self.sped_r2098_registro.criar_registro()
        self.sped_r2099_registro.sped_inclusao = False
        self._compute_situacao()

        # Recalcula os registros
        self.compute_registro_ids()
