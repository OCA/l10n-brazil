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


class SpedEmpregador(models.Model, SpedRegistroIntermediario):
    _name = "sped.empregador"
    _rec_name = "nome"
    _order = "company_id"

    nome = fields.Char(
        string='Nome',
        compute='_compute_name',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
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
        related='company_id.precisa_atualizar',
    )
    precisa_excluir = fields.Boolean(
        string='Precisa excluir dados?',
        compute='compute_precisa_enviar',
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
    )

    # Controle de limpeza do database (para uso em Produção Restrita somente)
    limpar_db = fields.Boolean(
        string='Limpar DB',
    )

    @api.depends('company_id')
    def _compute_name(self):
        for registro in self:
            nome = 'Empregador'
            if registro.company_id:
                nome += ' ('
                nome += registro.company_id.display_name or ''
                nome += ')'
            registro.nome = nome

    @api.depends('sped_inclusao.situacao', 'sped_alteracao.situacao', 'sped_exclusao.situacao', 'precisa_atualizar')
    def compute_situacao_esocial(self):
        for empregador in self:
            situacao_esocial = '0'  # Inativa

            # Se a empresa possui um registro de inclusão confirmado e não precisa atualizar nem excluir
            # então ela está Ativa
            if empregador.sped_inclusao and empregador.sped_inclusao.situacao == '4':
                if not empregador.precisa_atualizar and not empregador.precisa_excluir:
                    situacao_esocial = '1'
                else:
                    situacao_esocial = '2'

                # Se já possui um registro de exclusão confirmado, então
                # é situação é Finalizada
                if empregador.sped_exclusao and empregador.sped_exclusao.situacao == '4':
                    situacao_esocial = '9'

            # Se a empresa possui algum registro que esteja em fase de transmissão
            # então a situação é Aguardando Transmissão
            if empregador.sped_inclusao and empregador.sped_inclusao.situacao != '4':
                situacao_esocial = '3'
                registro = empregador.sped_inclusao
            if empregador.sped_exclusao and empregador.sped_exclusao.situacao != '4':
                situacao_esocial = '3'
                registro = empregador.sped_exclusao
            for alteracao in empregador.sped_alteracao:
                if alteracao.situacao != '4':
                    situacao_esocial = '3'
                    registro = alteracao

            # Se a situação == '3', verifica se já foi transmitida ou não (se já foi transmitida
            # então a situacao_esocial deve ser '4'
            if situacao_esocial == '3' and registro.situacao == '2':
                situacao_esocial = '4'

            # Verifica se algum registro está com erro de transmissão
            if empregador.sped_inclusao and empregador.sped_inclusao.situacao == '3':
                situacao_esocial = '5'
            if empregador.sped_exclusao and empregador.sped_exclusao.situacao == '3':
                situacao_esocial = '5'
            for alteracao in empregador.sped_alteracao:
                if alteracao.situacao == '3':
                    situacao_esocial = '5'

            # Popula na tabela
            empregador.situacao_esocial = situacao_esocial

    @api.depends('sped_inclusao.situacao', 'sped_alteracao.situacao', 'sped_exclusao.situacao',
                 'company_id.esocial_periodo_inicial_id', 'company_id.esocial_periodo_final_id')
    def compute_precisa_enviar(self):

        # Roda todos os registros da lista
        for empregador in self:

            # Inicia as variáveis como False
            precisa_incluir = False
            # precisa_atualizar = False
            precisa_excluir = False

            # Se a situação for '3' (Aguardando Transmissão) fica tudo falso
            if self.situacao_esocial != '3':

                # Se a empresa matriz tem um período inicial definido e não tem um registro S1000 de inclusão
                # confirmado, então precisa incluir
                if empregador.company_id.esocial_periodo_inicial_id:
                    if not empregador.sped_inclusao or empregador.sped_inclusao.situacao != '4':
                        precisa_incluir = True

                # # Se a empresa já tem um registro de inclusão confirmado mas a data da última atualização
                # # é menor que a o write_date da empresa, então precisa atualizar
                # if empregador.sped_inclusao and empregador.sped_inclusao.situacao == '4':
                #     if empregador.ultima_atualizacao < empregador.company_id.write_date:
                #         precisa_atualizar = True

                # Se a empresa já tem um registro de inclusão confirmado, tem um período final definido e
                # não tem um registro de exclusão confirmado, então precisa excluir
                if empregador.sped_inclusao and empregador.sped_inclusao.situacao == '4':
                    if empregador.company_id.esocial_periodo_final_id:
                        if not empregador.sped_exclusao or empregador.sped_exclusao != '4':
                            precisa_excluir = True

            # Popula os campos na tabela
            empregador.precisa_incluir = precisa_incluir
            # empregador.precisa_atualizar = precisa_atualizar
            empregador.precisa_excluir = precisa_excluir

    @api.depends('sped_inclusao.situacao', 'sped_alteracao.situacao', 'sped_exclusao.situacao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for empregador in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if empregador.sped_inclusao and empregador.sped_inclusao.situacao == '4':
                ultima_atualizacao = empregador.sped_inclusao.data_hora_origem

            # Se tiver alterações, pega a data/hora de origem da última alteração
            for alteracao in empregador.sped_alteracao:
                if alteracao.situacao == '4':
                    if alteracao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = alteracao.data_hora_origem

            # Se tiver exclusão, pega a data/hora de origem da exclusão
            if empregador.sped_exclusao and empregador.sped_exclusao.situacao == '4':
                ultima_atualizacao = empregador.sped_exclusao.data_hora_origem

            # Popula o campo na tabela
            empregador.ultima_atualizacao = ultima_atualizacao

    # Roda a atualização do e-Social (não transmite ainda)
    @api.multi
    def gerar_registro(self):
        self.ensure_one()

        # Criar o registro S-1000 de inclusão, se for necessário
        if self.precisa_incluir and not self.sped_inclusao:
            values = {
                'tipo': 'esocial',
                'registro': 'S-1000',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'operacao': 'I',
                'evento': 'evtInfoEmpregador',
                'origem': ('res.company,%s' % self.company_id.id),
                'origem_intermediario': ('sped.empregador,%s' % self.id),
            }

            sped_inclusao = self.env['sped.registro'].create(values)
            self.sped_inclusao = sped_inclusao

        # Criar o registro S-1000 de alteração, se for necessário
        if self.precisa_atualizar:
            # Verifica se já tem um registro de atualização em aberto
            reg = False
            for registro in self.sped_alteracao:
                if registro.situacao in ['2', '3']:
                    reg = registro
            if not reg:
                values = {
                    'tipo': 'esocial',
                    'registro': 'S-1000',
                    'ambiente': self.company_id.esocial_tpAmb,
                    'company_id': self.company_id.id,
                    'operacao': 'A',
                    'evento': 'evtInfoEmpregador',
                    'origem': ('res.company,%s' % self.company_id.id),
                    'origem_intermediario': ('sped.empregador,%s' % self.id),
                }

                sped_alteracao = self.env['sped.registro'].create(values)
                self.sped_alteracao = [(4, sped_alteracao.id)]

        # Criar o registro S-1000 de exclusão, se for necessário
        if self.precisa_excluir and not self.sped_exclusao:
            values = {
                'tipo': 'esocial',
                'registro': 'S-1000',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'operacao': 'E',
                'evento': 'evtInfoEmpregador',
                'origem': ('res.company,%s' % self.company_id.id),
                'origem_intermediario': ('sped.empregador,%s' % self.id),
            }

            sped_exclusao = self.env['sped.registro'].create(values)
            self.sped_exclusao = sped_exclusao

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        self.ensure_one()

        # Validação
        validacao = ""

        # Cria o registro
        S1000 = pysped.esocial.leiaute.S1000_2()

        # Popula ideEvento
        S1000.tpInsc = '1'
        S1000.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        S1000.evento.ideEvento.tpAmb.valor = int(ambiente)
        S1000.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
        S1000.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S1000.evento.ideEmpregador.tpInsc.valor = '1'
        S1000.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        # Popula a operação que será realizada com esse registro
        S1000.evento.infoEmpregador.operacao = operacao

        # Popula infoEmpregador.idePeriodo
        S1000.evento.infoEmpregador.idePeriodo.iniValid.valor = \
            self.company_id.esocial_periodo_inicial_id.code[3:7] + '-' + \
            self.company_id.esocial_periodo_inicial_id.code[0:2]

        # Se for operacao=='A' (Alteração) Popula idePeriodo usando company_id.periodo_atualizacao_id
        if operacao == 'A':

            # Se o campo periodo_atualizacao_id não estiver preenchido, retorne erro de dados para o usuário
            if not self.company_id.esocial_periodo_atualizacao_id:
                validacao += "O campo 'Período da Última Atualização' na Empresa não está preenchido !\n"
            else:
                # Popula infoEmpregador.novaValidade
                S1000.evento.infoEmpregador.novaValidade.iniValid.valor = \
                    self.company_id.esocial_periodo_atualizacao_id.code[3:7] + '-' + \
                    self.company_id.esocial_periodo_atualizacao_id.code[0:2]

        # Se for operacao=='E' (Exclusão) Popula idePeriodo usando
        if operacao == 'E':

            # Se o campo periodo_exclusao_id não estiver preenchido, retorne erro de dados para o usuário
            if not self.company_id.esocial_periodo_final_id:
                validacao += "O campo 'Período Final' na Empresa não está preenchido !\n"
            else:
                # Popula infoEmpregador.idePeriodo.fimValid
                S1000.evento.infoEmpregador.idePeriodo.fimValid.valor = \
                    self.company_id.esocial_periodo_final_id.code[3:7] + '-' + \
                    self.company_id.esocial_periodo_final_id.code[0:2]

        # Popula infoEmpregador.InfoCadastro
        S1000.evento.infoEmpregador.infoCadastro.nmRazao.valor = self.company_id.legal_name
        S1000.evento.infoEmpregador.infoCadastro.classTrib.valor = self.company_id.classificacao_tributaria_id.codigo
        S1000.evento.infoEmpregador.infoCadastro.natJurid.valor = limpa_formatacao(
            self.company_id.natureza_juridica_id.codigo)
        S1000.evento.infoEmpregador.infoCadastro.indCoop.valor = self.company_id.ind_coop
        S1000.evento.infoEmpregador.infoCadastro.indConstr.valor = self.company_id.ind_constr
        S1000.evento.infoEmpregador.infoCadastro.indDesFolha.valor = self.company_id.ind_desoneracao
        S1000.evento.infoEmpregador.infoCadastro.indOptRegEletron.valor = self.company_id.ind_opt_reg_eletron
        S1000.evento.infoEmpregador.infoCadastro.indEntEd.valor = self.company_id.ind_ent_ed
        S1000.evento.infoEmpregador.infoCadastro.indEtt.valor = self.company_id.ind_ett
        if self.company_id.nr_reg_ett:
            S1000.evento.infoEmpregador.infoCadastro.nrRegEtt.valor = self.company_id.nr_reg_ett
        if self.limpar_db:
            S1000.evento.infoEmpregador.infoCadastro.nmRazao.valor = 'RemoverEmpregadorDaBaseDeDadosDaProducaoRestrita'
            S1000.evento.infoEmpregador.infoCadastro.classTrib.valor = '00'

        # Popula infoEmpregador.Infocadastro.contato
        S1000.evento.infoEmpregador.infoCadastro.contato.nmCtt.valor = self.company_id.esocial_nm_ctt
        S1000.evento.infoEmpregador.infoCadastro.contato.cpfCtt.valor = self.company_id.esocial_cpf_ctt
        S1000.evento.infoEmpregador.infoCadastro.contato.foneFixo.valor = limpa_formatacao(
            self.company_id.esocial_fone_fixo)
        if self.company_id.esocial_fone_cel:
            S1000.evento.infoEmpregador.infoCadastro.contato.foneCel.valor = limpa_formatacao(
                self.company_id.esocial_fone_cel)
        if self.company_id.esocial_email:
            S1000.evento.infoEmpregador.infoCadastro.contato.email.valor = self.company_id.esocial_email

        # Popula infoEmpregador.infoCadastro.infoComplementares.situacaoPJ
        S1000.evento.infoEmpregador.infoCadastro.indSitPJ.valor = self.company_id.ind_sitpj

        return S1000, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        self.company_id.precisa_atualizar = False

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
