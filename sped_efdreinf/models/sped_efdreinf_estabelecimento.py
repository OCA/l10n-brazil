# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import \
    SpedRegistroIntermediario
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor


class SpedEfdReinfEstab(models.Model, SpedRegistroIntermediario):
    _name = 'sped.efdreinf.estabelecimento'
    _description = u'Prestadores de Eventos Periodicos EFD/Reinf'
    _rec_name = 'nome'
    _order = "nome"

    nome = fields.Char(
        string='Nome',
        compute='_compute_nome',
        store=True,
    )
    periodo_id = fields.Many2one(
        string='Período',
        comodel_name='account.period',
    )
    efdreinf_id = fields.Many2one(
        string='EFD/Reinf',
        comodel_name='sped.efdreinf',
        ondelete="cascade",
    )
    estabelecimento_id = fields.Many2one(
        string='Estabelecimento',
        comodel_name='res.company',
    )
    prestador_id = fields.Many2one(
        string='Prestador',
        comodel_name='res.partner',
    )
    vr_total_bruto = fields.Float(
        string='Valor Total Bruto',
        digits=[14, 2],
    )
    vr_total_base_retencao = fields.Float(
        string='Base de Retenção',
        digits=[14, 2],
    )
    vr_total_ret_princ = fields.Float(
        string='Total de Retenções',
        digits=[14, 2],
    )
    vr_total_ret_adic = fields.Float(
        string='Adicionais de Retenção das NFs',
        digits=[14, 2],
    )
    vr_total_nret_princ = fields.Float(
        string='Total Não Retido devido a Ações',
        digits=[14, 2],
    )
    vr_total_nret_adic = fields.Float(
        string='Total Retido Adicional devido a Ações',
        digits=[14, 2],
    )
    ind_cprb = fields.Binary(
        string='Prestador é CPRB ?',
    )
    nfs_ids = fields.One2many(
        string='Notas Fiscais',
        comodel_name='sped.efdreinf.nfs',
        inverse_name='estabelecimento_id',
    )
    sped_r2010 = fields.Boolean(
        string='Ativação EFD/Reinf',
        compute='_compute_sped_r2010',
    )
    sped_r2010_registro = fields.Many2one(
        string='Registro R-2010',
        comodel_name='sped.registro',
    )
    situacao_r2010 = fields.Selection(
        string='Situação R-2010',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        related='sped_r2010_registro.situacao',
        readonly=True,
    )
    sped_r2010_retificacao = fields.Many2one(
        string='Registro R-2010 (Retificação)',
        comodel_name='sped.registro',
    )

    @api.depends('estabelecimento_id', 'prestador_id')
    def _compute_nome(self):
        for prestador in self:
            nome = prestador.estabelecimento_id.name
            if prestador.prestador_id and prestador.prestador_id != prestador.estabelecimento_id:
                nome += '/' + prestador.prestador_id.name

            prestador.nome = nome

    @api.depends('sped_r2010_registro')
    def _compute_sped_r2010(self):
        for efdreinf in self:
            efdreinf.sped_r2010 = True if efdreinf.sped_r2010_registro else False

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        # Calcula o Período de Apuração no formato YYYY-MM
        periodo = self.efdreinf_id.periodo_id.code[3:7] + '-' + self.efdreinf_id.periodo_id.code[0:2]

        # Cria o registro
        R2010 = pysped.efdreinf.leiaute.R2010_1()

        # Popula ideEvento
        R2010.evento.ideEvento.tpAmb.valor = ambiente
        R2010.evento.ideEvento.indRetif.valor = '1'
        R2010.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
        R2010.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0
        R2010.evento.ideEvento.perApur.valor = periodo

        # Popula ideContri (Dados do Contribuinte)
        R2010.evento.ideContri.tpInsc.valor = '1'
        if self.estabelecimento_id.eh_empresa_base:
            matriz = self.estabelecimento_id
        else:
            matriz = self.estabelecimento_id.matriz
        R2010.evento.ideContri.nrInsc.valor = limpa_formatacao(
            matriz.cnpj_cpf)[0:8]

        # Popula infoServTom (Informações do Tomador)
        R2010.evento.infoServTom.ideEstabObra.tpInscEstab.valor = '1'
        R2010.evento.infoServTom.ideEstabObra.nrInscEstab.valor = limpa_formatacao(
            self.estabelecimento_id.cnpj_cpf)
        R2010.evento.infoServTom.ideEstabObra.indObra.valor = '0'
        R2010.evento.infoServTom.ideEstabObra.idePrestServ.cnpjPrestador.valor = limpa_formatacao(
            self.prestador_id.cnpj_cpf)
        R2010.evento.infoServTom.ideEstabObra.idePrestServ.vlrTotalBruto.valor = formata_valor(
            self.vr_total_bruto)
        R2010.evento.infoServTom.ideEstabObra.idePrestServ.vlrTotalBaseRet.valor = formata_valor(
            self.vr_total_base_retencao)
        R2010.evento.infoServTom.ideEstabObra.idePrestServ.vlrTotalRetPrinc.valor = formata_valor(
            self.vr_total_ret_princ)
        if self.vr_total_ret_adic:
            R2010.evento.infoServTom.ideEstabObra.idePrestServ.vlrTotalRetAdic.valor = formata_valor(
                self.vr_total_ret_adic)
        if self.vr_total_nret_princ:
            R2010.evento.infoServTom.ideEstabObra.idePrestServ.vlrTotalNRetPrinc.valor = formata_valor(
                self.vr_total_nret_princ)
        if self.vr_total_nret_adic:
            R2010.evento.infoServTom.ideEstabObra.idePrestServ.vlrTotalNRetAdic.valor = formata_valor(
                self.vr_total_nret_adic)
        R2010.evento.infoServTom.ideEstabObra.idePrestServ.indCPRB.valor = '1' if self.ind_cprb else '0'

        # Popula nfs
        for nfs in self.nfs_ids:
            R2010_nfs = pysped.efdreinf.leiaute.NFS_1()
            R2010_nfs.serie.valor = nfs.serie
            R2010_nfs.numDocto.valor = nfs.num_docto
            R2010_nfs.dtEmissaoNF.valor = nfs.dt_emissao_nf[0:10]
            R2010_nfs.vlrBruto.valor = formata_valor(nfs.vr_bruto)
            if nfs.observacoes:
                R2010_nfs.obs.valor = nfs.observacoes

            # Popula infoTpServ
            for item in nfs.servico_ids:
                R2010_infoTpServ = pysped.efdreinf.leiaute.InfoTpServ_1()
                R2010_infoTpServ.tpServico.valor = item.tp_servico_id.codigo
                R2010_infoTpServ.vlrBaseRet.valor = formata_valor(
                    item.vr_base_ret)
                R2010_infoTpServ.vlrRetencao.valor = formata_valor(
                    item.vr_retencao)
                if item.vr_ret_sub:
                    R2010_infoTpServ.vlrRetSub.valor = formata_valor(
                        item.vr_ret_sub)
                if item.vr_nret_princ:
                    R2010_infoTpServ.vlrNRetPrinc.valor = formata_valor(
                        item.vr_nret_princ)
                if item.vr_servicos_15:
                    R2010_infoTpServ.vlrServicos15.valor = formata_valor(
                        item.vr_servicos_15)
                if item.vr_servicos_20:
                    R2010_infoTpServ.vlrServicos20.valor = formata_valor(
                        item.vr_servicos_20)
                if item.vr_servicos_25:
                    R2010_infoTpServ.vlrServicos25.valor = formata_valor(
                        item.vr_servicos_25)
                if item.vr_adicional:
                    R2010_infoTpServ.vlrAdicional.valor = formata_valor(
                        item.vr_adicional)
                if item.vr_nret_adic:
                    R2010_infoTpServ.vlrNRetAdic.valor = formata_valor(
                        item.vr_nret_adic)

                # Adiciona infoTpServ em nfs
                R2010_nfs.infoTpServ.append(R2010_infoTpServ)

            # Adiciona nfs em idePrestServ
            R2010.evento.infoServTom.ideEstabObra.idePrestServ.nfs.append(
                R2010_nfs)

        return R2010

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()
