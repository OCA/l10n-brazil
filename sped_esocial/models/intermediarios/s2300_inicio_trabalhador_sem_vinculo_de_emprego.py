# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, models, fields
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor
from openerp.exceptions import Warning, ValidationError
from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario
from dateutil.relativedelta import relativedelta


class SpedEsocialHrContrato(models.Model, SpedRegistroIntermediario):
    _name = "sped.esocial.contrato.autonomo"

    name = fields.Char(
        string='name',
        compute='_compute_name'
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
    registro_inclusao = fields.Many2one(
        string='Registro S-2300',
        comodel_name='sped.registro',
    )
    registro_retificacao = fields.Many2many(
        string='Registro S-2306 - Retificação',
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
            ('6', 'Retificado'),
            ('7', 'Excluído'),
        ],
        compute="compute_situacao_esocial",
        store=True,
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
    )

    @api.multi
    @api.depends('registro_inclusao.situacao', 'registro_retificacao.situacao')
    def compute_ultima_atualizacao(self):
        """
        Calcular a ultima atualizacao do registro
        """
        for record in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if record.registro_inclusao and \
                    record.registro_inclusao.situacao == '4':
                ultima_atualizacao = \
                    record.registro_inclusao.data_hora_origem

            # Se tiver alterações, pega a data/hora de origem da última alteração
            for retificacao in record.registro_retificacao:
                if retificacao.situacao == '4':
                    if retificacao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = retificacao.data_hora_origem

            # Popula o campo na tabela
            record.ultima_atualizacao = ultima_atualizacao

    @api.multi
    def gerar_registro(self):
        """
        """
        for record in self:
                
            if not record.registro_inclusao:
                values = {
                    'tipo': 'esocial',
                    'registro': 'S-2300',
                    'ambiente': record.company_id.esocial_tpAmb,
                    'company_id': record.company_id.id,
                    'evento': 'evtTSVInicio',
                    'origem': 
                        ('hr.contract,%s' % record.hr_contract_id.id),
                    'origem_intermediario': 
                        ('sped.esocial.contrato.autonomo,%s' % record.id),
                }
    
                sped_inclusao = self.env['sped.registro'].create(values)
                record.registro_inclusao = sped_inclusao

    @api.multi
    @api.depends('registro_inclusao.situacao', 'registro_retificacao.situacao')
    def compute_situacao_esocial(self):
        """
        Definir a situacao do envio do e social de acordo com a ultima 
        retificacao ou com o registro de inclusao
        """
        for record in self:
            
            situacao_esocial = '1'

            # TODO: Melhorar o IF e nao ficar sobrescrevendo variavel
            if record.registro_inclusao:
                situacao_esocial = \
                    record.registro_inclusao.situacao

            for retificao in record.registro_retificacao:
                situacao_esocial = retificao.situacao

            record.situacao_esocial = situacao_esocial

    @api.multi
    def _compute_name(self):
        """
        """
        for record in self:
            record.name = 'S-2300 - Admissão {}'.\
                format(record.hr_contract_id.display_name)

    def get_registro_para_retificar(self, sped_registro):
        """
        Identificar o registro para retificar
        :return:
        """
        # Se tiver registro de retificação com erro ou nao possuir nenhuma
        # retificação ainda, retornar o registro que veio no parametro
        retificacao_com_erro = sped_registro.retificacao_ids.filtered(
            lambda x: x.situacao in ['1', '3'])
        if retificacao_com_erro or not sped_registro.retificacao_ids:
            return sped_registro

        # Do contrario navegar ate as retificacoes com sucesso e efetuar a
        # verificacao de erro novamente
        else:
            registro_com_sucesso = sped_registro.retificacao_ids.filtered(
                lambda x: x.situacao not in ['1', '3'])

            return self.get_registro_para_retificar(registro_com_sucesso[0])

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        """
        Função para popular o xml com os dados referente ao contrato de um 
        Trabalhador sem vinculo
        :return:
        """
        self.ensure_one()

        # Validação
        validacao = ""

        # Cria o registro
        S2300 = pysped.esocial.leiaute.S2300_2()

        # Campos de controle para gerar ID do Evento -
        S2300.tpInsc = '1'
        S2300.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        # Popular ideEvento
        # Producao restrita == 2
        S2300.evento.ideEvento.tpAmb.valor = int(ambiente) or 2
        # Processo de Emissão = Aplicativo do Contribuinte
        S2300.evento.ideEvento.procEmi.valor = '1'
        # Odoo v8.0
        S2300.evento.ideEvento.verProc.valor = '8.0'

        #
        # Popula (Dados do Empregador)- evtTSVInicio.ideEvento.ideEmpregador
        #
        S2300.evento.ideEmpregador.tpInsc.valor = '1'
        S2300.evento.ideEmpregador.nrInsc.valor = \
            limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        # Retificação
        if operacao == 'R':  # Retificação
            S2300.evento.ideEvento.indRetif.valor = '2'

            registro_para_retificar = self.get_registro_para_retificar(
                self.sped_s2200_registro_inclusao)

            S2300.evento.ideEvento.nrRecibo.valor = \
                registro_para_retificar.recibo

        #
        # Popula "trabalhador" (Dados do Trabalhador)
        #
        S2300.evento.trabalhador.cpfTrab.valor = \
            limpa_formatacao(self.hr_contract_id.employee_id.cpf)
        S2300.evento.trabalhador.nisTrab.valor = \
            limpa_formatacao(self.hr_contract_id.employee_id.pis_pasep)
        S2300.evento.trabalhador.nmTrab.valor = \
            self.hr_contract_id.employee_id.name

        if self.hr_contract_id.employee_id.gender == 'male':
            sexo = 'M'
        elif self.hr_contract_id.employee_id.gender == 'female':
            sexo = 'F'
        S2300.evento.trabalhador.sexo.valor = sexo

        S2300.evento.trabalhador.racaCor.valor = \
            self.hr_contract_id.employee_id.ethnicity.code or ''

        if self.hr_contract_id.employee_id.marital:
            if self.hr_contract_id.employee_id.marital == 'single':
                estado_civil = '1'
            elif self.hr_contract_id.employee_id.marital in \
                    ['married','common_law_marriage']:
                estado_civil = '2'
            elif self.hr_contract_id.employee_id.marital == 'divorced':
                estado_civil = '3'
            elif self.hr_contract_id.employee_id.marital == 'separated':
                estado_civil = '4'
            elif self.hr_contract_id.employee_id.marital == 'widower':
                estado_civil = '5'
            S2300.evento.trabalhador.estCiv.valor = estado_civil

        # workaround kkkk
        code = self.hr_contract_id.employee_id.educational_attainment.code
        if len(self.hr_contract_id.employee_id.educational_attainment.code) == 1:
            code = '0' + self.hr_contract_id.employee_id.educational_attainment.code
        S2300.evento.trabalhador.grauInstr.valor = code

        # TODO separar Nome Legal de Nome Social no Odoo
        # S2300.evento.trabalhador.nmSoc = self.hr_contract_id.employee_id.name


        #
        # Popula Trabalhador.Nascimento
        #
        S2300.evento.trabalhador.nascimento.dtNascto.valor = \
            self.hr_contract_id.employee_id.birthday

        if self.hr_contract_id.employee_id.naturalidade:
            # Só preenche o município/estado se a naturalidade for Brasil
            if self.hr_contract_id.employee_id.pais_nascto_id == self.env.ref('sped_tabelas.tab06_105'):
                S2300.evento.trabalhador.nascimento.codMunic.valor = \
                    self.hr_contract_id.employee_id.naturalidade.state_id.ibge_code + \
                    self.hr_contract_id.employee_id.naturalidade.ibge_code
                S2300.evento.trabalhador.nascimento.uf.valor = \
                    self.hr_contract_id.employee_id.naturalidade.state_id.code
        S2300.evento.trabalhador.nascimento.paisNascto.valor = \
            self.hr_contract_id.employee_id.pais_nascto_id.codigo
        S2300.evento.trabalhador.nascimento.paisNac.valor = \
            self.hr_contract_id.employee_id.pais_nac_id.codigo
        S2300.evento.trabalhador.nascimento.nmMae.valor = \
            self.hr_contract_id.employee_id.mother_name or ''
        S2300.evento.trabalhador.nascimento.nmPai.valor = \
            self.hr_contract_id.employee_id.father_name or ''

        #
        # Popula trabalhador.Documentos
        #

        # CTPS
        if self.hr_contract_id.employee_id.ctps:
            CTPS = pysped.esocial.leiaute.S2300_CTPS_2()
            CTPS.nrCtps.valor = self.hr_contract_id.employee_id.ctps or ''
            CTPS.serieCtps.valor = \
                self.hr_contract_id.employee_id.ctps_series or ''
            CTPS.ufCtps.valor = \
                self.hr_contract_id.employee_id.ctps_uf_id.code or ''
            S2300.evento.trabalhador.documentos.CTPS.append(CTPS)

        # RIC  # TODO (Criar campos em l10n_br_hr)
        # if self.hr_contract_id.employee_id.ric:
        #     RIC = pysped.esocial.leiaute.S2300_RIC_2()
        #     RIC.nrRic.valor = self.hr_contract_id.employee_id.ric
        #     RIC.orgaoEmissor.valor =
        #           self.hr_contract_id.employee_id.ric_orgao_emissor
        #     if self.hr_contract_id.employee_id.ric_dt_exped:
        #         RIC.dtExped.valor =
        #           self.hr_contract_id.employee_id.ric_dt_exped
        #     S2300.evento.trabalhador.documentos.RG.append(RIC)

        # RG - Registro Geral
        if self.hr_contract_id.employee_id.rg:
            RG = pysped.esocial.leiaute.S2300_RG_2()
            RG.nrRg.valor = self.hr_contract_id.employee_id.rg or ''
            RG.orgaoEmissor.valor = \
                self.hr_contract_id.employee_id.organ_exp or ''
            if self.hr_contract_id.employee_id.rg_emission:
                RG.dtExped.valor = self.hr_contract_id.employee_id.rg_emission
            S2300.evento.trabalhador.documentos.RG.append(RG)

        # RNE - Registro Nacional de Estrangeiro
        # if self.hr_contract_id.employee_id.rne:
        #     RNE = pysped.esocial.leiaute.S2300_RNE_2()
        #     RNE.nrRne.valor = self.hr_contract_id.employee_id.rne
        #     RNE.orgaoEmissor.valor =
        #         self.hr_contract_id.employee_id.rne_orgao_emissor
        #     if self.hr_contract_id.employee_id.rne_dt_exped:
        #         RNE.dtExped.valor =
        #             self.hr_contract_id.employee_id.rne_dt_exped
        #     S2300.evento.trabalhador.documentos.RNE.append(RNE)

        # OC - Orgão de Classe
        # if self.hr_contract_id.employee_id.oc:
        #     OC = pysped.esocial.leiaute.S2300_OC_2()
        #     OC.nrOc.valor = self.hr_contract_id.employee_id.oc
        #     OC.orgaoEmissor.valor = \
        #         self.hr_contract_id.employee_id.oc_orgao_emissor
        #     if self.hr_contract_id.employee_id.oc_dt_exped:
        #         OC.dtExped.valor = self.hr_contract_id.employee_id.oc_dt_exped
        #     if self.hr_contract_id.employee_id.oc_dt_valid:
        #         OC.dtValid.valor = self.hr_contract_id.employee_id.oc_dt_valid
        #     S2300.evento.trabalhador.documentos.OC.append(OC)

        # CNH
        if self.hr_contract_id.employee_id.driver_license:
            CNH = pysped.esocial.leiaute.S2300_CNH_2()
            CNH.nrRegCnh.valor = self.hr_contract_id.employee_id.driver_license
            if self.hr_contract_id.employee_id.cnh_dt_exped:
                CNH.dtExped.valor = self.hr_contract_id.employee_id.cnh_dt_exped
            CNH.ufCnh.valor = self.hr_contract_id.employee_id.cnh_uf.code
            CNH.dtValid.valor = self.hr_contract_id.employee_id.expiration_date
            if self.hr_contract_id.employee_id.cnh_dt_pri_hab:
                CNH.dtPriHab.valor = self.hr_contract_id.employee_id.cnh_dt_pri_hab
            CNH.categoriaCnh.valor = self.hr_contract_id.employee_id.driver_categ
            S2300.evento.trabalhador.documentos.CNH.append(CNH)

        #
        # Popula Trabalhador.Endereco.Brasil
        #
        Brasil = pysped.esocial.leiaute.S2300_Brasil_2()
        if self.hr_contract_id.employee_id.address_home_id.tp_lograd:
            Brasil.tpLograd.valor = \
                self.hr_contract_id.employee_id.address_home_id.tp_lograd.codigo or ''
        else:
            Brasil.tpLograd.valor = 'R'
        Brasil.dscLograd.valor = \
            self.hr_contract_id.employee_id.address_home_id.street or ''
        Brasil.nrLograd.valor = \
            self.hr_contract_id.employee_id.address_home_id.number or 'S/N'
        Brasil.complemento.valor = \
            self.hr_contract_id.employee_id.address_home_id.street2 or ''
        Brasil.bairro.valor = \
            self.hr_contract_id.employee_id.address_home_id.district or ''
        if not self.hr_contract_id.employee_id.address_home_id.zip:
            validacao += 'Por favor preencha corretamente o CEP do ' \
                          'funcionário {}'.format(self.hr_contract_id.employee_id.name)
        else:
            Brasil.cep.valor = limpa_formatacao(
                self.hr_contract_id.employee_id.address_home_id.zip or '')
        Brasil.codMunic.valor = \
            self.hr_contract_id.employee_id.\
                address_home_id.l10n_br_city_id.state_id.ibge_code + \
            self.hr_contract_id.employee_id.\
                address_home_id.l10n_br_city_id.ibge_code
        Brasil.uf.valor = \
            self.hr_contract_id.employee_id.address_home_id.state_id.code
        S2300.evento.trabalhador.endereco.brasil.append(Brasil)

        #
        # Popula Trabalhador.Dependente
        #
        for dependente in self.hr_contract_id.employee_id.dependent_ids:
            Dependente = pysped.esocial.leiaute.S2300_Dependente_2()
            Dependente.tpDep.valor = \
                dependente.dependent_type_id.code.zfill(2)
            Dependente.nmDep.valor = dependente.name
            if dependente.dependent_verification:
                if not dependente.cnpj_cpf:
                    validacao += "O trabalhador {} está faltando o CPF de um dependente !".format(
                            self.hr_contract_id.employee_id.name)
                else:
                    Dependente.cpfDep.valor = limpa_formatacao(dependente.cnpj_cpf)
            Dependente.dtNascto.valor = dependente.dependent_dob
            Dependente.depIRRF.valor = \
                'S' if dependente.dependent_verification else 'N'
            Dependente.depSF.valor = 'S' if dependente.dep_sf else 'N'
            Dependente.incTrab.valor = 'S' if dependente.inc_trab else 'N'
            S2300.evento.trabalhador.dependente.append(Dependente)

        # Popula trabEstrangeiro se pais_nascto_id diferente de Brasil
        if self.hr_contract_id.employee_id.pais_nascto_id != self.env.ref('sped_tabelas.tab06_105'):
            TrabEstrangeiro = pysped.esocial.leiaute.S2300_TrabEstrangeiro_2()
            TrabEstrangeiro.classTrabEstrang.valor = self.hr_contract_id.employee_id.class_trab_estrang
            if self.hr_contract_id.employee_id.dt_chegada:
                TrabEstrangeiro.dtChegada.valor = self.hr_contract_id.employee_id.dt_chegada
            TrabEstrangeiro.casadoBr.valor = self.hr_contract_id.employee_id.casado_br
            TrabEstrangeiro.filhosBr.valor = self.hr_contract_id.employee_id.filhos_br
            S2300.evento.trabalhador.trabEstrangeiro.append(TrabEstrangeiro)

        #
        # Popula Trabalhador.Contato
        #
        Contato = pysped.esocial.leiaute.S2300_Contato_2()
        Contato.fonePrinc.valor = limpa_formatacao(
            self.hr_contract_id.employee_id.address_home_id.phone or '')
        Contato.foneAlternat.valor = limpa_formatacao(
            self.hr_contract_id.employee_id.alternate_phone or '')
        Contato.emailPrinc.valor = \
            self.hr_contract_id.employee_id.address_home_id.email or ''
        Contato.emailAlternat.valor = \
            self.hr_contract_id.employee_id.alternate_email or ''
        S2300.evento.trabalhador.contato.append(Contato)

        #
        # Popula InfoTSVInicio
        #

        data_inicio_contrato = fields.Datetime.from_string(self.hr_contract_id.date_start)
        data_inicio_esocial = fields.Datetime.from_string(self.company_id.esocial_periodo_inicial_id.date_start)
        data_inicio_esocial = data_inicio_esocial + relativedelta(months=3)
        cad_ini = 'S' if data_inicio_contrato < data_inicio_esocial else 'N'
        S2300.evento.infoTSVInicio.cadIni.valor = cad_ini

        S2300.evento.infoTSVInicio.codCateg.valor = self.hr_contract_id.category_id.code
        S2300.evento.infoTSVInicio.dtInicio.valor = self.hr_contract_id.date_start
        if self.hr_contract_id.category_id.code not in ['721', '722']:
            S2300.evento.infoTSVInicio.natAtividade.valor = self.hr_contract_id.nat_atividade

        # InfoTSVInicio.InfoComplementares
        InfoComplementares = pysped.esocial.leiaute.S2300_InfoComplementares_2()

        # InfoTSVInicio.InfoComplementares.CargoFuncao
        if self.hr_contract_id.category_id.code not in ['901','903','904','905']:
            CargoFuncao = pysped.esocial.leiaute.S2300_CargoFuncao_2()
            CargoFuncao.codCargo.valor = self.hr_contract_id.job_id.codigo
            # CargoFuncao.codFuncao.valor = ''
            InfoComplementares.cargoFuncao.append(CargoFuncao)

        # InfoTSVInicio.InfoComplementares.Remuneracao
        if self.hr_contract_id.category_id.code in ['301','302','305','306','721','722','771']:
            Remuneracao = pysped.esocial.leiaute.S2300_Remuneracao_2()
            Remuneracao.vrSalFx.valor = formata_valor(self.hr_contract_id.wage)
            if self.hr_contract_id.salary_unit.code in [7]:
                Remuneracao.vrSalFx.valor = 0
            Remuneracao.undSalFixo.valor = self.hr_contract_id.salary_unit.code
            if self.hr_contract_id.salary_unit.code in [6,7]:
                Remuneracao.dscSalVar.valor = self.hr_contract_id.dsc_sal_var
            InfoComplementares.remuneracao.append(Remuneracao)

        # InfoTSVInicio.InfoComplementares.FGTS
        if self.hr_contract_id.category_id.code in ['721']:
            FGTS = pysped.esocial.leiaute.S2300_FGTS_2()
            FGTS.opcFGTS.valor = self.hr_contract_id.opc_fgts
            FGTS.dtOpcFGTS.valor = self.hr_contract_id.dt_opc_fgts
            data_inicio_contrato = \
                fields.Datetime.from_string(self.hr_contract_id.date_start)
            data_inicio_esocial = \
                fields.Datetime.from_string(
                    self.company_id.esocial_periodo_inicial_id.date_start)
            FGTS.dtOpcFGTS.valor = self.hr_contract_id.date_start \
                if not data_inicio_esocial or data_inicio_contrato > data_inicio_esocial \
                else self.company_id.esocial_periodo_inicial_id.date_start
            InfoComplementares.fgts.append(FGTS)

        # InfoTSVInicio.InfoComplementares.InfoDirigenteSindical
        # if self.hr_contract_id.category_id.code in ['401']:
        # InfoDirigenteSind = pysped.esocial.leiaute.S2300_InfoDirigenteSindical_2()
        # InfoDirigenteSind.categOrigem.valor = ''
        # InfoDirigenteSind.cnphOrigem.valor = ''
        # InfoDirigenteSind.dtAdmOrigem.valor = ''
        # InfoDirigenteSind.matricOrig.valor = ''
        # InfoComplementares.infoDirigenteSind.append(InfoDirigenteSind)

        # InfoTSVInicio.InfoComplementares.InfoTrabCedido

        if self.hr_contract_id.category_id.code == '410':
            InfoTrabCedido = pysped.esocial.leiaute.S2300_InfoTrabCedido_2()
            InfoTrabCedido.cnpjCednt.valor = \
                limpa_formatacao(self.hr_contract_id.cnpj_empregador_cedente)
            InfoTrabCedido.categOrig.valor = \
                self.hr_contract_id.assignor_category_id.code
            InfoTrabCedido.matricCed.valor = \
                self.hr_contract_id.matricula_cedente
            InfoTrabCedido.dtAdmCed.valor = \
                self.hr_contract_id.data_admissao_cedente
            InfoTrabCedido.tpRegTrab.valor = \
                self.hr_contract_id.labor_regime_id.code
            InfoTrabCedido.tpRegPrev.valor = self.hr_contract_id.tp_reg_prev
            InfoTrabCedido.infOnus.valor = self.hr_contract_id.infOnus
            InfoComplementares.infoTrabCedido.append(InfoTrabCedido)

        # InfoTSVInicio.InfoComplementares.InfoEstagiario
        # if self.hr_contract_id.category_id.code in ['901']:
        # InfoEstagiario = pysped.esocial.leiaute.S2300_InfoEstagiario_2()
        # InfoEstagiario.natEstagio.valor = ''
        # InfoEstagiario.nivEstagio.valor = ''
        # InfoEstagiario.areaAtuacao.valor = ''
        # InfoEstagiario.nrApol.valor = ''
        # InfoEstagiario.vlrBolsa.valor = ''
        # InfoEstagiario.dtPrevTerm.valor = ''
        # InfoComplementares.infoEstagiario.append(InfoEstagiario)

        # InfoTSVInicio.InfoComplementares.InfoEstagiario.InstEnsino
        # InstEnsino = pysped.esocial.leiaute.S2300_InstEnsino_2()
        # InstEnsino.cnpjInstEnsino = ''
        # InstEnsino.nmRazao = ''
        # InstEnsino.dscLograd = ''
        # InstEnsino.nrLograd = ''
        # InstEnsino.bairro = ''
        # InstEnsino.cep = ''
        # InstEnsino.codMunic = ''
        # InstEnsino.uf = ''
        # InfoComplementares.instEnsino.append(InstEnsino)

        # InfoTSVInicio.InfoComplementares.InfoEstagiario.AgeIntegracao
        # AgeIntegracao = pysped.esocial.leiaute.S2300_AgeIntegracao_2()
        # AgeIntegracao.cnpjAgntInteg = ''
        # AgeIntegracao.nmRazao = ''
        # AgeIntegracao.dscLograd = ''
        # AgeIntegracao.nrLograd = ''
        # AgeIntegracao.bairro = ''
        # AgeIntegracao.cep = ''
        # AgeIntegracao.codMunic = ''
        # AgeIntegracao.uf = ''
        # InfoComplementares.ageIntegracao.append(AgeIntegracao)

        # InfoTSVInicio.InfoComplementares.InfoEstagiario.SupervisorEstagio
        # SupervisorEstagio = pysped.esocial.leiaute.S2300_SupervisorEstagio_2()
        # SupervisorEstagio.cpfSupervisor = ''
        # SupervisorEstagio.nmSuperv = ''
        # InfoComplementares.supervisorEstagio.append(SupervisorEstagio)

        # InfoTSVInicio.Afastamento
        # Afastamento = pysped.esocial.leiaute.S2300_Afastamento_2()
        # Afastamento.dtIniAfast = ''
        # Afastamento.codMotAfast = ''
        # S2300.evento.infoTSVInicio.afastamento.append(Afastamento)

        # # InfoTSVInicio.Termino
        # if self.hr_contract_id.date_end:
        #     Termino = pysped.esocial.leiaute.S2300_Termino_2()
        #     Termino.dtTerm.valor = self.hr_contract_id.date_end
        #     S2300.evento.infoTSVInicio.termino.append(Termino)

        S2300.evento.infoTSVInicio.infoComplementares.append(InfoComplementares)
        return S2300, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        pass

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
            if self.registro_inclusao.situacao in ['1', '3']:
                registro = self.registro_inclusao
            else:
                for r in self.registro_retificacao:
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
            if self.registro_inclusao.situacao == '2':
                registro = self.registro_inclusao
            else:
                for r in self.registro_retificacao:
                    if r.situacao == '2':
                        registro = r

            # Com o registro identificado, é só rodar o método consulta_lote() do registro
            if registro:
                registro.consulta_lote()
