# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import \
    SpedRegistroIntermediario
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor


class SpedReinfContribuinte(models.Model, SpedRegistroIntermediario):
    _name = 'sped.efdreinf.contribuinte'
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
    situacao = fields.Selection(
        selection=[
            ('0', 'Inativa'),
            ('1', 'Ativa'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('9', 'Finalizada'),
        ],
        string='Situação no e-Social',
        compute='compute_situacao',
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

    # Controle de limpeza do database (para uso em Produção Restrita somente)
    limpar_db = fields.Boolean(
        string='Limpar DB',
    )

    @api.depends('company_id')
    def _compute_name(self):
        for registro in self:
            nome = 'Contribuinte'
            if registro.company_id:
                nome += ' ('
                nome += registro.company_id.display_name or ''
                nome += ')'
            registro.nome = nome

    @api.depends('sped_inclusao', 'sped_exclusao')
    def compute_situacao(self):
        for contribuinte in self:
            situacao = '0'  # Inativa

            # Se a empresa possui um registro de inclusão confirmado e não precisa atualizar nem excluir
            # então ela está Ativa
            if contribuinte.sped_inclusao and contribuinte.sped_inclusao.situacao == '4':
                if not contribuinte.precisa_atualizar and not contribuinte.precisa_excluir:
                    situacao = '1'
                else:
                    situacao = '2'

                # Se já possui um registro de exclusão confirmado, então
                # é situação é Finalizada
                if contribuinte.sped_exclusao and contribuinte.sped_exclusao.situacao == '4':
                    situacao = '9'

            # Se a empresa possui algum registro que esteja em fase de transmissão
            # então a situação é Aguardando Transmissão
            if contribuinte.sped_inclusao and contribuinte.sped_inclusao.situacao != '4':
                situacao = '3'
            if contribuinte.sped_exclusao and contribuinte.sped_exclusao.situacao != '4':
                situacao = '3'
            for alteracao in contribuinte.sped_alteracao:
                if alteracao.situacao != '4':
                    situacao = '3'

            # Popula na tabela
            contribuinte.situacao = situacao

    @api.depends('sped_inclusao', 'sped_alteracao', 'sped_alteracao.situacao',
                 'sped_exclusao')
    def compute_precisa_enviar(self):

        # Roda todos os registros da lista
        for contribuinte in self:

            # Inicia as variáveis como False
            precisa_incluir = False
            precisa_atualizar = False
            precisa_excluir = False

            # Se a situação for '3' (Aguardando Transmissão) fica tudo falso
            if self.situacao != '3':

                # Se a empresa matriz tem um período inicial definido e não tem um registro S1000 de inclusão
                # confirmado, então precisa incluir
                if contribuinte.company_id.esocial_periodo_inicial_id:
                    if not contribuinte.sped_inclusao or contribuinte.sped_inclusao.situacao != '4':
                        precisa_incluir = True

                # Se a empresa já tem um registro de inclusão confirmado mas a data da última atualização
                # é menor que a o write_date da empresa, então precisa atualizar
                if contribuinte.sped_inclusao and contribuinte.sped_inclusao.situacao == '4':
                    if contribuinte.ultima_atualizacao < contribuinte.company_id.write_date:
                        precisa_atualizar = True

                # Se a empresa já tem um registro de inclusão confirmado, tem um período final definido e
                # não tem um registro de exclusão confirmado, então precisa excluir
                if contribuinte.sped_inclusao and contribuinte.sped_inclusao.situacao == '4':
                    if contribuinte.company_id.esocial_periodo_final_id:
                        if not contribuinte.sped_exclusao or contribuinte.sped_exclusao != '4':
                            precisa_excluir = True

            # Popula os campos na tabela
            contribuinte.precisa_incluir = precisa_incluir
            contribuinte.precisa_atualizar = precisa_atualizar
            contribuinte.precisa_excluir = precisa_excluir

    @api.depends('sped_inclusao', 'sped_alteracao', 'sped_alteracao.situacao',
                 'sped_exclusao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for contribuinte in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if contribuinte.sped_inclusao and contribuinte.sped_inclusao.situacao == '4':
                ultima_atualizacao = contribuinte.sped_inclusao.data_hora_origem

            # Se tiver alterações, pega a data/hora de origem da última alteração
            for alteracao in contribuinte.sped_alteracao:
                if alteracao.situacao == '4':
                    if alteracao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = alteracao.data_hora_origem

            # Se tiver exclusão, pega a data/hora de origem da exclusão
            if contribuinte.sped_exclusao and contribuinte.sped_exclusao.situacao == '4':
                ultima_atualizacao = contribuinte.sped_exclusao.data_hora_origem

            # Popula o campo na tabela
                contribuinte.ultima_atualizacao = ultima_atualizacao

    # Roda a atualização do e-Social (não transmite ainda)
    @api.multi
    def atualizar_reinf(self):
        values = {
            'tipo': 'efdreinf',
            'registro': 'R-1000',
            'ambiente': self.company_id.tpAmb,
            'company_id': self.company_id.id,
            'evento': 'evtInfoContri',
            'origem': ('res.company,%s' % self.company_id.id),
            'origem_intermediario': ('sped.efdreinf.contribuinte,%s' % self.id),
        }

        # Criar o registro R-1000 de inclusão, se for necessário
        if self.precisa_incluir:
            values['operacao'] = 'I'
            sped_inclusao = self.env['sped.registro'].create(values)
            self.sped_inclusao = sped_inclusao

        # Criar o registro R-1000 de alteração, se for necessário
        if self.precisa_atualizar:
            values['operacao'] = 'A'
            sped_alteracao = self.env['sped.registro'].create(values)
            self.sped_alteracao = [(4, sped_alteracao.id)]

        # Criar o registro R-1000 de exclusão, se for necessário
        if self.precisa_excluir:
            values['operacao'] = 'E'
            sped_exclusao = self.env['sped.registro'].create(values)
            self.sped_exclusao = sped_exclusao

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):

        # Validação
        validacao = ""

        # Cria o registro
        R1000 = pysped.efdreinf.leiaute.R1000_1()

        # Popula ideEvento
        R1000.evento.ideEvento.tpAmb.valor = ambiente
        # Processo de Emissão = Aplicativo do Contribuinte
        R1000.evento.ideEvento.procEmi.valor = '1'
        R1000.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0
        if self.limpar_db:
            R1000.evento.ideEvento.verProc.valor = 'RemoverContribuinte'

        # Popula ideContri (Dados do Contribuinte)
        R1000.evento.ideContri.tpInsc.valor = '1'
        if self.company_id.eh_empresa_base:
            matriz = self.company_id
        else:
            matriz = self.company_id.matriz
        R1000.evento.ideContri.nrInsc.valor = limpa_formatacao(
            matriz.cnpj_cpf)[0:8]

        # Popula infoContri
        if operacao == 'I':
            R1000.evento.infoContri.operacao = 'I'
            R1000.evento.infoContri.idePeriodo.iniValid.valor = \
                self.company_id.reinf_periodo_inicial_id.code[3:7] + '-' + \
                self.company_id.reinf_periodo_inicial_id.code[0:2]

        # Popula infoContri.InfoCadastro
        R1000.evento.infoContri.infoCadastro.classTrib.valor = self.company_id.classificacao_tributaria_id.codigo
        if self.limpar_db:
            R1000.evento.infoContri.infoCadastro.classTrib.valor = '00'

        R1000.evento.infoContri.infoCadastro.indEscrituracao.valor = self.company_id.ind_escrituracao
        R1000.evento.infoContri.infoCadastro.indDesoneracao.valor = self.company_id.ind_desoneracao
        R1000.evento.infoContri.infoCadastro.indAcordoIsenMulta.valor = self.company_id.ind_acordoisenmulta
        R1000.evento.infoContri.infoCadastro.indSitPJ.valor = self.company_id.ind_sitpj
        R1000.evento.infoContri.infoCadastro.contato.nmCtt.valor = self.company_id.nmctt
        R1000.evento.infoContri.infoCadastro.contato.cpfCtt.valor = self.company_id.cpfctt
        R1000.evento.infoContri.infoCadastro.contato.foneFixo.valor = self.company_id.cttfonefixo
        if self.company_id.cttfonecel:
            R1000.evento.infoContri.infoCadastro.contato.foneCel.valor = self.company_id.cttfonecel
        if self.company_id.cttemail:
            R1000.evento.infoContri.infoCadastro.contato.email.valor = self.company_id.cttemail

        return R1000, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()
