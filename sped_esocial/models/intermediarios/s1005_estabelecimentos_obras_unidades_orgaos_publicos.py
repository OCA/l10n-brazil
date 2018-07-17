# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor

from .sped_registro_intermediario import SpedRegistroIntermediario


class SpedEstabelecimentos(models.Model, SpedRegistroIntermediario):
    _name = "sped.estabelecimentos"
    _rec_name = "nome"

    nome = fields.Char(
        string='Nome',
        compute='_compute_name',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    estabelecimento_id = fields.Many2one(
        string='Estabelecimento',
        comodel_name='res.company',
    )
    sped_inclusao = fields.Many2one(
        string='Inclusão',
        comodel_name='sped.registro',
    )
    sped_alteracao = fields.Many2many(
        string='Alterações',
        comodel_name='sped.registro',
    )
    sped_exclusao = fields.Many2one(
        string='Exclusão',
        comodel_name='sped.registro',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('0', 'Inativa'),
            ('1', 'Ativa'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('9', 'Finalizada'),
        ],
        string='Situação no e-Social',
        compute='compute_situacao_esocial',
    )
    precisa_incluir = fields.Boolean(
        string='Precisa incluir dados?',
        compute='compute_precisa_enviar',
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa atualizar dados?',
        compute='compute_precisa_enviar',
    )
    precisa_excluir = fields.Boolean(
        string='Precisa excluir dados?',
        compute='compute_precisa_enviar',
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
    )

    @api.depends('estabelecimento_id')
    def _compute_name(self):
        for registro in self:
            nome = 'Estabelecimento'
            if registro.estabelecimento_id:
                nome += ' ('
                nome += registro.estabelecimento_id.display_name or ''
                nome += ')'
            registro.nome = nome

    @api.depends('sped_inclusao', 'sped_exclusao')
    def compute_situacao_esocial(self):
        for estabelecimento in self:
            situacao_esocial = '0'  # Inativa

            # Se o estabelecimento possui um registro de inclusão confirmado e
            # não precisa atualizar nem excluir então ela está Ativa
            if estabelecimento.sped_inclusao and \
                    estabelecimento.sped_inclusao.situacao == '4':
                if not estabelecimento.precisa_atualizar and not \
                        estabelecimento.precisa_excluir:
                    situacao_esocial = '1'
                else:
                    situacao_esocial = '2'

                # Se já possui um registro de exclusão confirmado, então
                # é situação é Finalizada
                if estabelecimento.sped_exclusao and \
                        estabelecimento.sped_exclusao.situacao == '4':
                    situacao_esocial = '9'

            # Se a empresa possui algum registro que esteja em fase de
            # transmissão então a situação é Aguardando Transmissão
            if estabelecimento.sped_inclusao and \
                    estabelecimento.sped_inclusao.situacao != '4':
                situacao_esocial = '3'
            if estabelecimento.sped_exclusao and \
                    estabelecimento.sped_exclusao.situacao != '4':
                situacao_esocial = '3'
            for alteracao in estabelecimento.sped_alteracao:
                if alteracao.situacao != '4':
                    situacao_esocial = '3'

            # Popula na tabela
            estabelecimento.situacao_esocial = situacao_esocial

    @api.depends('sped_inclusao',
                 'sped_alteracao', 'sped_alteracao.situacao',
                 'sped_exclusao',
                 'company_id.estabelecimento_periodo_inicial_id',
                 'company_id.estabelecimento_periodo_final_id')
    def compute_precisa_enviar(self):

        # Roda todos os registros da lista
        for estabelecimento in self:

            # Inicia as variáveis como False
            precisa_incluir = False
            precisa_atualizar = False
            precisa_excluir = False

            # Se a empresa filial tem um período inicial definido e não
            # tem um registro S1005 de inclusão # confirmado,
            # então precisa incluir
            if estabelecimento.company_id.estabelecimento_periodo_inicial_id:
                if not estabelecimento.sped_inclusao or \
                        estabelecimento.sped_inclusao.situacao != '4':
                    precisa_incluir = True

            # Se a empresa já tem um registro de inclusão confirmado mas a
            # data da última atualização é menor que a o write_date da empresa,
            # então precisa atualizar
            if estabelecimento.sped_inclusao and \
                    estabelecimento.sped_inclusao.situacao == '4':
                if estabelecimento.ultima_atualizacao < \
                        estabelecimento.estabelecimento_id.write_date:
                    precisa_atualizar = True

            # Se a empresa já tem um registro de inclusão confirmado, tem um
            # período final definido e não tem um
            # registro de exclusão confirmado, então precisa excluir
            if estabelecimento.sped_inclusao and \
                    estabelecimento.sped_inclusao.situacao == '4':
                if estabelecimento.company_id.estabelecimento_periodo_final_id:
                    if not estabelecimento.sped_exclusao or \
                            estabelecimento.sped_exclusao != '4':
                        precisa_excluir = True

            # Popula os campos na tabela
            estabelecimento.precisa_incluir = precisa_incluir
            estabelecimento.precisa_atualizar = precisa_atualizar
            estabelecimento.precisa_excluir = precisa_excluir

    @api.depends('sped_inclusao',
                 'sped_alteracao', 'sped_alteracao.situacao',
                 'sped_exclusao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for estabelecimento in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if estabelecimento.sped_inclusao and \
                    estabelecimento.sped_inclusao.situacao == '4':
                ultima_atualizacao = estabelecimento.sped_inclusao.data_hora_origem

            # Se tiver alterações, pega a data/hora de
            # origem da última alteração
            for alteracao in estabelecimento.sped_alteracao:
                if alteracao.situacao == '4':
                    if alteracao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = alteracao.data_hora_origem

            # Se tiver exclusão, pega a data/hora de origem da exclusão
            if estabelecimento.sped_exclusao and \
                    estabelecimento.sped_exclusao.situacao == '4':
                ultima_atualizacao = estabelecimento.sped_exclusao.data_hora_origem

            # Popula o campo na tabela
            estabelecimento.ultima_atualizacao = ultima_atualizacao

    # Roda a atualização do e-Social (não transmite ainda)
    @api.multi
    def atualizar_esocial(self):
        self.ensure_one()

        values = {
            'tipo': 'esocial',
            'registro': 'S-1005',
            'ambiente': self.company_id.esocial_tpAmb,
            'company_id': self.company_id.id,
            'evento': 'evtTabEstab',
            'origem': ('res.company,%s' % self.estabelecimento_id.id),
            'origem_intermediario': ('sped.estabelecimentos,%s' % self.id),
        }

        # Criar o registro S-1005 de inclusão, se for necessário
        if self.precisa_incluir:
            values['operacao'] = 'I'

            sped_inclusao = self.env['sped.registro'].create(values)
            self.sped_inclusao = sped_inclusao

        # Criar o registro S-1005 de alteração, se for necessário
        if self.precisa_atualizar:
            values['operacao'] = 'A'

            sped_atualizacao = self.env['sped.registro'].create(values)
            self.sped_alteracao = [(4, sped_atualizacao.id)]

        # Criar o registro S-1005 de exclusão, se for necessário
        if self.precisa_excluir:
            values['operacao'] = 'E'

            sped_exclusao = self.env['sped.registro'].create(values)
            self.sped_exclusao = sped_exclusao

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        # Cria o registro
        S1005 = pysped.esocial.leiaute.S1005_2()

        # Popula ideEvento
        S1005.tpInsc = '1'
        S1005.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        S1005.evento.ideEvento.tpAmb.valor = int(ambiente)

        # Processo de Emissão = Aplicativo do Contribuinte
        S1005.evento.ideEvento.procEmi.valor = '1'
        S1005.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S1005.evento.ideEmpregador.tpInsc.valor = '1'
        S1005.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        # Popula a operação que será realizada com esse registro
        S1005.evento.infoEstab.operacao = operacao

        # Popula infoEstab (Informações do Estabelecimentou o Obra)
        S1005.evento.infoEstab.ideEstab.tpInsc.valor = '1'
        S1005.evento.infoEstab.ideEstab.nrInsc.valor = limpa_formatacao(
            self.estabelecimento_id.cnpj_cpf)

        S1005.evento.infoEstab.ideEstab.iniValid.valor = \
            self.estabelecimento_id.estabelecimento_periodo_inicial_id.code[3:7] + '-' + \
            self.estabelecimento_id.estabelecimento_periodo_inicial_id.code[0:2]

        S1005.evento.infoEstab.dadosEstab.cnaePrep.valor = limpa_formatacao(
            self.estabelecimento_id.cnae_main_id.code)

        # Inclusão, não precisa adicionar mais nada aqui

        # Se for operacao=='A' (Alteração) Popula idePeriodo usando company_id.periodo_atualizacao_id
        if operacao == 'A':

            # Se o campo periodo_atualizacao_id não estiver preenchido, retorne erro de dados para o usuário
            if not self.estabelecimento_id.estabelecimento_periodo_atualizacao_id:
                raise ValidationError("O campo 'Período da Última Atualização' no Estabelecimento não está preenchido !")

            # Popula infoEstab.novaValidade
            S1005.evento.infoEstab.novaValidade.iniValid.valor = \
                self.estabelecimento_id.estabelecimento_periodo_atualizacao_id.code[3:7] + '-' + \
                self.estabelecimento_id.estabelecimento_periodo_atualizacao_id.code[0:2]

        # Se for operacao=='E' (Exclusão) Popula idePeriodo usando
        if operacao == 'E':

            # Se o campo periodo_exclusao_id não estiver preenchido, retorne erro de dados para o usuário
            if not self.estabelecimento_id.estabelecimento_periodo_final_id:
                raise ValidationError("O campo 'Período Final' no Estabelecimento não está preenchido !")

            # Popula infoEmpregador.idePeriodo.fimValid
            S1005.evento.infoEstab.novaValidade.fimValid.valor = \
                self.estabelecimento_id.estabelecimento_periodo_final_id.code[3:7] + '-' + \
                self.estabelecimento_id.estabelecimento_periodo_final_id.code[0:2]

        # Localiza o percentual de RAT e FAP para esta empresa neste período
        if self.company_id.estabelecimento_periodo_atualizacao_id:
            ano = self.estabelecimento_id.estabelecimento_periodo_atualizacao_id.fiscalyear_id.code
        else:
            ano = self.estabelecimento_id.estabelecimento_periodo_inicial_id.fiscalyear_id.code
        domain = [
            ('company_id', '=', self.company_id.id),
            ('year', '=', int(ano)),
        ]
        rat_fap = self.env['l10n_br.hr.rat.fap'].search(domain)
        if not rat_fap:
            raise Exception(
                "Tabela de RAT/FAP não encontrada para este período")

        # Popula aligGilRat
        S1005.evento.infoEstab.dadosEstab.aliqGilrat.aliqRat.valor = int(
            rat_fap.rat_rate)
        S1005.evento.infoEstab.dadosEstab.aliqGilrat.fap.valor = formata_valor(
            rat_fap.fap_rate)
        S1005.evento.infoEstab.dadosEstab.aliqGilrat.aliqRatAjust.valor = \
            formata_valor(rat_fap.rat_rate * rat_fap.fap_rate)

        # Popula infoCaepf
        if self.estabelecimento_id.tp_caepf:
            S1005.evento.infoEstab.dadosEstab.infoCaepf.tpCaepf.valor = int(
                self.estabelecimento_id.tp_caepf)

        # Popula infoTrab
        S1005.evento.infoEstab.dadosEstab.infoTrab.regPt.valor = \
            self.estabelecimento_id.reg_pt

        # Popula infoApr
        S1005.evento.infoEstab.dadosEstab.infoTrab.infoApr.contApr.valor = \
            self.estabelecimento_id.cont_apr
        S1005.evento.infoEstab.dadosEstab.infoTrab.infoApr.contEntEd.valor = \
            self.estabelecimento_id.cont_ent_ed

        # Popula infoEntEduc
        for entidade in self.estabelecimento_id.info_ent_educ_ids:
            info_ent_educ = pysped.esocial.leiaute.InfoEntEduc_2()
            info_ent_educ.nrInsc = limpa_formatacao(entidade.cnpj_cpf)
            S1005.evento.infoEstab.dadosEstab.infoTrab.infoApr.infoEntEduc\
                .append(info_ent_educ)

        # Popula infoPCD
        if self.estabelecimento_id.cont_pcd:
            S1005.evento.infoEstab.dadosEstab.infoTrab.infoPCD.contPCD = \
                self.estabelecimento_id.cont_pcd

        return S1005

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()
