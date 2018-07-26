# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from pybrasil.valor import formata_valor
from openerp import api, models, fields
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
import pysped

from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario


class SpedEsocialHrContrato(models.Model, SpedRegistroIntermediario):
    _name = "sped.esocial.contrato"
    _rec_name = 'name'

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
        string="Contrato de Trabalho",
        comodel_name="hr.contract",
        required=True,
    )
    sped_s2200_registro_inclusao = fields.Many2one(
        string='Registro S-2200',
        comodel_name='sped.registro',
    )
    sped_s2200_registro_retificacao = fields.Many2many(
        string='Registro S-2200 - Retificação',
        comodel_name='sped.registro',
    )
    situacao_esocial = fields.Selection(
        string='Situação no e-Social',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        compute="compute_situacao_esocial",
        readonly=True,
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
    )

    @api.depends('sped_s2200_registro_inclusao',
                 'sped_s2200_registro_retificacao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for desligamento in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if desligamento.sped_s2200_registro_inclusao and \
                    desligamento.sped_s2200_registro_inclusao.situacao == '4':
                ultima_atualizacao = \
                    desligamento.sped_s2200_registro_inclusao.data_hora_origem

            # Se tiver alterações, pega a data/hora de origem da última alteração
            for retificacao in desligamento.sped_s2200_registro_retificacao:
                if retificacao.situacao == '4':
                    if retificacao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = retificacao.data_hora_origem

            # Popula o campo na tabela
            desligamento.ultima_atualizacao = ultima_atualizacao

    @api.multi
    def gerar_registro(self):
        if not self.sped_s2200_registro_inclusao:
            values = {
                'tipo': 'esocial',
                'registro': 'S-2200',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'evento': 'evtAdmissao',
                'origem': (
                        'hr.contract,%s' %
                        self.hr_contract_id.id),
                'origem_intermediario': (
                        'sped.esocial.contrato,%s' % self.id),
            }

            sped_inclusao = self.env['sped.registro'].create(values)
            self.sped_s2200_registro_inclusao = sped_inclusao

    @api.depends('sped_s2200_registro_inclusao',
                 'sped_s2200_registro_retificacao')
    def compute_situacao_esocial(self):
        for desligamento in self:
            situacao_esocial = '1'

            if desligamento.sped_s2200_registro_inclusao:
                situacao_esocial = \
                    desligamento.sped_s2200_registro_inclusao.situacao

            for retificao in desligamento.sped_s2200_registro_retificacao:
                situacao_esocial = retificao.situacao

            # Popula na tabela
            desligamento.situacao_esocial = situacao_esocial

    @api.depends('hr_contract_id')
    def _compute_display_name(self):
        for record in self:
            record.name = 'S-2200 - Admissão {}'.format(record.hr_contract_id.display_name or '')

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        """
        Função para popular o xml com os dados referente ao desligamento de
        um contrato de trabalho
        :return:
        """
        # Cria o registro
        S2200 = pysped.esocial.leiaute.S2200_2()

        # Popula ideEvento
        S2200.tpInsc = '1'
        S2200.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        S2200.evento.ideEvento.tpAmb.valor = int(ambiente)
        S2200.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
        S2200.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S2200.evento.ideEmpregador.tpInsc.valor = '1'
        S2200.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        # Popula "trabalhador" (Dados do Trabalhador)
        S2200.evento.trabalhador.cpfTrab.valor = limpa_formatacao(
            self.hr_contract_id.employee_id.cpf)
        S2200.evento.trabalhador.nisTrab.valor = limpa_formatacao(
            self.hr_contract_id.employee_id.pis_pasep)
        S2200.evento.trabalhador.nmTrab.valor = self.hr_contract_id.employee_id.name
        sexo = ''
        if self.hr_contract_id.employee_id.gender == 'male':
            sexo = 'M'
        elif self.hr_contract_id.employee_id.gender == 'female':
            sexo = 'F'
        S2200.evento.trabalhador.sexo.valor = sexo
        S2200.evento.trabalhador.racaCor.valor = self.hr_contract_id.employee_id.ethnicity.code or ''

        if self.hr_contract_id.employee_id.marital:
            if self.hr_contract_id.employee_id.marital == 'single':
                estado_civil = '1'
            elif self.hr_contract_id.employee_id.marital in ['married', 'common_law_marriage']:
                estado_civil = '2'
            elif self.hr_contract_id.employee_id.marital == 'divorced':
                estado_civil = '3'
            elif self.hr_contract_id.employee_id.marital == 'separated':
                estado_civil = '4'
            elif self.hr_contract_id.employee_id.marital == 'widower':
                estado_civil = '5'
            S2200.evento.trabalhador.estCiv.valor = estado_civil

        S2200.evento.trabalhador.grauInstr.valor = \
            self.hr_contract_id.employee_id.educational_attainment.code.zfill(2) or ''
        S2200.evento.trabalhador.indPriEmpr.valor = 'S' if self.hr_contract_id.primeiro_emprego else 'N'
        # S2200.evento.trabalhador.nmSoc =  # TODO separar Nome Legal de Nome Social no Odoo

        # Popula trabalhador.nascimento
        S2200.evento.trabalhador.nascimento.dtNascto.valor = self.hr_contract_id.employee_id.birthday
        if self.hr_contract_id.employee_id.naturalidade:
            S2200.evento.trabalhador.nascimento.codMunic.valor = \
                self.hr_contract_id.employee_id.naturalidade.state_id.ibge_code + \
                self.hr_contract_id.employee_id.naturalidade.ibge_code
            S2200.evento.trabalhador.nascimento.uf.valor = self.hr_contract_id.employee_id.naturalidade.state_id.code
        S2200.evento.trabalhador.nascimento.paisNascto.valor = self.hr_contract_id.employee_id.pais_nascto_id.codigo
        S2200.evento.trabalhador.nascimento.paisNac.valor = self.hr_contract_id.employee_id.pais_nac_id.codigo
        S2200.evento.trabalhador.nascimento.nmMae.valor = self.hr_contract_id.employee_id.mother_name or ''
        S2200.evento.trabalhador.nascimento.nmPai.valor = self.hr_contract_id.employee_id.father_name or ''

        # Popula trabalhador.documentos
        # CTPS
        if self.hr_contract_id.employee_id.ctps:
            CTPS = pysped.esocial.leiaute.S2200_CTPS_2()  # Cria o registro

        # Popula ideEvento
        S2200.tpInsc = '1'
        S2200.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        S2200.evento.ideEvento.tpAmb.valor = int(ambiente)
        S2200.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
        S2200.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S2200.evento.ideEmpregador.tpInsc.valor = '1'
        S2200.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        # Popula "trabalhador" (Dados do Trabalhador)
        S2200.evento.trabalhador.cpfTrab.valor = limpa_formatacao(
            self.hr_contract_id.employee_id.cpf)
        S2200.evento.trabalhador.nisTrab.valor = limpa_formatacao(
            self.hr_contract_id.employee_id.pis_pasep)
        S2200.evento.trabalhador.nmTrab.valor = self.hr_contract_id.employee_id.name
        sexo = ''
        if self.hr_contract_id.employee_id.gender == 'male':
            sexo = 'M'
        elif self.hr_contract_id.employee_id.gender == 'female':
            sexo = 'F'
        S2200.evento.trabalhador.sexo.valor = sexo
        S2200.evento.trabalhador.racaCor.valor = self.hr_contract_id.employee_id.ethnicity.code or ''
        estado_civil = ''
        if self.hr_contract_id.employee_id.marital == 'single':
            estado_civil = '1'
        elif self.hr_contract_id.employee_id.marital in ['married',
                                                 'common_law_marriage']:
            estado_civil = '2'
        elif self.hr_contract_id.employee_id.marital == 'divorced':
            estado_civil = '3'
        elif self.hr_contract_id.employee_id.marital == 'separated':
            estado_civil = '4'
        elif self.hr_contract_id.employee_id.marital == 'widower':
            estado_civil = '5'
        S2200.evento.trabalhador.estCiv.valor = estado_civil
        S2200.evento.trabalhador.grauInstr.valor = \
            self.hr_contract_id.employee_id.educational_attainment.code.zfill(2) or ''
        S2200.evento.trabalhador.indPriEmpr.valor = 'S' if self.hr_contract_id.primeiro_emprego else 'N'
        # S2200.evento.trabalhador.nmSoc =  # TODO separa
        CTPS.nrCtps.valor = self.hr_contract_id.employee_id.ctps or ''
        CTPS.serieCtps.valor = self.hr_contract_id.employee_id.ctps_series or ''
        CTPS.ufCtps.valor = self.hr_contract_id.employee_id.ctps_uf_id.code or ''
        S2200.evento.trabalhador.documentos.CTPS.append(CTPS)

        # # RIC  # TODO (Criar campos em l10n_br_hr)
        # if self.hr_contract_id.employee_id.ric:
        #     RIC = pysped.esocial.leiaute.S2200_RIC_2()
        #     RIC.nrRic.valor = self.hr_contract_id.employee_id.ric
        #     RIC.orgaoEmissor.valor = self.hr_contract_id.employee_id.ric_orgao_emissor
        #     if self.hr_contract_id.employee_id.ric_dt_exped:
        #         RIC.dtExped.valor = self.hr_contract_id.employee_id.ric_dt_exped
        #     S2200.evento.trabalhador.documentos.RG.append(RIC)

        # RG
        if self.hr_contract_id.employee_id.rg:
            RG = pysped.esocial.leiaute.S2200_RG_2()
            RG.nrRg.valor = self.hr_contract_id.employee_id.rg or ''
            RG.orgaoEmissor.valor = self.hr_contract_id.employee_id.organ_exp or ''
            if self.hr_contract_id.employee_id.rg_emission:
                RG.dtExped.valor = self.hr_contract_id.employee_id.rg_emission
            S2200.evento.trabalhador.documentos.RG.append(RG)

        # # RNE  # TODO (Criar campos em l10n_br_hr)
        # if self.hr_contract_id.employee_id.rne:
        #     RNE = pysped.esocial.leiaute.S2200_RNE_2()
        #     RNE.nrRne.valor = self.hr_contract_id.employee_id.rne
        #     RNE.orgaoEmissor.valor = self.hr_contract_id.employee_id.rne_orgao_emissor
        #     if self.hr_contract_id.employee_id.rne_dt_exped:
        #         RNE.dtExped.valor = self.hr_contract_id.employee_id.rne_dt_exped
        #     S2200.evento.trabalhador.documentos.RNE.append(RNE)

        # # OC  # TODO (Criar campos em l10n_br_hr)
        # if self.hr_contract_id.employee_id.oc:
        #     OC = pysped.esocial.leiaute.S2200_OC_2()
        #     OC.nrOc.valor = self.hr_contract_id.employee_id.oc
        #     OC.orgaoEmissor.valor = self.hr_contract_id.employee_id.oc_orgao_emissor
        #     if self.hr_contract_id.employee_id.oc_dt_exped:
        #         OC.dtExped.valor = self.hr_contract_id.employee_id.oc_dt_exped
        #     if self.hr_contract_id.employee_id.oc_dt_valid:
        #         OC.dtValid.valor = self.hr_contract_id.employee_id.oc_dt_valid
        #     S2200.evento.trabalhador.documentos.OC.append(OC)

        # CNH
        if self.hr_contract_id.employee_id.driver_license:
            CNH = pysped.esocial.leiaute.S2200_CNH_2()
            CNH.nrRegCnh.valor = self.hr_contract_id.employee_id.driver_license
            if self.hr_contract_id.employee_id.cnh_dt_exped:
                CNH.dtExped.valor = self.hr_contract_id.employee_id.cnh_dt_exped
            CNH.ufCnh.valor = self.hr_contract_id.employee_id.cnh_uf.code
            CNH.dtValid.valor = self.hr_contract_id.employee_id.expiration_date
            if self.hr_contract_id.employee_id.cnh_dt_pri_hab:
                CNH.dtPriHab.valor = self.hr_contract_id.employee_id.cnh_dt_pri_hab
            CNH.categoriaCnh.valor = self.hr_contract_id.employee_id.driver_categ
            S2200.evento.trabalhador.documentos.CNH.append(CNH)

        # Popula trabalhador.endereco.brasil
        Brasil = pysped.esocial.leiaute.S2200_Brasil_2()
        if self.hr_contract_id.employee_id.address_home_id.tp_lograd:
            Brasil.tpLograd.valor = self.hr_contract_id.employee_id.address_home_id.tp_lograd.codigo or ''
        else:
            Brasil.tpLograd.valor = 'R'
        Brasil.dscLograd.valor = self.hr_contract_id.employee_id.address_home_id.street or ''
        Brasil.nrLograd.valor = self.hr_contract_id.employee_id.address_home_id.number or 'S/N'
        Brasil.complemento.valor = self.hr_contract_id.employee_id.address_home_id.street2 or ''
        Brasil.bairro.valor = self.hr_contract_id.employee_id.address_home_id.district or ''
        Brasil.cep.valor = limpa_formatacao(
            self.hr_contract_id.employee_id.address_home_id.zip) or ''
        Brasil.codMunic.valor = \
            self.hr_contract_id.employee_id.address_home_id.l10n_br_city_id.state_id.ibge_code + \
            self.hr_contract_id.employee_id.address_home_id.l10n_br_city_id.ibge_code
        Brasil.uf.valor = self.hr_contract_id.employee_id.address_home_id.state_id.code
        S2200.evento.trabalhador.endereco.brasil.append(Brasil)

        # Popula trabalhador.dependente
        if self.hr_contract_id.employee_id.have_dependent:
            for dependente in self.hr_contract_id.employee_id.dependent_ids:
                Dependente = pysped.esocial.leiaute.S2200_Dependente_2()
                Dependente.tpDep.valor = dependente.dependent_type_id.code.zfill(2)
                Dependente.nmDep.valor = dependente.dependent_name
                Dependente.cpfDep.valor = limpa_formatacao(dependente.dependent_cpf)
                Dependente.dtNascto.valor = dependente.dependent_dob
                Dependente.depIRRF.valor = 'S' if dependente.dependent_verification else 'N'
                Dependente.depSF.valor = 'S' if dependente.dep_sf else 'N'
                Dependente.incTrab.valor = 'S' if dependente.inc_trab else 'N'
                S2200.evento.trabalhador.dependente.append(Dependente)

        # Popula trabalhador.contato
        Contato = pysped.esocial.leiaute.S2200_Contato_2()
        Contato.fonePrinc.valor = limpa_formatacao(
            self.hr_contract_id.employee_id.address_home_id.phone or '')
        Contato.foneAlternat.valor = limpa_formatacao(
            self.hr_contract_id.employee_id.alternate_phone or '')
        Contato.emailPrinc.valor = self.hr_contract_id.employee_id.address_home_id.email or ''
        Contato.emailAlternat.valor = self.hr_contract_id.employee_id.alternate_email or ''
        S2200.evento.trabalhador.contato.append(Contato)

        # Popula "vinculo"
        S2200.evento.vinculo.matricula.valor = self.hr_contract_id.matricula
        S2200.evento.vinculo.tpRegTrab.valor = self.hr_contract_id.labor_regime_id.code
        S2200.evento.vinculo.tpRegPrev.valor = self.hr_contract_id.tp_reg_prev
        S2200.evento.vinculo.cadIni.valor = self.hr_contract_id.cad_ini

        # Popula vinculo.infoRegimeTrab
        if self.hr_contract_id.labor_regime_id.code == '1':

            # Popula infoCeletista
            InfoCeletista = pysped.esocial.leiaute.S2200_InfoCeletista_2()
            data_inicio_contrato = fields.Datetime.from_string(self.hr_contract_id.date_start)
            data_inicio_esocial = fields.Datetime.from_string(self.company_id.esocial_periodo_inicial_id.date_start)
            InfoCeletista.dtAdm.valor = self.hr_contract_id.date_start
            InfoCeletista.tpAdmissao.valor = str(self.hr_contract_id.admission_type_id.code)
            InfoCeletista.indAdmissao.valor = self.hr_contract_id.indicativo_de_admissao
            InfoCeletista.tpRegJor.valor = self.hr_contract_id.tp_reg_jor
            InfoCeletista.natAtividade.valor = self.hr_contract_id.nat_atividade
            InfoCeletista.cnpjSindCategProf.valor = limpa_formatacao(
                self.hr_contract_id.partner_union.cnpj_cpf)
            InfoCeletista.FGTS.opcFGTS.valor = self.hr_contract_id.opc_fgts
            if self.hr_contract_id.dt_opc_fgts:
                InfoCeletista.FGTS.dtOpcFGTS.valor = self.hr_contract_id.dt_opc_fgts
            S2200.evento.vinculo.infoRegimeTrab.infoCeletista.append(InfoCeletista)

        elif self.hr_contract_id.labor_regime_id.code == '2':

            # Popula infoEstatutario  # TODO
            InfoEstatutario = pysped.esocial.leiaute.S2200_InfoEstatutario_2()

        # Popula vinculo.infoContrato
        S2200.evento.vinculo.infoContrato.codCargo.valor = self.hr_contract_id.job_id.codigo
        # S2200.evento.vinculo.infoContrato.codFuncao.valor =   # TODO Quando lidar com Estatutários
        S2200.evento.vinculo.infoContrato.codCateg.valor = self.hr_contract_id.categoria  # TODO Migrar esse campo para
        # relacionar com tabela 1 do eSocial
        # S2200.evento.vinculo.infoContrato.codCarreira.valor =   # TODO Quando lidar com Estatutários
        # S2200.evento.vinculo.infoContrato.dtIngrCarr.valor =   # TODO Quando lidar com Estatutários

        # Popula vinculo.infoContrato.remuneracao
        S2200.evento.vinculo.infoContrato.vrSalFx.valor = formata_valor(
            self.hr_contract_id.wage)
        S2200.evento.vinculo.infoContrato.undSalFixo.valor = self.hr_contract_id.salary_unit.code
        S2200.evento.vinculo.infoContrato.dscSalVar.valor = self.hr_contract_id.dsc_sal_var or ''

        # Popula vinculo.infoContrato.duracao
        S2200.evento.vinculo.infoContrato.tpContr.valor = self.hr_contract_id.tp_contr
        if self.hr_contract_id.tp_contr == '2':
            S2200.evento.vinculo.infoContrato.dtTerm.valor = self.hr_contract_id.date_end
            S2200.evento.vinculo.infoContrato.clauAssec.valor = self.hr_contract_id.clau_assec

        # Popula vinculo.infoContrato.localTrabalho
        LocalTrabGeral = pysped.esocial.leiaute.S2200_LocalTrabGeral_2()
        LocalTrabGeral.tpInsc.valor = '1'
        LocalTrabGeral.nrInsc.valor = limpa_formatacao(
            self.hr_contract_id.company_id.cnpj_cpf)
        # LocalTrabGeral.descComp.valor = ''  # TODO Criar no contrato
        S2200.evento.vinculo.infoContrato.localTrabalho.localTrabGeral.append(
            LocalTrabGeral)

        # Popula vinculo.infoContrato.horContratual (Campos)
        HorContratual = pysped.esocial.leiaute.S2200_HorContratual_2()
        HorContratual.qtdHrsSem.valor = formata_valor(self.hr_contract_id.weekly_hours)
        HorContratual.tpJornada.valor = self.hr_contract_id.tp_jornada
        if self.hr_contract_id.tp_jornada == '9':
            HorContratual.dscTpJor.valor = self.hr_contract_id.dsc_tp_jorn
        HorContratual.tmpParc.valor = self.hr_contract_id.tmp_parc

        # Popula vinculo.horContratual.horario
        if self.hr_contract_id.working_hours:
            for horario in self.hr_contract_id.working_hours.attendance_ids:
                Horario = pysped.esocial.leiaute.S2200_Horario_2()
                Horario.dia.valor = horario.diadasemana
                Horario.codHorContrat.valor = horario.turno_id.cod_hor_contrat
                HorContratual.horario.append(Horario)

        # Popula vinculo.infoContrato.horContratual (Efetivamente)
        S2200.evento.vinculo.infoContrato.horContratual.append(HorContratual)

        # Popula vinculo.infoContrato.filiacaoSindical
        FiliacaoSindical = pysped.esocial.leiaute.S2200_FiliacaoSindical_2()
        FiliacaoSindical.cnpjSindTrab.valor = limpa_formatacao(
            self.hr_contract_id.partner_union.cnpj_cpf or '')
        S2200.evento.vinculo.infoContrato.filiacaoSindical.append(FiliacaoSindical)

        # Popula vinculo.infoContrato.observacoes
        if self.hr_contract_id.notes:
            Observacoes = pysped.esocial.leiaute.S2200_Observacoes_2()
            Observacoes.observacao.valor = self.hr_contract_id.notes[0:254]
            S2200.evento.vinculo.infoContrato.observacoes.append(Observacoes)

        # Popula vinculo.sucessaoVinc
        if self.hr_contract_id.cnpj_empregador_anterior:
            SucessaoVinc = pysped.esocial.leiaute.S2200_SucessaoVinc_2()
            SucessaoVinc.cnpjEmpregAnt.valor = limpa_formatacao(
                self.hr_contract_id.cnpj_empregador_anterior)
            if self.hr_contract_id.matricula_anterior:
                SucessaoVinc.matricAnt.valor = self.hr_contract_id.matricula_anterior
            # SucessaoVinc.dtTransf.valor = self.hr_contract_id.date_start  # Se for transf. a data de inicio do contrato é a correta neste campo
            if self.hr_contract_id.observacoes_vinculo_anterior:
                SucessaoVinc.observacao.valor = self.hr_contract_id.observacoes_vinculo_anterior
            S2200.evento.vinculo.sucessaoVinc.append(SucessaoVinc)

        return S2200

    @api.multi
    def retorno_sucesso(self, evento):
        pass

    @api.multi
    def retorna_trabalhador(self):
        self.ensure_one()
        return self.hr_contract_id.employee_id
