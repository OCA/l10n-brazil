# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor

from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario


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
    precisa_incluir = fields.Boolean(
        string='Precisa incluir dados?',
        compute='compute_precisa_enviar',
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa atualizar dados?',
        related='estabelecimento_id.precisa_atualizar_estabelecimento',
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

    @api.depends('sped_inclusao.situacao', 'sped_alteracao.situacao', 'sped_exclusao.situacao', 'precisa_atualizar')
    def compute_situacao_esocial(self):
        for estabelecimento in self:
            situacao_esocial = '0'  # Inativa

            # Se o estabelecimento possui um registro de inclusão com sucesso(4) e
            # não precisa atualizar nem excluir então ela está Ativa
            if estabelecimento.sped_inclusao and estabelecimento.sped_inclusao.situacao == '4':
                if not estabelecimento.precisa_atualizar and not estabelecimento.precisa_excluir:
                    situacao_esocial = '1'
                else:
                    situacao_esocial = '2'

                # Se já possui um registro de exclusão confirmado, então
                # é situação é Finalizada
                if estabelecimento.sped_exclusao and estabelecimento.sped_exclusao.situacao == '4':
                    situacao_esocial = '9'

            # Se a empresa possui algum registro que esteja em fase de
            # transmissão então a situação é Aguardando Transmissão
            if estabelecimento.sped_inclusao and estabelecimento.sped_inclusao.situacao != '4':
                situacao_esocial = '3'
                registro = estabelecimento.sped_inclusao
            if estabelecimento.sped_exclusao and estabelecimento.sped_exclusao.situacao != '4':
                situacao_esocial = '3'
                registro = estabelecimento.sped_exclusao
            for alteracao in estabelecimento.sped_alteracao:
                if alteracao.situacao != '4':
                    situacao_esocial = '3'
                    registro = alteracao

            # Se a situação == '3', verifica se já foi transmitida ou não (se já foi transmitida
            # então a situacao_esocial deve ser '4'
            if situacao_esocial == '3' and registro.situacao == '2':
                situacao_esocial = '4'

            # Verifica se algum registro está com erro de transmissão
            if estabelecimento.sped_inclusao and estabelecimento.sped_inclusao.situacao == '3':
                situacao_esocial = '5'
            if estabelecimento.sped_exclusao and estabelecimento.sped_exclusao.situacao == '3':
                situacao_esocial = '5'
            for alteracao in estabelecimento.sped_alteracao:
                if alteracao.situacao == '3':
                    situacao_esocial = '5'

            # Popula na tabela
            estabelecimento.situacao_esocial = situacao_esocial

    @api.depends('sped_inclusao.situacao', 'sped_alteracao.situacao', 'sped_exclusao.situacao',
                 'company_id.estabelecimento_periodo_inicial_id',
                 'company_id.estabelecimento_periodo_final_id')
    def compute_precisa_enviar(self):

        # Roda todos os registros da lista
        for estabelecimento in self:

            # Inicia as variáveis como False
            precisa_incluir = False
            # precisa_atualizar = False
            precisa_excluir = False

            # Se a empresa filial tem um período inicial definido e não
            # tem um registro S1005 de inclusão # confirmado,
            # então precisa incluir
            if estabelecimento.company_id.estabelecimento_periodo_inicial_id:
                if not estabelecimento.sped_inclusao or \
                        estabelecimento.sped_inclusao.situacao != '4':
                    precisa_incluir = True

            # # Se a empresa já tem um registro de inclusão confirmado mas a
            # # data da última atualização é menor que a o write_date da empresa,
            # # então precisa atualizar
            # if estabelecimento.sped_inclusao and \
            #         estabelecimento.sped_inclusao.situacao == '4':
            #     if estabelecimento.ultima_atualizacao < \
            #             estabelecimento.estabelecimento_id.write_date:
            #         precisa_atualizar = True

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
            # estabelecimento.precisa_atualizar = precisa_atualizar
            estabelecimento.precisa_excluir = precisa_excluir

    @api.depends('sped_inclusao.situacao', 'sped_alteracao.situacao', 'sped_exclusao.situacao')
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
    def gerar_registro(self):
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
        if self.precisa_incluir and not self.sped_inclusao:
            values['operacao'] = 'I'

            sped_inclusao = self.env['sped.registro'].create(values)
            self.sped_inclusao = sped_inclusao

        # Criar o registro S-1005 de alteração, se for necessário
        if self.precisa_atualizar:
            values['operacao'] = 'A'

            # Verifica se já tem um registro de atualização em aberto
            reg = False
            for registro in self.sped_alteracao:
                if registro.situacao in ['2', '3']:
                    reg = registro
            if not reg:
                sped_atualizacao = self.env['sped.registro'].create(values)
                self.sped_alteracao = [(4, sped_atualizacao.id)]

        # Criar o registro S-1005 de exclusão, se for necessário
        if self.precisa_excluir and not self.sped_exclusao:
            values['operacao'] = 'E'

            sped_exclusao = self.env['sped.registro'].create(values)
            self.sped_exclusao = sped_exclusao

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):

        # Validação
        validacao = ""

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
                validacao += "O campo 'Período da Última Atualização' no Estabelecimento não está preenchido !\n"
            else:
                # Popula infoEstab.novaValidade
                S1005.evento.infoEstab.novaValidade.iniValid.valor = \
                    self.estabelecimento_id.estabelecimento_periodo_atualizacao_id.code[3:7] + '-' + \
                    self.estabelecimento_id.estabelecimento_periodo_atualizacao_id.code[0:2]

        # Se for operacao=='E' (Exclusão) Popula idePeriodo usando
        if operacao == 'E':

            # Se o campo periodo_exclusao_id não estiver preenchido, retorne erro de dados para o usuário
            if not self.estabelecimento_id.estabelecimento_periodo_final_id:
                validacao += "O campo 'Período Final' no Estabelecimento não está preenchido !\n"
            else:
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
            validacao += "Tabela de RAT/FAP não encontrada para este período\n"
        else:
            # Popula aligGilRat
            S1005.evento.infoEstab.dadosEstab.aliqGilrat.aliqRat.valor = int(
                rat_fap.rat_rate)
            S1005.evento.infoEstab.dadosEstab.aliqGilrat.fap.valor = formata_valor(
                rat_fap.fap_rate)
            S1005.evento.infoEstab.dadosEstab.aliqGilrat.aliqRatAjust.valor = \
                formata_valor(rat_fap.rat_rate * rat_fap.fap_rate)

        # Popula infoCaepf
        if self.estabelecimento_id.tp_caepf:
            info_caepf = pysped.esocial.leiaute.S1005_InfoCaepf_2()
            info_caepf.tpCaepf.valor = int(
                self.estabelecimento_id.tp_caepf)
            S1005.evento.infoEstab.dadosEstab.infoCaepf.append(info_caepf)

        # Popula infoTrab
        S1005.evento.infoEstab.dadosEstab.infoTrab.regPt.valor = \
            self.estabelecimento_id.reg_pt

        # Popula infoApr
        # Contrata aprendiz?
        S1005.evento.infoEstab.dadosEstab.infoTrab.infoApr.contApr.valor = \
            self.estabelecimento_id.cont_apr

        # Se nao contratar, nao preecher nada
        if self.estabelecimento_id.cont_apr != '0':
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
            info_pcd = pysped.esocial.leiaute.S1005_InfoPCD_2()
            info_pcd.contPCD.valor = self.estabelecimento_id.cont_pcd
            S1005.evento.infoEstab.dadosEstab.infoTrab.infoPCD.append(info_pcd)

        return S1005, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        self.estabelecimento_id.precisa_atualizar = False

    @api.multi
    def transmitir(self):
        self.ensure_one()

        if self.situacao_esocial in ['2', '3', '5']:
            # Identifica qual registro precisa transmitir
            registro = False
            if self.sped_inclusao.situacao in ['1', '3']:
                registro = self.sped_inclusao
            else:
                for r in self.sped_alteracao:
                    if r.situacao in ['1', '3']:
                        registro = r

            if not registro:
                if self.sped_exclusao.situacao in ['1', '3']:
                    registro = self.sped_exclusao

            # Com o registro identificado, é só rodar o método transmitir_lote() do registro
            if registro:
                registro.transmitir_lote()

    @api.multi
    def consultar(self):
        self.ensure_one()

        if self.situacao_esocial in ['4']:
            # Identifica qual registro precisa consultar
            registro = False
            if self.sped_inclusao.situacao == '2':
                registro = self.sped_inclusao
            else:
                for r in self.sped_alteracao:
                    if r.situacao == '2':
                        registro = r

            if not registro:
                if self.sped_exclusao == '2':
                    registro = self.sped_exclusao

            # Com o registro identificado, é só rodar o método consulta_lote() do registro
            if registro:
                registro.consulta_lote()
