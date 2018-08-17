# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor

from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario


class SpedAlteracaoContrato(models.Model, SpedRegistroIntermediario):
    _name = "sped.esocial.alteracao.contrato"
    _rec_name = "name"
    _order = "company_id"

    name = fields.Char(
        string='name',
        compute='_compute_display_name',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    hr_contract_change_id = fields.Many2one(
        string='Alteração Contratual',
        comodel_name='l10n_br_hr.contract.change',
        required=True,
    )
    hr_contract_id = fields.Many2one(
        string='Contrato de Trabalho',
        comodel_name='hr.contract',
        related='hr_contract_change_id.contract_id',
    )
    sped_alteracao = fields.Many2one(
        string='Alterações',
        comodel_name='sped.registro',
    )
    sped_retificacao_ids = fields.Many2many(
        string='Retificações',
        comodel_name='sped.registro',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('1', 'Precisa Atualizar'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        string='Situação no e-Social',
        compute='compute_situacao_esocial',
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa atualizar dados?',
        related='hr_contract_change_id.precisa_atualizar',
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_situacao_esocial',
    )

    @api.depends('hr_contract_id')
    def _compute_display_name(self):
        for record in self:
            record.name = 'S-2206 - Alteração Contratual {}'.format(
                record.hr_contract_id.display_name or '')

    @api.depends('sped_alteracao', 'sped_retificacao_ids')
    def compute_situacao_esocial(self):
        for s2206 in self:
            situacao_esocial = '1'
            ultima_atualizacao = False

            # Usa o status do registro de inclusão
            if s2206.sped_alteracao:
                situacao_esocial = s2206.sped_alteracao.situacao
                ultima_atualizacao = s2206.sped_alteracao.data_hora_origem

            for retificacao in s2206.sped_retificacao_ids:
                if not ultima_atualizacao or retificacao.data_hora_origem > ultima_atualizacao:
                    ultima_atualizacao = retificacao.data_hora_origem
                    situacao_esocial = retificacao.situacao

            # Popula na tabela
            s2206.situacao_esocial = situacao_esocial
            s2206.ultima_atualizacao = ultima_atualizacao

    # @api.multi
    # @api.depends('sped_alteracao')
    # def compute_precisa_enviar(self):
    #
    #     # Roda todos os registros da lista
    #     for contrato in self:
    #
    #         # Inicia as variáveis como False
    #         precisa_atualizar = False
    #
    #         # Se a situação for '3' (Aguardando Transmissão) fica tudo falso
    #         if contrato.situacao_esocial != '3':
    #
    #             # Se a empresa já tem um registro de inclusão confirmado mas
    #             # a data da última atualização é menor que a o write_date da
    #             # empresa, então precisa atualizar
    #             if not contrato.precisa_atualizar or contrato.ultima_atualizacao \
    #                     < contrato.hr_contract_id.write_date:
    #                 precisa_atualizar = True
    #
    #         # Popula os campos na tabela
    #         contrato.precisa_atualizar = precisa_atualizar

    # @api.depends('sped_alteracao')
    # def compute_ultima_atualizacao(self):
    #
    #     # Roda todos os registros da lista
    #     for contrato in self:
    #
    #         # Inicia a última atualização com a data/hora now()
    #         ultima_atualizacao = fields.Datetime.now()
    #
    #         # Se tiver alterações pega a data/hora de origem da última alteração
    #         for alteracao in contrato.sped_alteracao:
    #             if alteracao.situacao == '4':
    #                 if alteracao.data_hora_origem > ultima_atualizacao:
    #                     ultima_atualizacao = alteracao.data_hora_origem
    #
    #         # Popula o campo na tabela
    #         contrato.ultima_atualizacao = ultima_atualizacao

    # Roda a atualização do e-Social (não transmite ainda)
    @api.multi
    def gerar_registro(self):
        self.ensure_one()

        # Criar o registro S-2206 de alteração, se for necessário
        values = {
            'tipo': 'esocial',
            'registro': 'S-2206',
            'ambiente': self.company_id.esocial_tpAmb,
            'company_id': self.company_id.id,
            'evento': 'evtAltContratual',
            'origem': ('hr.contract,%s' % self.hr_contract_id.id),
            'origem_intermediario': (
                    'sped.esocial.alteracao.contrato,%s' % self.id),
        }
        if not self.sped_alteracao:
            sped_alteracao = self.env['sped.registro'].create(values)
            self.sped_alteracao = sped_alteracao
        elif self.precisa_atualizar:
            # Cria o registro de Retificação
            values['operacao'] = 'R'
            sped_retificacao = self.env['sped.registro'].create(values)
            self.sped_retificacao_ids = [(4, sped_retificacao.id)]

    @api.multi
    def popula_xml(self, ambiente='2', operacao='na'):
        """
        Função para popular o xml com os dados referente a alteração de
        dados contratuais
        """

        # Validação
        validacao = ""

        # Cria o registro
        S2206 = pysped.esocial.leiaute.S2206_2()
        contrato_id = self.hr_contract_id

        # Popula ideEvento
        S2206.tpInsc = '1'
        S2206.nrInsc = limpa_formatacao(
            contrato_id.company_id.cnpj_cpf
        )[0:8]
        S2206.evento.ideEvento.indRetif.valor = '1'
        if operacao == 'R':  # Retificação
            S2206.evento.ideEvento.indRetif.valor = '2'
            S2206.evento.ideEvento.nrRecibo.valor = self.sped_alteracao.recibo
        S2206.evento.ideEvento.tpAmb.valor = int(
            contrato_id.company_id.esocial_tpAmb
        )
        S2206.evento.ideEvento.procEmi.valor = '1'
        S2206.evento.ideEvento.verProc.valor = '8.0'

        # Popula ideEmpregador (Dados do Empregador)
        S2206.evento.ideEmpregador.tpInsc.valor = '1'
        S2206.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            contrato_id.company_id.cnpj_cpf)[0:8]

        # Popula ideVinculo (Identificador do Trabalhador e do Vínculo)
        S2206.evento.ideVinculo.cpfTrab.valor = limpa_formatacao(
            contrato_id.employee_id.cpf)
        S2206.evento.ideVinculo.nisTrab.valor = limpa_formatacao(
            contrato_id.employee_id.pis_pasep)
        S2206.evento.ideVinculo.matricula.valor = contrato_id.matricula

        # Popula altContratual (Informações do Contrato de Trabalho)
        S2206.evento.altContratual.dtAlteracao.valor = fields.Datetime.now()

        alteracao_contratual = S2206.evento.altContratual

        # Popula vinculo (Informações do vínculo trabalhista)
        vinculo = pysped.esocial.leiaute.S2206_Vinculo_2()
        vinculo.tpRegPrev.valor = contrato_id.tp_reg_prev
        alteracao_contratual.vinculo.append(vinculo)

        # Popula infoRegimeTrab (Informações do regime trabalhista)
        info_celetista = pysped.esocial.leiaute.S2206_InfoCeletista_2()

        info_celetista.tpRegJor.valor = contrato_id.tp_reg_jor
        info_celetista.natAtividade.valor = contrato_id.nat_atividade
        info_celetista.cnpjSindCategProf.valor = limpa_formatacao(
            contrato_id.partner_union.cnpj_cpf)

        info_regime_trab = pysped.esocial.leiaute.S2206_InfoRegimeTrab_2()
        info_regime_trab.infoCeletista.append(info_celetista)

        alteracao_contratual.infoRegimeTrab.append(info_regime_trab)

        # Popula infoContrato (Informações do Contrato de Trabalho)
        info_contrato = alteracao_contratual.infoContrato
        info_contrato.codCargo.valor = contrato_id.job_id.codigo

        info_contrato.codCateg.valor = contrato_id.categoria

        # Popula remuneracao (Informações da remuneração e
        #  e pagamento)
        info_contrato.remuneracao.vrSalFx.valor = formata_valor(
            contrato_id.wage)
        info_contrato.remuneracao.undSalFixo.valor = \
            contrato_id.salary_unit.code

        # Popula duração (Duração do Contrato de Trabalho)
        info_contrato.duracao.tpContr.valor = contrato_id.tp_contr
        if contrato_id.tp_contr == '2':
            info_contrato.duracao.dtTerm.valor = contrato_id.date_end

        # Popula localTrabalho (Informações do local de Trabalho)
        local_trabalho = pysped.esocial.leiaute.S2206_LocalTrabGeral_2()
        local_trabalho.tpInsc.valor = '1'
        local_trabalho.nrInsc.valor = limpa_formatacao(
            contrato_id.company_id.cnpj_cpf
        )

        info_contrato.localTrabalho.localTrabGeral.append(local_trabalho)

        # Popula horContratual (Informações do Horario
        # Contratual do Trabalhador)
        horario_contratual = pysped.esocial.leiaute.S2206_HorContratual_2()
        horario_contratual.qtdHrsSem.valor = int(contrato_id.weekly_hours)
        horario_contratual.tpJornada.valor = contrato_id.tp_jornada
        horario_contratual.tmpParc.valor = contrato_id.tmp_parc

        for horario in contrato_id.working_hours.attendance_ids:
            horario_dia_semana = pysped.esocial.leiaute.S2206_Horario_2()
            horario_dia_semana.dia.valor = horario.diadasemana
            horario_dia_semana.codHorContrat.valor = \
                horario.turno_id.cod_hor_contrat

            horario_contratual.horario.append(horario_dia_semana)

        info_contrato.horContratual.append(horario_contratual)

        if contrato_id.partner_union:
            filiacao_sindical = \
                pysped.esocial.leiaute.S2206_FiliacaoSindical_2()
            filiacao_sindical.cnpjSindTrab.valor = limpa_formatacao(
                contrato_id.partner_union.cnpj_cpf)

            info_contrato.filiacaoSindical.append(filiacao_sindical)

        return S2206, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        # Executa método original do contract_change para aplicar a mudança
        self.hr_contract_change_id.apply_contract_changes()

    @api.multi
    def retorna_trabalhador(self):
        self.ensure_one()
        return self.hr_contract_id.employee_id

    @api.multi
    def transmitir(self):
        self.ensure_one()

        if self.situacao_esocial in ['1', '3']:
            # Identifica qual registro precisa transmitir
            registro = False
            if self.sped_alteracao.situacao in ['1', '3']:
                registro = self.sped_alteracao
            else:
                for r in self.sped_retificacao_ids:
                    if r.situacao in ['1', '3']:
                        registro = r

            # Com o registro identificado, é só rodar o método
            # transmitir_lote() do registro
            if registro:
                registro.transmitir_lote()

    @api.multi
    def consultar(self):
        self.ensure_one()

        if self.situacao_esocial in ['2']:
            # Identifica qual registro precisa consultar
            registro = False
            if self.sped_alteracao.situacao == '2':
                registro = self.sped_alteracao
            else:
                for r in self.sped_retificacao_ids:
                    if r.situacao == '2':
                        registro = r

            # Com o registro identificado, é só rodar o método consulta_lote() do registro
            if registro:
                registro.consulta_lote()
