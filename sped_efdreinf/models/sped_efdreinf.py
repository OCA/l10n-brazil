# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class SpedEfdReinf(models.Model):
    _name = 'sped.efdreinf'
    _description = 'Eventos Periódicos EFD/Reinf'
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
            ('2', 'Fechado'),
        ],
        default='1',
    )

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

    # Registro R-2099
    sped_R2099 = fields.Boolean(
        string='Fechamento EFD/Reinf',
        compute='_compute_r2099',
    )
    sped_R2099_registro = fields.Many2one(
        string='Registro R-2099',
        comodel_name='sped.transmissao',
    )
    situacao_R2099 = fields.Selection(
        string='Situação R-2099',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
        ],
        related='sped_R2099_registro.situacao',
        readonly=True,
    )

    @api.depends('periodo_id', 'company_id', 'estabelecimento_ids', 'sped_R2099_registro')
    def _compute_r2099(self):
        for efdreinf in self:
            efdreinf.sped_R2099 = True if efdreinf.sped_R2099_registro else False
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

        # Limpar dados anteriores
        for estabelecimento in self.estabelecimento_ids:
            estabelecimento.unlink()

        # Pegar a lista de empresas
        # domain = [
        #     ('cnpj_cpf', '=ilike', cnpj_base),
        # ]
        empresas = self.env['res.company'].search([])

        # Roda 1 empresa por vez (cada empresa é um Estabelecimento no EFD/Reinf)
        for empresa in empresas:

            if empresa.cnpj_cpf[0:10] != cnpj_base:
                continue

            # Identificar NFs de entrada do período com retenção de INSS nesta empresa
            domain = [
                ('state', 'in', ['open', 'paid']),
                ('type', '=', 'in_invoice'),
                ('date_hour_invoice', '>=', data_hora_inicial),
                ('date_hour_invoice', '<=', data_hora_final),
                # ('inss_value_wh', '>', 0),  # Só pegar as NFs com retenção de INSS
                # ('company_id', '=', empresa.id),  # Só pegar as NFs desta empresa
            ]
            nfs_busca = self.env['account.invoice'].search(domain, order='partner_id')
            prestador_id = False
            estabelecimento_id = empresa
            ind_cprb = False
            for nf in nfs_busca:

                if nf.company_id != empresa or nf.inss_value_wh == 0:
                    continue

                if prestador_id != nf.partner_id and nf.company_id == empresa:

                    # Define o próximo prestador_id
                    prestador_id = nf.partner_id
                    ind_cprb = False  # TODO Colocar no parceiro o campo de indicador de CPRB

                    vals = {
                        'efdreinf_id': self.id,
                        'estabelecimento_id': empresa.id,
                        'prestador_id': prestador_id.id,
                        'ind_cprb': ind_cprb,
                    }
                    estabelecimento_id = self.env['sped.efdreinf.estabelecimento'].create(vals)
                    self.estabelecimento_ids = [(4, estabelecimento_id.id)]

                # Soma os totalizadores desta NF
                estabelecimento_id.vr_total_bruto += nf.amount_total
                estabelecimento_id.vr_total_base_retencao += nf.inss_base_wh
                estabelecimento_id.vr_total_ret_princ += nf.inss_value_wh
                estabelecimento_id.vr_total_ret_adic += 0  # TODO Criar o campo vr_total_rec_adic na NF
                estabelecimento_id.vr_total_nret_princ += 0  # TODO Criar o campo vr_total_nret_princ na NF
                estabelecimento_id.vr_total_nret_adic += 0  # TODO Criar o campo vr_total_nret_adic na NF

                # Criar o registro da NF
                vals = {
                    'estabelecimento_id': estabelecimento_id.id,
                    'nfs_id': nf.id,
                }
                nfs_estabelecimento = self.env['sped.efdreinf.nfs'].create(vals)
                estabelecimento_id.nfs_ids = [(4, nfs_estabelecimento.id)]

                # Criar os registros dos itens das NFs
                for item in nf.invoice_line:
                    vals = {
                        'efdreinf_nfs_id': nfs_estabelecimento.id,
                        'servico_nfs_id': item.id,
                        'tp_servico_id': item.product_id.tp_servico_id.id or False,
                        'vr_base_ret': item.inss_base,
                        'vr_retencao': item.inss_wh_value,
                        'vr_ret_sub': 0,  # TODO Criar esse campo no item da NF
                        'vr_nret_princ': 0,  # TODO Criar esse campo no item da NF
                        'vr_servicos_15': 0,  # TODO Criar esse campo no item da NF
                        'vr_servicos_20': 0,  # TODO Criar esse campo no item da NF
                        'vr_servicos_25': 0,  # TODO Criar esse campo no item da NF
                        'vr_adicional': 0,  # TODO Criar esse campo no item da NF
                        'vr_nret_adic': 0,  # TODO Criar esse campo no item da NF
                    }
                    servico = self.env['sped.efdreinf.servico'].create(vals)
                    nfs_estabelecimento.servico_ids = [(4, servico.id)]

    @api.multi
    def criar_R2010(self):
        self.ensure_one()

        for estabelecimento in self.estabelecimento_ids:
            if not estabelecimento.sped_R2010_registro:

                values = {
                    'tipo': 'efdreinf',
                    'registro': 'R-2010',
                    'company_id': self.company_id.id,
                    'evento': 'evtServTom',
                    'origem': ('sped.efdreinf.estabelecimento,%s' % estabelecimento.id),
                }

                sped_R2010_registro = self.env['sped.transmissao'].create(values)
                estabelecimento.sped_R2010_registro = sped_R2010_registro

    @api.multi
    def criar_R2099(self):
        self.ensure_one()

        for efdreinf in self:

            values = {
                'tipo': 'efdreinf',
                'registro': 'R-2099',
                'company_id': self.company_id.id,
                'evento': 'evtFechamento',
                'origem': ('sped.efdreinf,%s' % efdreinf.id),
            }

            sped_R2099_registro = self.env['sped.transmissao'].create(values)
            efdreinf.sped_R2099_registro = sped_R2099_registro
