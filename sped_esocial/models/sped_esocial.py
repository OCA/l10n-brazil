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

    # @api.multi
    # def importar_movimento(self):
    #     self.ensure_one()
    #
    #     data_hora_inicial = self.periodo_id.date_start + ' 00:00:00'
    #     data_hora_final = self.periodo_id.date_stop + ' 23:59:59'
    #     cnpj_base = self.company_id.cnpj_cpf[0:10]
    #
    #     # Limpar dados anteriores que não tenham registro SPED
    #     for estabelecimento in self.estabelecimento_ids:
    #         if not estabelecimento.sped_R2010_registro:
    #             estabelecimento.unlink()
    #
    #     # Pegar a lista de empresas
    #     # domain = [
    #     #     ('cnpj_cpf', '=ilike', cnpj_base),
    #     # ]
    #     empresas = self.env['res.company'].search([])
    #
    #     # Roda 1 empresa por vez (cada empresa é um Estabelecimento no EFD/Reinf)
    #     for empresa in empresas:
    #
    #         if empresa.cnpj_cpf[0:10] != cnpj_base:
    #             continue
    #
    #         # Identificar NFs de entrada do período com retenção de INSS nesta empresa
    #         domain = [
    #             ('state', 'in', ['open', 'paid']),
    #             ('type', '=', 'in_invoice'),
    #             ('date_hour_invoice', '>=', data_hora_inicial),
    #             ('date_hour_invoice', '<=', data_hora_final),
    #         ]
    #         nfs_busca = self.env['account.invoice'].search(domain, order='partner_id')
    #         prestador_id = False
    #         estabelecimento_id = False
    #         ind_cprb = False
    #
    #         # Inicia acumuladores do Estabelecimento
    #         vr_total_bruto = 0
    #         vr_total_base_retencao = 0
    #         vr_total_ret_princ = 0
    #         vr_total_ret_adic = 0
    #         vr_total_nret_princ = 0
    #         vr_total_nret_adic = 0
    #         for nf in nfs_busca:
    #
    #             if nf.company_id != empresa or nf.inss_value_wh == 0:
    #                 continue
    #
    #             if prestador_id != nf.partner_id and nf.company_id == empresa:
    #
    #                 # Popula os totalizadores do prestador anterior
    #                 if prestador_id:
    #
    #                     # Precisa mudar o status do registro R-2010 ?
    #                     if estabelecimento_id.sped_R2010 and \
    #                             (round(estabelecimento_id.vr_total_bruto, 2) != round(vr_total_bruto, 2) or
    #                              round(estabelecimento_id.vr_total_base_retencao, 2) != round(vr_total_base_retencao, 2) or
    #                              round(estabelecimento_id.vr_total_ret_princ, 2) != round(vr_total_ret_princ, 2) or
    #                              round(estabelecimento_id.vr_total_ret_adic, 2) != round(vr_total_ret_adic, 2) or
    #                              round(estabelecimento_id.vr_total_nret_princ, 2) != round(vr_total_nret_princ, 2) or
    #                              round(estabelecimento_id.vr_total_nret_adic, 2) != round(vr_total_nret_adic, 2)):
    #                         estabelecimento_id.sped_R2010_registro.situacao = '5'
    #                         estabelecimento_id.vr_total_bruto = vr_total_bruto
    #                         estabelecimento_id.vr_total_base_retencao = vr_total_base_retencao
    #                         estabelecimento_id.vr_total_ret_princ = vr_total_ret_princ
    #                         estabelecimento_id.vr_total_ret_adic = vr_total_ret_adic
    #                         estabelecimento_id.vr_total_nret_princ = vr_total_nret_princ
    #                         estabelecimento_id.vr_total_nret_adic = vr_total_nret_adic
    #                     else:
    #                         if estabelecimento_id.situacao_R2010 != '5':
    #                             estabelecimento_id.vr_total_bruto = vr_total_bruto
    #                             estabelecimento_id.vr_total_base_retencao = vr_total_base_retencao
    #                             estabelecimento_id.vr_total_ret_princ = vr_total_ret_princ
    #                             estabelecimento_id.vr_total_ret_adic = vr_total_ret_adic
    #                             estabelecimento_id.vr_total_nret_princ = vr_total_nret_princ
    #                             estabelecimento_id.vr_total_nret_adic = vr_total_nret_adic
    #
    #                     # Zera os totalizadores
    #                     vr_total_bruto = 0
    #                     vr_total_base_retencao = 0
    #                     vr_total_ret_princ = 0
    #                     vr_total_ret_adic = 0
    #                     vr_total_nret_princ = 0
    #                     vr_total_nret_adic = 0
    #
    #                 # Define o próximo prestador_id
    #                 prestador_id = nf.partner_id
    #                 ind_cprb = False  # TODO Colocar no parceiro o campo de indicador de CPRB
    #
    #                 # Acha o registro do prestador
    #                 domain = [
    #                     ('efdreinf_id', '=', self.id),
    #                     ('estabelecimento_id', '=', empresa.id),
    #                     ('prestador_id', '=', prestador_id.id),
    #                 ]
    #                 estabelecimento_id = self.env['sped.efdreinf.estabelecimento'].search(domain)
    #
    #                 # Cria o registro se ele não existir
    #                 if not estabelecimento_id:
    #                     vals = {
    #                         'efdreinf_id': self.id,
    #                         'estabelecimento_id': empresa.id,
    #                         'prestador_id': prestador_id.id,
    #                         'ind_cprb': ind_cprb,
    #                     }
    #                     estabelecimento_id = self.env['sped.efdreinf.estabelecimento'].create(vals)
    #                     self.estabelecimento_ids = [(4, estabelecimento_id.id)]
    #
    #             # Soma os totalizadores desta NF
    #             vr_total_bruto += nf.amount_total
    #             vr_total_base_retencao += nf.inss_base_wh
    #             vr_total_ret_princ += nf.inss_value_wh
    #             vr_total_ret_adic += 0  # TODO Criar o campo vr_total_rec_adic na NF
    #             vr_total_nret_princ += 0  # TODO Criar o campo vr_total_nret_princ na NF
    #             vr_total_nret_adic += 0  # TODO Criar o campo vr_total_nret_adic na NF
    #
    #             # Criar o registro da NF
    #             domain = [
    #                 ('estabelecimento_id', '=', estabelecimento_id.id),
    #                 ('nfs_id', '=', nf.id),
    #             ]
    #             nfs_estabelecimento = self.env['sped.efdreinf.nfs'].search(domain)
    #             if not nfs_estabelecimento:
    #
    #                 # Cria a NF que ainda não existe
    #                 vals = {
    #                     'estabelecimento_id': estabelecimento_id.id,
    #                     'nfs_id': nf.id,
    #                 }
    #                 nfs_estabelecimento = self.env['sped.efdreinf.nfs'].create(vals)
    #                 estabelecimento_id.nfs_ids = [(4, nfs_estabelecimento.id)]
    #
    #             # Criar os registros dos itens das NFs
    #             for item in nf.invoice_line:
    #                 domain = [
    #                     ('efdreinf_nfs_id', '=', nfs_estabelecimento.id),
    #                     ('servico_nfs_id', '=', item.id),
    #                 ]
    #                 servico = self.env['sped.efdreinf.servico'].search(domain)
    #
    #                 if not servico:
    #                     vals = {
    #                         'efdreinf_nfs_id': nfs_estabelecimento.id,
    #                         'servico_nfs_id': item.id,
    #                         'tp_servico_id': item.product_id.tp_servico_id.id or False,
    #                         'vr_base_ret': item.inss_base,
    #                         'vr_retencao': item.inss_wh_value,
    #                         'vr_ret_sub': 0,  # TODO Criar esse campo no item da NF
    #                         'vr_nret_princ': 0,  # TODO Criar esse campo no item da NF
    #                         'vr_servicos_15': 0,  # TODO Criar esse campo no item da NF
    #                         'vr_servicos_20': 0,  # TODO Criar esse campo no item da NF
    #                         'vr_servicos_25': 0,  # TODO Criar esse campo no item da NF
    #                         'vr_adicional': 0,  # TODO Criar esse campo no item da NF
    #                         'vr_nret_adic': 0,  # TODO Criar esse campo no item da NF
    #                     }
    #                     servico = self.env['sped.efdreinf.servico'].create(vals)
    #                     nfs_estabelecimento.servico_ids = [(4, servico.id)]
    #
    #         # Precisa mudar o status do registro R-2010 ?
    #         if estabelecimento_id:
    #             if estabelecimento_id.sped_R2010 and \
    #                     (round(estabelecimento_id.vr_total_bruto, 2) != round(vr_total_bruto, 2) or
    #                      round(estabelecimento_id.vr_total_base_retencao, 2) != round(vr_total_base_retencao, 2) or
    #                      round(estabelecimento_id.vr_total_ret_princ, 2) != round(vr_total_ret_princ, 2) or
    #                      round(estabelecimento_id.vr_total_ret_adic, 2) != round(vr_total_ret_adic, 2) or
    #                      round(estabelecimento_id.vr_total_nret_princ, 2) != round(vr_total_nret_princ, 2) or
    #                      round(estabelecimento_id.vr_total_nret_adic, 2) != round(vr_total_nret_adic, 2)):
    #                 estabelecimento_id.sped_R2010_registro.situacao = '5'
    #                 estabelecimento_id.vr_total_bruto = vr_total_bruto
    #                 estabelecimento_id.vr_total_base_retencao = vr_total_base_retencao
    #                 estabelecimento_id.vr_total_ret_princ = vr_total_ret_princ
    #                 estabelecimento_id.vr_total_ret_adic = vr_total_ret_adic
    #                 estabelecimento_id.vr_total_nret_princ = vr_total_nret_princ
    #                 estabelecimento_id.vr_total_nret_adic = vr_total_nret_adic
    #             else:
    #                 if estabelecimento_id.situacao_R2010 != '5':
    #                     estabelecimento_id.vr_total_bruto = vr_total_bruto
    #                     estabelecimento_id.vr_total_base_retencao = vr_total_base_retencao
    #                     estabelecimento_id.vr_total_ret_princ = vr_total_ret_princ
    #                     estabelecimento_id.vr_total_ret_adic = vr_total_ret_adic
    #                     estabelecimento_id.vr_total_nret_princ = vr_total_nret_princ
    #                     estabelecimento_id.vr_total_nret_adic = vr_total_nret_adic

    # @api.multi
    # def criar_R2010(self):
    #     self.ensure_one()
    #
    #     for estabelecimento in self.estabelecimento_ids:
    #         if not estabelecimento.sped_R2010_registro:
    #
    #             values = {
    #                 'tipo': 'efdreinf',
    #                 'registro': 'R-2010',
    #                 'ambiente': self.company_id.tpAmb,
    #                 'company_id': self.company_id.id,
    #                 'evento': 'evtServTom',
    #                 'origem': ('sped.efdreinf.estabelecimento,%s' % estabelecimento.id),
    #             }
    #
    #             sped_R2010_registro = self.env['sped.transmissao'].create(values)
    #             estabelecimento.sped_R2010_registro = sped_R2010_registro

    # @api.multi
    # def criar_R2099(self):
    #     self.ensure_one()
    #
    #     for efdreinf in self:
    #
    #         values = {
    #             'tipo': 'efdreinf',
    #             'registro': 'R-2099',
    #             'ambiente': self.company_id.tpAmb,
    #             'company_id': self.company_id.id,
    #             'evento': 'evtFechamento',
    #             'origem': ('sped.efdreinf,%s' % efdreinf.id),
    #         }
    #
    #         sped_R2099_registro = self.env['sped.transmissao'].create(values)
    #         efdreinf.sped_R2099_registro = sped_R2099_registro
