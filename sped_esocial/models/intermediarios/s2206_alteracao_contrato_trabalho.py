# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor

from .sped_registro_intermediario import SpedRegistroIntermediario


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
    hr_contract_id = fields.Many2one(
        string='Contrato de Trabalho',
        comodel_name='hr.contract',
        required=True,
    )
    sped_alteracao = fields.Many2many(
        string='Alterações',
        comodel_name='sped.registro',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('1', 'Precisa Atualizar'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
        ],
        string='Situação no e-Social',
        compute='compute_situacao_esocial',
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa atualizar dados?',
        compute='compute_precisa_enviar',
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
    )

    @api.depends('hr_contract_id')
    def _compute_display_name(self):
        for record in self:
            record.name = 'S-2206 - Alteração Contratual {}'.format(
                record.hr_contract_id.display_name or '')

    @api.depends('sped_alteracao')
    def compute_situacao_esocial(self):
        for contrato in self:
            situacao_esocial = '1'

            for alteracao in contrato.sped_alteracao:
                situacao_esocial = alteracao.situacao

            # Popula na tabela
            contrato.situacao_esocial = situacao_esocial

    @api.depends('sped_alteracao')
    def compute_precisa_enviar(self):

        # Roda todos os registros da lista
        for contrato in self:

            # Inicia as variáveis como False
            precisa_atualizar = False

            # Se a situação for '3' (Aguardando Transmissão) fica tudo falso
            if contrato.situacao_esocial != '3':

                # Se a empresa já tem um registro de inclusão confirmado mas
                # a data da última atualização é menor que a o write_date da
                # empresa, então precisa atualizar
                if not contrato.precisa_atualizar or contrato.ultima_atualizacao \
                        < contrato.hr_contract_id.write_date:
                    precisa_atualizar = True

            # Popula os campos na tabela
            contrato.precisa_atualizar = precisa_atualizar

    @api.depends('sped_alteracao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for contrato in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver alterações pega a data/hora de origem da última alteração
            for alteracao in contrato.sped_alteracao:
                if alteracao.situacao == '4':
                    if alteracao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = alteracao.data_hora_origem

            # Popula o campo na tabela
            contrato.ultima_atualizacao = ultima_atualizacao

    # Roda a atualização do e-Social (não transmite ainda)
    @api.multi
    def gerar_registro(self):
        self.ensure_one()

        # Criar o registro S-2206 de alteração, se for necessário
        if self.precisa_atualizar:
            values = {
                'tipo': 'esocial',
                'registro': 'S-2206',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'operacao': 'A',
                'evento': 'evtAltContratual',
                'origem': ('hr.contract,%s' % self.hr_contract_id.id),
                'origem_intermediario': (
                        'sped.esocial.alteracao.contrato,%s' % self.id),
            }

            sped_alteracao = self.env['sped.registro'].create(values)
            self.sped_alteracao = [(4, sped_alteracao.id)]

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        """
        Função para popular o xml com os dados referente a alteração de
        dados contratuais
        """
        # Cria o registro
        S2206 = pysped.esocial.leiaute.S2206_2()
        contrato_id = self.hr_contract_id

        # Popula ideEvento
        S2206.tpInsc = '1'
        S2206.nrInsc = limpa_formatacao(
            contrato_id.company_id.cnpj_cpf
        )[0:8]
        S2206.evento.ideEvento.indRetif.valor = '1'
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

        return S2206

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()
