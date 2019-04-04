# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor
from datetime import datetime
import pysped


class SpedEsocialExclusao(models.Model, SpedRegistroIntermediario):
    _name = "sped.esocial.exclusao"
    _rec_name = "nome"
    _order = "company_id"

    nome = fields.Char(
        string='Nome',
        compute='_compute_name',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company'
    )
    sped_registro_id = fields.Many2one(
        comodel_name='sped.registro',
    )
    sped_transmissao_id = fields.Many2one(
        string='Registro de Exclusão',
        comodel_name='sped.registro'
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('0', 'Inativo'),
            ('1', 'Ativo'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('4', 'Aguardando Processamento'),
            ('5', 'Erro(s)'),
            ('9', 'Finalizado'),
        ],
        string='Situação no e-Social',
        compute='compute_situacao_esocial',
        store=True,
    )

    @api.depends('company_id')
    def _compute_name(self):
        for registro in self:
            nome = 'S-3000 Exclusão'
            if registro.company_id:
                nome += ' ('
                nome += registro.sped_registro_id.display_name or ''
                nome += ')'
            registro.nome = nome

    @api.depends('sped_transmissao_id.situacao')
    def compute_situacao_esocial(self):
        for exclusao in self:
            situacao_esocial = '0'  # Inativa

            # Se a empresa possui um registro de inclusão confirmado e não precisa atualizar nem excluir
            # então ela está Ativa
            if exclusao.sped_transmissao_id and exclusao.sped_transmissao_id.situacao == '4':
                situacao_esocial = '1'

            # Se a empresa possui algum registro que esteja em fase de transmissão
            # então a situação é Aguardando Transmissão
            if exclusao.sped_transmissao_id and exclusao.sped_transmissao_id.situacao != '4':
                situacao_esocial = '3'

            # Se a situação == '3', verifica se já foi transmitida ou não (se já foi transmitida
            # então a situacao_esocial deve ser '4'
            if situacao_esocial == '3' and exclusao.sped_transmissao_id.situacao == '2':
                situacao_esocial = '4'

            # Verifica se algum registro está com erro de transmissão
            if exclusao.sped_transmissao_id and exclusao.sped_transmissao_id.situacao == '3':
                situacao_esocial = '5'

            # Popula na tabela
            exclusao.situacao_esocial = situacao_esocial

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        self.ensure_one()

        # Validação
        validacao = ""

        # Cria o registro
        S3000 = pysped.esocial.leiaute.S3000_2()

        # Popula ideEvento
        S3000.tpInsc = '1'
        S3000.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        S3000.evento.ideEvento.tpAmb.valor = int(ambiente)
        S3000.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
        S3000.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S3000.evento.ideEmpregador.tpInsc.valor = '1'
        S3000.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        # Popula infoExclusao
        S3000.evento.infoExclusao.tpEvento.valor = self.sped_registro_id.registro
        S3000.evento.infoExclusao.nrRecEvt.valor = self.sped_registro_id.recibo

        # Se for um registro Não-periódico, deve enviar a tag ideTrabalhador
        if self.sped_registro_id.registro in ['S-2190', 'S-2200', 'S-2205', 'S-2206', 'S-2210',
                                              'S-2220', 'S-2230', 'S-2240', 'S-2241', 'S-2250',
                                              'S-2260', 'S-2298', 'S-2299', 'S-2300', 'S-2306',
                                              'S-2399', 'S-1200', 'S-1202', 'S-1210']:
            ide_trabalhador = pysped.esocial.leiaute.S3000_IdeTrabalhador_2()
            trabalhador = self.sped_registro_id.origem.retorna_trabalhador()
            ide_trabalhador.cpfTrab.valor = limpa_formatacao(trabalhador.cpf)
            if self.sped_registro_id.registro not in ['S-1210', 'S-2190']:
                ide_trabalhador.nisTrab.valor = limpa_formatacao(trabalhador.pis_pasep)
            S3000.evento.infoExclusao.ideTrabalhador.append(ide_trabalhador)

        # Se for um registro Período, deve enviar a tag ideFolhaPagto
        if self.sped_registro_id.registro in ['S-1200', 'S-1202', 'S-1207', 'S-1210', 'S-1250',
                                              'S-1260', 'S-1270', 'S-1280', 'S-1295', 'S-1300']:
            ide_folhapagto = pysped.esocial.leiaute.S3000_IdeFolhaPagto_2()
        if '13/' not in \
                self.sped_registro_id.origem_intermediario.periodo_id.code:
            ide_folhapagto.indApuracao.valor = '1'
            ide_folhapagto.perApur.valor = \
                self.sped_registro_id.origem_intermediario.periodo_id.code[3:7]\
                + '-' + \
                self.sped_registro_id.origem_intermediario.periodo_id.code[0:2]
            S3000.evento.infoExclusao.ideFolhaPagto.append(ide_folhapagto)
        else:
            ide_folhapagto.indApuracao.valor = '2'
            ide_folhapagto.perApur.valor = \
                self.sped_registro_id.origem_intermediario.periodo_id.code[3:7]
            S3000.evento.infoExclusao.ideFolhaPagto.append(ide_folhapagto)

        return S3000, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        # Mudar o status do registro de origem para 7-Excluído
        self.sped_registro_id.situacao = '7'
        registro_id = self.sped_registro_id
        self.sped_registro_id.origem_intermediario.sped_registro_excluido_ids =\
            [(4, registro_id.id)]
        self.sped_registro_id.origem_intermediario.sped_registro = False

    @api.multi
    def transmitir(self):
        self.ensure_one()

        if self.situacao_esocial in ['2', '3', '5']:
            # Identifica qual registro precisa transmitir
            registro = self.sped_transmissao_id

            # Com o registro identificado, é só rodar o método transmitir_lote() do registro
            if registro:
                registro.transmitir_lote()

    @api.multi
    def consultar(self):
        self.ensure_one()

        if self.situacao_esocial in ['4']:
            # Identifica qual registro precisa consultar
            registro = self.sped_transmissao_id

            # Com o registro identificado, é só rodar o método consulta_lote() do registro
            if registro:
                registro.consulta_lote()
