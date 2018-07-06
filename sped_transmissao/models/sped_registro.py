# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor
from datetime import datetime
from openerp.exceptions import ValidationError
import base64
import pysped
import tempfile
from decimal import Decimal


class SpedRegistro(models.Model):
    _name = 'sped.registro'
    _inherit = []
    _description = 'Registros SPED'
    _rec_name = 'registro'
    _order = "data_hora_origem DESC, situacao"

    # Campo para mostrar que está limpado db
    limpar_db = fields.Boolean()

    tipo = fields.Selection(
        string='Tipo',
        selection=[
            ('efdreinf', 'EFD-Reinf'),
            ('esocial', 'e-Social'),
        ],
    )
    codigo = fields.Char(
        string='Código',
        default=lambda self: self.env['ir.sequence'].next_by_code('sped.registro'),
        readonly=True,
    )
    registro = fields.Char(
        string='Registro',
        size=30,
    )
    evento = fields.Char(
        string='Evento Sped',
        size=30,
    )
    operacao = fields.Selection(
        string='Operação',
        selection=[
            ('na', 'N/A'),
            ('I', 'Inclusão'),
            ('A', 'Alteração'),
            ('E', 'Exclusão'),
        ],
        default='na',
    )
    ambiente = fields.Selection(
        string='Ambiente',
        selection=[
            ('1', 'Produção'),
            ('2', 'Produção Restrita'),
            ('3', 'Homologação'),
        ],
    )
    origem = fields.Reference(
        string='Documento de Origem',
        selection=[
            ('res.company', 'Empresa')
        ],
    )
    origem_intermediario = fields.Reference(
        string='Registro Intermediário',
        selection=[
            ('sped.empregador', 'S-1000')
        ],
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    id_evento = fields.Char(
        string='ID do Evento',
        size=36,
    )
    situacao = fields.Selection(
        string='Situação',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        default='1',
    )
    data_hora_origem = fields.Datetime(
        string='Data/Hora Origem',
        default=lambda self: fields.Datetime.now(),
    )
    data_hora_transmissao = fields.Datetime(
        string='Data/Hora Transmissão',
    )
    data_hora_retorno = fields.Datetime(
        string='Data/Hora Retorno',
    )
    lote_ids = fields.Many2many(
        string='Lotes de Transmissão',
        comodel_name='sped.lote',
    )

    # Status de Retorno
    recibo = fields.Char(  # evtTotal.ideRecRetorno.infoRecEv.nrRecArqBase
        string='Recibo de Entrega',
    )
    cd_retorno = fields.Char(  # evtTotal.ideRecRetorno.ideStatus.cdRetorno
        string='Código de Retorno',
    )
    desc_retorno = fields.Char(  # evtTotal.ideRecRetorno.ideStatus.descRetorno
        string='Retorno',
    )

    # Ocorrências retornadas
    ocorrencia_ids = fields.One2many(
        string='Ocorrências',
        comodel_name='sped.ocorrencia',
        inverse_name='transmissao_id',
    )

    # Retorno EFD-Reinf
    per_apur = fields.Char(  # evtTotal.ideEvento.perApur
        string='Período de Apuração',
    )
    dh_process = fields.Char(  # evtTotal.ideRecRetorno.infoRecEv.dhProcess
        string='Data/Hora Início Processamento',
    )
    tp_ev = fields.Char(  # evtTotal.ideRecRetorno.infoRecEv.tpEv
        string='Tipo do Evento',
    )
    id_ev = fields.Char(  # evtTotal.ideRecRetorno.infoRecEv.idEv
        string='ID do Evento',
    )
    hash = fields.Char(  # evtTotal.ideRecRetorno.infoRecEv.hash
        string='Hash do Arquivo Processado',
    )
    envio_xml_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML enviado',
        copy=False,
    )
    envio_xml = fields.Text(
        string='XML',
        compute='_compute_arquivo_xml',
    )
    retorno_xml_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de retorno',
        copy=False,
    )
    retorno_xml = fields.Text(
        string='XML',
        compute='_compute_arquivo_xml',
    )
    consulta_xml_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de consulta',
        copy=False,
    )
    consulta_xml = fields.Text(
        string='XML',
        compute='_compute_arquivo_xml',
    )
    fechamento_xml_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de Fechamento',
        copy=False,
    )
    fechamento_xml = fields.Text(
        string='XML',
        compute='_compute_arquivo_xml',
    )
    protocolo = fields.Char(
        string='Protocolo',
        size=60,
    )

    # Identifica se o registro ja está na fila de um lote para transmissão
    transmissao_lote = fields.Boolean(
        string='Transmissão por Lote?',
        compute='_compute_lote',
    )

    @api.depends('lote_ids')
    def _compute_lote(self):
        for registro in self:
            transmissao_lote = False
            for lote in registro.lote_ids:
                if lote.situacao != '4':
                    transmissao_lote = True
            registro.transmissao_lote = transmissao_lote

    @api.depends('envio_xml_id', 'retorno_xml_id', 'consulta_xml', 'fechamento_xml_id')
    def _compute_arquivo_xml(self):
        for documento in self:
            dados = {
                'envio_xml': False,
                'retorno_xml': False,
                'consulta_xml': False,
                'fechamento_xml': False,
            }

            if documento.envio_xml_id:
                dados['envio_xml'] = documento.envio_xml_id.conteudo_xml

            if documento.retorno_xml_id:
                dados['retorno_xml'] = documento.retorno_xml_id.conteudo_xml

            if documento.consulta_xml_id:
                dados['consulta_xml'] = documento.consulta_xml_id.conteudo_xml

            if documento.fechamento_xml_id:
                dados['fechamento_xml'] = documento.fechamento_xml_id.conteudo_xml

            documento.update(dados)

    @api.multi
    def _grava_anexo(self, nome_arquivo='', conteudo='', model=None, res_id=None):
        self.ensure_one()

        if model is None:
            model = self._name

        busca = [
            ('res_model', '=', model),
            ('res_id', '=', res_id if res_id is not None else self.id),
            ('name', '=', nome_arquivo),
        ]
        anexo = self.env['ir.attachment'].search(busca)
        anexo.unlink()

        if type(conteudo) != bytes:
            conteudo = conteudo.encode('utf-8')

        dados = {
            'name': nome_arquivo,
            'datas_fname': nome_arquivo,
            'res_model': model,
            'res_id': res_id if res_id is not None else self.id,
            'datas': base64.b64encode(conteudo),
            # 'mimetype': tipo,
        }

        anexo = self.env['ir.attachment'].create(dados)

        return anexo

    @api.multi
    def unlink(self):

        for registro in self:

            # Não permite excluir se a situação não for '1-Pendente' ou '3-Erro(s)'
            if registro.situacao not in ['1', '3']:
                raise ValidationError("Não pode excluir registros que não estejam Pendente(s) !")

            # Exclui
            super(SpedRegistro, registro).unlink()

        return True

    @api.multi
    def limpa_db(self):
        self.ensure_one()
        if self.ambiente == '1':
            raise ValidationError("Ambiente de Produção não suporta Limpeza de Banco de Dados !")

        if self.registro == 'S-1000':
            self.origem_intermediario.limpar_db = True
            self.transmitir_lote()
            self.recibo = False
            self.protocolo = False
            self.origem_intermediario.limpar_db = False
        elif self.registro == 'R-1000':
            self.limpar_db = True
            self.gera_xml()
            self.recibo = False
            self.protocolo = False
            self.limpar_db = False

    @api.multi
    def consulta_lote(self):
        self.ensure_one()

        # Identifica o lote que pode ser consultado
        lote_consultar = False
        for lote in self.lote_ids:
            if lote.situacao == '2':
                lote_consultar = lote

        # Executa a consulta
        if lote_consultar:
            lote_consultar.consultar()

    @api.multi
    def transmitir_lote(self):
        self.ensure_one()

        # Se já tem um lote pendente transmissão, transmite ele
        for lote in self.lote_ids:
            if lote.situacao == '1':
                lote.transmitir()
                return

        # Se chegou até aqui é porque não tem nenhum lote criado, então cria um novo
        #
        # Criar registro do Lote
        vals = {
            'tipo': 'esocial',
            'company_id': self.company_id.id,
            'ambiente': self.ambiente,
            'transmissao_ids': [(4, self.id)],
        }
        lote_id = self.env['sped.lote'].create(vals)
        self.lote_ids = [(4, lote_id.id)]

        # Transmite
        lote_id.transmitir()

    @api.multi
    def gera_xml(self):
        self.ensure_one()

        # Gravar certificado em arquivo temporario
        arquivo = tempfile.NamedTemporaryFile()
        arquivo.seek(0)
        arquivo.write(
            base64.decodestring(self.company_id.nfe_a1_file)
        )
        arquivo.flush()

        processo = False

        # Prepara variaveis para gravar os XMLs
        envio_xml = False
        retorno_xml = False

        # Registro S-1000 - Informações do Empregador (e-Social)
        if self.registro == 'S-1000':
            return

            # # Criar registro do Lote
            # vals = {
            #     'tipo': 'esocial',
            #     'company_id': self.company_id.id,
            #     'ambiente': self.ambiente,
            #     'transmissao_ids': [(4, self.id)],
            # }
            #
            # lote_id = self.env['sped.lote'].create(vals)
            # self.lote_ids = [(4, lote_id.id)]
            #
            # # Transmite
            # lote_id.transmitir()

        # Registro S-1005 - Tabela de Estabelecimentos, Obras ou Unidades de Órgãos Públicos
        elif self.registro == 'S-1005':
            return

            # # Criar registro do Lote
            # data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # vals = {
            #     'tipo': 'esocial',
            #     'ambiente': self.ambiente,
            #     'transmissao_ids': [(4, self.id)],
            #     'data_hora_transmissao': data_hora_transmissao,
            # }
            #
            # lote_id = self.env['sped.lote'].create(vals)
            # self.lote_ids = [(4, lote_id.id)]
            # self.data_hora_transmissao = data_hora_transmissao

        # Registro S-1010 - Tabela de Rubricas
        elif self.registro == 'S-1010':
            return

            # # Criar registro do Lote
            # data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # vals = {
            #     'tipo': 'esocial',
            #     'ambiente': self.ambiente,
            #     'transmissao_ids': [(4, self.id)],
            #     'data_hora_transmissao': data_hora_transmissao,
            # }
            #
            # lote_id = self.env['sped.lote'].create(vals)
            # self.lote_ids = [(4, lote_id.id)]
            # self.data_hora_transmissao = data_hora_transmissao

        # Registro S-1020 - Tabela de Lotações Tributárias
        elif self.registro == 'S-1020':
            return

            # # Criar registro do Lote
            # data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # vals = {
            #     'tipo': 'esocial',
            #     'ambiente': self.ambiente,
            #     'transmissao_ids': [(4, self.id)],
            #     'data_hora_transmissao': data_hora_transmissao,
            # }
            #
            # lote_id = self.env['sped.lote'].create(vals)
            # self.lote_ids = [(4, lote_id.id)]
            # self.data_hora_transmissao = data_hora_transmissao

        # Registro S-1030 - Tabela de Cargos/Empregos Públicos
        elif self.registro == 'S-1030':



            # Gera
            data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            dh_transmissao = datetime.now().strftime('%Y%m%d%H%M%S')
            S1030.gera_id_evento(dh_transmissao)
            processador = pysped.ProcessadorESocial()

            processador.certificado.arquivo = arquivo.name
            processador.certificado.senha = self.company_id.nfe_a1_password
            processador.ambiente = int(self.ambiente)

            # Define a Inscrição do Processador
            processador.tpInsc = '1'
            processador.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)

            # Criar registro do Lote
            vals = {
                'tipo': 'esocial',
                'ambiente': self.ambiente,
                'transmissao_ids': [(4, self.id)],
                'data_hora_transmissao': data_hora_transmissao,
            }

            lote_id = self.env['sped.lote'].create(vals)
            self.lote_ids = [(4, lote_id.id)]
            self.data_hora_transmissao = data_hora_transmissao

            # Transmite
            processo = processador.enviar_lote([S1030])
            envio_xml = processo.envio.envioLoteEventos.eventos[0].xml
            envio_xml_nome = S1030.evento.Id.valor + '-S1030-env.xml'
            retorno_xml = processo.resposta.xml
            retorno_xml_nome = S1030.evento.Id.valor + '-S1030-ret.xml'

        # Registro S-1050 - Informações de Turno de Jornada de Trabalho
        if self.registro == 'S-1050':
            # Criar registro do Lote
            data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            vals = {
                'tipo': 'esocial',
                'ambiente': self.ambiente,
                'transmissao_ids': [(4, self.id)],
                'data_hora_transmissao': data_hora_transmissao,
            }

            lote_id = self.env['sped.lote'].create(vals)
            self.lote_ids = [(4, lote_id.id)]
            self.data_hora_transmissao = data_hora_transmissao

            lote_id.transmitir()

        # Registro S-2200 - Cadastramento Inicial do Vínculo e Admissão/Ingresso do Trabalhador
        elif self.registro == 'S-2200':

            # Cria o registro
            S2200 = pysped.esocial.leiaute.S2200_2()

            # Popula ideEvento
            S2200.tpInsc = '1'
            S2200.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
            S2200.evento.ideEvento.tpAmb.valor = int(self.ambiente)
            S2200.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
            S2200.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

            # Popula ideEmpregador (Dados do Empregador)
            S2200.evento.ideEmpregador.tpInsc.valor = '1'
            S2200.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

            # Popula "trabalhador" (Dados do Trabalhador)
            S2200.evento.trabalhador.cpfTrab.valor = limpa_formatacao(self.origem.employee_id.cpf)
            S2200.evento.trabalhador.nisTrab.valor = limpa_formatacao(self.origem.employee_id.pis_pasep)
            S2200.evento.trabalhador.nmTrab.valor = self.origem.employee_id.name
            sexo = ''
            if self.origem.employee_id.gender == 'male':
                sexo = 'M'
            elif self.origem.employee_id.gender == 'female':
                sexo = 'F'
            S2200.evento.trabalhador.sexo.valor = sexo
            S2200.evento.trabalhador.racaCor.valor = self.origem.employee_id.ethnicity.code or ''
            estado_civil = ''
            if self.origem.employee_id.marital == 'single':
                estado_civil = '1'
            elif self.origem.employee_id.marital in ['married', 'common_law_marriage']:
                estado_civil = '2'
            elif self.origem.employee_id.marital == 'divorced':
                estado_civil = '3'
            elif self.origem.employee_id.marital == 'separated':
                estado_civil = '4'
            elif self.origem.employee_id.marital == 'widower':
                estado_civil = '5'
            S2200.evento.trabalhador.estCiv.valor = estado_civil
            S2200.evento.trabalhador.grauInstr.valor = self.origem.employee_id.educational_attainment.code or ''
            S2200.evento.trabalhador.indPriEmpr.valor = 'S' if self.origem.primeiro_emprego else 'N'
            # S2200.evento.trabalhador.nmSoc =  # TODO separar Nome Legal de Nome Social no Odoo

            # Popula trabalhador.nascimento
            S2200.evento.trabalhador.nascimento.dtNascto.valor = self.origem.employee_id.birthday
            S2200.evento.trabalhador.nascimento.codMunic.valor = \
                self.origem.employee_id.naturalidade.state_id.ibge_code + self.origem.employee_id.naturalidade.ibge_code
            S2200.evento.trabalhador.nascimento.uf.valor = self.origem.employee_id.naturalidade.state_id.code or ''
            S2200.evento.trabalhador.nascimento.paisNascto.valor = self.origem.employee_id.pais_nascto_id.codigo
            S2200.evento.trabalhador.nascimento.paisNac.valor = self.origem.employee_id.pais_nac_id.codigo
            S2200.evento.trabalhador.nascimento.nmMae.valor = self.origem.employee_id.mother_name or ''
            S2200.evento.trabalhador.nascimento.nmPai.valor = self.origem.employee_id.father_name or ''

            # Popula trabalhador.documentos
            # CTPS
            if self.origem.employee_id.ctps:
                CTPS = pysped.esocial.leiaute.S2200_CTPS_2()
                CTPS.nrCtps.valor = self.origem.employee_id.ctps or ''
                CTPS.serieCtps.valor = self.origem.employee_id.ctps_series or ''
                CTPS.ufCtps.valor = self.origem.employee_id.ctps_uf_id.code or ''
                S2200.evento.trabalhador.documentos.CTPS.append(CTPS)

            # # RIC  # TODO (Criar campos em l10n_br_hr)
            # if self.origem.employee_id.ric:
            #     RIC = pysped.esocial.leiaute.S2200_RIC_2()
            #     RIC.nrRic.valor = self.origem.employee_id.ric
            #     RIC.orgaoEmissor.valor = self.origem.employee_id.ric_orgao_emissor
            #     if self.origem.employee_id.ric_dt_exped:
            #         RIC.dtExped.valor = self.origem.employee_id.ric_dt_exped
            #     S2200.evento.trabalhador.documentos.RG.append(RIC)

            # RG
            if self.origem.employee_id.rg:
                RG = pysped.esocial.leiaute.S2200_RG_2()
                RG.nrRg.valor = self.origem.employee_id.rg or ''
                RG.orgaoEmissor.valor = self.origem.employee_id.organ_exp or ''
                if self.origem.employee_id.rg_emission:
                    RG.dtExped.valor = self.origem.employee_id.rg_emission
                S2200.evento.trabalhador.documentos.RG.append(RG)

            # # RNE  # TODO (Criar campos em l10n_br_hr)
            # if self.origem.employee_id.rne:
            #     RNE = pysped.esocial.leiaute.S2200_RNE_2()
            #     RNE.nrRne.valor = self.origem.employee_id.rne
            #     RNE.orgaoEmissor.valor = self.origem.employee_id.rne_orgao_emissor
            #     if self.origem.employee_id.rne_dt_exped:
            #         RNE.dtExped.valor = self.origem.employee_id.rne_dt_exped
            #     S2200.evento.trabalhador.documentos.RNE.append(RNE)

            # # OC  # TODO (Criar campos em l10n_br_hr)
            # if self.origem.employee_id.oc:
            #     OC = pysped.esocial.leiaute.S2200_OC_2()
            #     OC.nrOc.valor = self.origem.employee_id.oc
            #     OC.orgaoEmissor.valor = self.origem.employee_id.oc_orgao_emissor
            #     if self.origem.employee_id.oc_dt_exped:
            #         OC.dtExped.valor = self.origem.employee_id.oc_dt_exped
            #     if self.origem.employee_id.oc_dt_valid:
            #         OC.dtValid.valor = self.origem.employee_id.oc_dt_valid
            #     S2200.evento.trabalhador.documentos.OC.append(OC)

            # CNH
            if self.origem.employee_id.driver_license:
                CNH = pysped.esocial.leiaute.S2200_CNH_2()
                CNH.nrRegCnh.valor = self.origem.employee_id.driver_license
                if self.origem.employee_id.cnh_dt_exped:
                    CNH.dtExped.valor = self.origem.employee_id.cnh_dt_exped
                CNH.ufCnh.valor = self.origem.employee_id.cnh_uf.code
                CNH.dtValid.valor = self.origem.employee_id.expiration_date
                if self.origem.employee_id.cnh_dt_pri_hab:
                    CNH.dtPriHab.valor = self.origem.employee_id.cnh_dt_pri_hab
                CNH.categoriaCnh.valor = self.origem.employee_id.driver_categ
                S2200.evento.trabalhador.documentos.CNH.append(CNH)

            # Popula trabalhador.endereco.brasil
            Brasil = pysped.esocial.leiaute.S2200_Brasil_2()
            if self.origem.employee_id.address_home_id.tp_lograd:
                Brasil.tpLograd.valor = self.origem.employee_id.address_home_id.tp_lograd.codigo or ''
            else:
                Brasil.tpLograd.valor = 'R'
            Brasil.dscLograd.valor = self.origem.employee_id.address_home_id.street or ''
            Brasil.nrLograd.valor = self.origem.employee_id.address_home_id.number or ''
            Brasil.complemento.valor = self.origem.employee_id.address_home_id.street2 or ''
            Brasil.bairro.valor = self.origem.employee_id.address_home_id.district or ''
            Brasil.cep.valor = limpa_formatacao(self.origem.employee_id.address_home_id.zip) or ''
            Brasil.codMunic.valor = \
                self.origem.employee_id.address_home_id.l10n_br_city_id.state_id.ibge_code + \
                self.origem.employee_id.address_home_id.l10n_br_city_id.ibge_code
            Brasil.uf.valor = self.origem.employee_id.address_home_id.state_id.code
            S2200.evento.trabalhador.endereco.brasil.append(Brasil)

            # Popula trabalhador.dependente
            if self.origem.employee_id.have_dependent:
                for dependente in self.origem.employee_id.dependent_ids:
                    Dependente = pysped.esocial.leiaute.S2200_Dependente_2()
                    Dependente.tpDep.valor = dependente.dependent_type_id.code.zfill(2)
                    Dependente.nmDep.valor = dependente.dependent_name
                    Dependente.cpfDep.valor = dependente.dependent_cpf
                    Dependente.dtNascto.valor = dependente.dependent_dob
                    Dependente.depIRRF.valor = 'S' if dependente.dependent_verification else 'N'
                    Dependente.depSF.valor = 'S' if dependente.dep_sf else 'N'
                    Dependente.incTrab.valor = 'S' if dependente.inc_trab else 'N'
                    S2200.evento.trabalhador.dependente.append(Dependente)

            # Popula trabalhador.contato
            Contato = pysped.esocial.leiaute.S2200_Contato_2()
            Contato.fonePrinc.valor = limpa_formatacao(self.origem.employee_id.address_home_id.phone or '')
            Contato.foneAlternat.valor = limpa_formatacao(self.origem.employee_id.alternate_phone or '')
            Contato.emailPrinc.valor = self.origem.employee_id.address_home_id.email or ''
            Contato.emailAlternat.valor = self.origem.employee_id.alternate_email or ''
            S2200.evento.trabalhador.contato.append(Contato)

            # Popula "vinculo"
            S2200.evento.vinculo.matricula.valor = self.origem.codigo_contrato
            S2200.evento.vinculo.tpRegTrab.valor = self.origem.labor_regime_id.code
            S2200.evento.vinculo.tpRegPrev.valor = self.origem.tp_reg_prev
            S2200.evento.vinculo.cadIni.valor = self.origem.cad_ini

            # Popula vinculo.infoRegimeTrab
            if self.origem.labor_regime_id.code == '1':

                # Popula infoCeletista
                InfoCeletista = pysped.esocial.leiaute.S2200_InfoCeletista_2()
                InfoCeletista.dtAdm.valor = self.origem.date_start
                InfoCeletista.tpAdmissao.valor = str(self.origem.admission_type_id.code)
                InfoCeletista.indAdmissao.valor = self.origem.indicativo_de_admissao
                InfoCeletista.tpRegJor.valor = self.origem.tp_reg_jor
                InfoCeletista.natAtividade.valor = self.origem.nat_atividade
                InfoCeletista.cnpjSindCategProf.valor = limpa_formatacao(self.origem.partner_union.cnpj_cpf)
                InfoCeletista.FGTS.opcFGTS.valor = self.origem.opc_fgts
                if self.origem.dt_opc_fgts:
                    InfoCeletista.FGTS.dtOpcFGTS.valor = self.origem.dt_opc_fgts
                S2200.evento.vinculo.infoRegimeTrab.infoCeletista.append(InfoCeletista)

            elif self.origem.labor_regime_id.code == '2':

                # Popula infoEstatutario  # TODO
                InfoEstatutario = pysped.esocial.leiaute.S2200_InfoEstatutario_2()


            # Popula vinculo.infoContrato
            S2200.evento.vinculo.infoContrato.codCargo.valor = self.origem.job_id.codigo
            # S2200.evento.vinculo.infoContrato.codFuncao.valor =   # TODO Quando lidar com Estatutários
            S2200.evento.vinculo.infoContrato.codCateg.valor = self.origem.categoria  # TODO Migrar esse campo para
                                                                                      # relacionar com tabela 1 do eSocial
            # S2200.evento.vinculo.infoContrato.codCarreira.valor =   # TODO Quando lidar com Estatutários
            # S2200.evento.vinculo.infoContrato.dtIngrCarr.valor =   # TODO Quando lidar com Estatutários

            # Popula vinculo.infoContrato.remuneracao
            S2200.evento.vinculo.infoContrato.vrSalFx.valor = formata_valor(self.origem.wage)
            S2200.evento.vinculo.infoContrato.undSalFixo.valor = self.origem.salary_unit.code
            S2200.evento.vinculo.infoContrato.dscSalVar.valor = self.origem.dsc_sal_var or ''

            # Popula vinculo.infoContrato.duracao
            S2200.evento.vinculo.infoContrato.tpContr.valor = self.origem.tp_contr
            if self.origem.tp_contr == '2':
                S2200.evento.vinculo.infoContrato.dtTerm.valor = self.origem.date_end
                S2200.evento.vinculo.infoContrato.clauAssec.valor = self.origem.clau_assec

            # Popula vinculo.infoContrato.localTrabalho
            LocalTrabGeral = pysped.esocial.leiaute.S2200_LocalTrabGeral_2()
            LocalTrabGeral.tpInsc.valor = '1'
            LocalTrabGeral.nrInsc.valor = limpa_formatacao(self.origem.company_id.cnpj_cpf)
            # LocalTrabGeral.descComp.valor = ''  # TODO Criar no contrato
            S2200.evento.vinculo.infoContrato.localTrabalho.localTrabGeral.append(LocalTrabGeral)

            # Popula vinculo.infoContrato.horContratual (Campos)
            HorContratual = pysped.esocial.leiaute.S2200_HorContratual_2()
            HorContratual.qtdHrsSem.valor = formata_valor(self.origem.weekly_hours)
            print(formata_valor(self.origem.weekly_hours))
            HorContratual.tpJornada.valor = self.origem.tp_jornada
            if self.origem.tp_jornada == '9':
                HorContratual.dscTpJor.valor = self.origem.dsc_tp_jorn
            HorContratual.tmpParc.valor = self.origem.tmp_parc

            # Popula vinculo.horContratual.horario
            if self.origem.working_hours:
                for horario in self.origem.working_hours.attendance_ids:
                    Horario = pysped.esocial.leiaute.S2200_Horario_2()
                    Horario.dia.valor = horario.diadasemana
                    Horario.codHorContrat.valor = horario.turno_id.cod_hor_contrat
                    HorContratual.horario.append(Horario)

            # Popula vinculo.infoContrato.horContratual (Efetivamente)
            S2200.evento.vinculo.infoContrato.horContratual.append(HorContratual)

            # Popula vinculo.infoContrato.filiacaoSindical
            FiliacaoSindical = pysped.esocial.leiaute.S2200_FiliacaoSindical_2()
            FiliacaoSindical.cnpjSindTrab.valor = limpa_formatacao(self.origem.partner_union.cnpj_cpf or '')
            S2200.evento.vinculo.infoContrato.filiacaoSindical.append(FiliacaoSindical)

            # Popula vinculo.infoContrato.observacoes
            if self.origem.notes:
                Observacoes = pysped.esocial.leiaute.S2200_Observacoes_2()
                Observacoes.observacao.valor = self.origem.notes[0:254]
                S2200.evento.vinculo.infoContrato.observacoes.append(Observacoes)

            # Popula vinculo.sucessaoVinc
            if self.origem.cnpj_empregador_anterior:
                SucessaoVinc = pysped.esocial.leiaute.S2200_SucessaoVinc_2()
                SucessaoVinc.cnpjEmpregAnt.valor = limpa_formatacao(self.origem.cnpj_empregador_anterior)
                if self.origem.matricula_anterior:
                    SucessaoVinc.matricAnt.valor = self.origem.matricula_anterior
                SucessaoVinc.dtTransf.valor = self.origem.date_start  # Se for transf. a data de inicio do contrato é a correta neste campo
                if self.origem.observacoes_vinculo_anterior:
                    SucessaoVinc.observacao.valor = self.origem.observacoes_vinculo_anterior
                S2200.evento.vinculo.sucessaoVinc.append(SucessaoVinc)

            # Gera
            data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            dh_transmissao = datetime.now().strftime('%Y%m%d%H%M%S')
            S2200.gera_id_evento(dh_transmissao)
            processador = pysped.ProcessadorESocial()

            processador.certificado.arquivo = arquivo.name
            processador.certificado.senha = self.company_id.nfe_a1_password
            processador.ambiente = int(self.ambiente)

            # Define a Inscrição do Processador
            processador.tpInsc = '1'
            processador.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)

            # Criar registro do Lote
            vals = {
                'tipo': 'esocial',
                'ambiente': self.ambiente,
                'transmissao_ids': [(4, self.id)],
                'data_hora_transmissao': data_hora_transmissao,
            }

            lote_id = self.env['sped.lote'].create(vals)
            self.lote_ids = [(4, lote_id.id)]
            self.data_hora_transmissao = data_hora_transmissao

            # Transmite
            processo = processador.enviar_lote(lista_eventos=[S2200], grupo='2')
            envio_xml = processo.envio.envioLoteEventos.eventos[0].xml
            envio_xml_nome = S2200.evento.Id.valor + '-S2200-env.xml'
            retorno_xml = processo.resposta.xml
            retorno_xml_nome = S2200.evento.Id.valor + '-S2200-ret.xml'

        # Registro S-2299 - Informações do Desligamento do Contrato de trabalho
        if self.registro == 'S-2299':
            data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            vals = {
                'tipo': 'esocial',
                'company_id': self.company_id.id,
                'ambiente': self.ambiente,
                'transmissao_ids': [(4, self.id)],
                'data_hora_transmissao': data_hora_transmissao,
            }

            lote_id = self.env['sped.lote'].create(vals)
            self.lote_ids = [(4, lote_id.id)]

            # Transmite
            lote_id.transmitir()

        # Registro R-1000 - Informações do Contribuinte (EFD-REINF)
        if self.registro == 'R-1000':

            # Cria o registro
            R1000 = pysped.efdreinf.leiaute.R1000_1()

            # Popula ideEvento
            R1000.evento.ideEvento.tpAmb.valor = self.ambiente
            R1000.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
            R1000.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0
            if self.limpar_db:
                R1000.evento.ideEvento.verProc.valor = 'RemoverContribuinte'

            # Popula ideContri (Dados do Contribuinte)
            R1000.evento.ideContri.tpInsc.valor = '1'
            R1000.evento.ideContri.nrInsc.valor = limpa_formatacao(self.origem.cnpj_cpf)[0:8]

            # Popula infoContri
            R1000.evento.infoContri.operacao = 'I'
            R1000.evento.infoContri.idePeriodo.iniValid.valor = self.origem.periodo_id.code[3:7] + '-' + self.origem.periodo_id.code[0:2]

            # Popula infoContri.InfoCadastro
            R1000.evento.infoContri.infoCadastro.classTrib.valor = self.origem.classificacao_tributaria_id.codigo
            if self.limpar_db:
                R1000.evento.infoContri.infoCadastro.classTrib.valor = '00'

            R1000.evento.infoContri.infoCadastro.indEscrituracao.valor = self.origem.ind_escrituracao
            R1000.evento.infoContri.infoCadastro.indDesoneracao.valor = self.origem.ind_desoneracao
            R1000.evento.infoContri.infoCadastro.indAcordoIsenMulta.valor = self.origem.ind_acordoisenmulta
            R1000.evento.infoContri.infoCadastro.indSitPJ.valor = self.origem.ind_sitpj
            R1000.evento.infoContri.infoCadastro.contato.nmCtt.valor = self.origem.nmctt
            R1000.evento.infoContri.infoCadastro.contato.cpfCtt.valor = self.origem.cpfctt
            R1000.evento.infoContri.infoCadastro.contato.foneFixo.valor = self.origem.cttfonefixo
            if self.origem.cttfonecel:
                R1000.evento.infoContri.infoCadastro.contato.foneCel.valor = self.origem.cttfonecel
            if self.origem.cttemail:
                R1000.evento.infoContri.infoCadastro.contato.email.valor = self.origem.cttemail

            # # Criar registro do Lote
            # vals = {
            #     'tipo': 'efdreinf',
            #     'company_id': self.company_id.id,
            #     'ambiente': self.ambiente,
            #     'transmissao_ids': [(4, self.id)],
            #     # 'data_hora_transmissao': data_hora_transmissao,
            # }
            #
            # lote_id = self.env['sped.lote'].create(vals)
            # self.lote_ids = [(4, lote_id.id)]

            # # Transmite
            # lote_id.transmitir()

            # Gera
            data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            dh_transmissao = datetime.now().strftime('%Y%m%d%H%M%S')
            R1000.gera_id_evento(dh_transmissao)
            processador = pysped.ProcessadorEFDReinf()

            processador.certificado.arquivo = arquivo.name
            processador.certificado.senha = self.company_id.nfe_a1_password
            processador.ambiente = int(self.ambiente)

            # Criar registro do Lote
            vals = {
                'tipo': 'efdreinf',
                'ambiente': self.ambiente,
                'transmissao_ids': [(4, self.id)],
                'data_hora_transmissao': data_hora_transmissao,
            }

            lote_id = self.env['sped.lote'].create(vals)
            self.lote_ids = [(4, lote_id.id)]
            self.data_hora_transmissao = data_hora_transmissao

            # Transmite
            processo = processador.enviar_lote([R1000])
            envio_xml = processo.envio.envioLoteEventos.eventos[0].xml
            envio_xml_nome = R1000.evento.Id.valor + '-R1000-env.xml'
            retorno_xml = processo.resposta.retornoEventos[0].xml
            retorno_xml_nome = R1000.evento.Id.valor + '-R1000-ret.xml'

        # Registro R-2010 - Retenção Contribuição Previdenciária - Serviços Tomados (EFD-REINF)
        elif self.registro == 'R-2010':

            # Calcula o Período de Apuração no formato YYYY-MM
            periodo = self.origem.efdreinf_id.periodo_id.code[3:7] + '-' + self.origem.efdreinf_id.periodo_id.code[0:2]

            # Cria o registro
            R2010 = pysped.efdreinf.leiaute.R2010_1()

            # Popula ideEvento
            R2010.evento.ideEvento.tpAmb.valor = self.ambiente
            R2010.evento.ideEvento.indRetif.valor = '1'
            R2010.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
            R2010.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0
            R2010.evento.ideEvento.perApur.valor = periodo

            # Popula ideContri (Dados do Contribuinte)
            R2010.evento.ideContri.tpInsc.valor = '1'
            R2010.evento.ideContri.nrInsc.valor = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

            # Popula infoServTom (Informações do Tomador)
            R2010.evento.infoServTom.ideEstabObra.tpInscEstab.valor = '1'
            R2010.evento.infoServTom.ideEstabObra.nrInscEstab.valor = limpa_formatacao(self.origem.estabelecimento_id.cnpj_cpf)
            R2010.evento.infoServTom.ideEstabObra.indObra.valor = '0'
            R2010.evento.infoServTom.ideEstabObra.idePrestServ.cnpjPrestador.valor = limpa_formatacao(self.origem.prestador_id.cnpj_cpf)
            R2010.evento.infoServTom.ideEstabObra.idePrestServ.vlrTotalBruto.valor = formata_valor(self.origem.vr_total_bruto)
            R2010.evento.infoServTom.ideEstabObra.idePrestServ.vlrTotalBaseRet.valor = formata_valor(self.origem.vr_total_base_retencao)
            R2010.evento.infoServTom.ideEstabObra.idePrestServ.vlrTotalRetPrinc.valor = formata_valor(self.origem.vr_total_ret_princ)
            if self.origem.vr_total_ret_adic:
                R2010.evento.infoServTom.ideEstabObra.idePrestServ.vlrTotalRetAdic.valor = formata_valor(self.origem.vr_total_ret_adic)
            if self.origem.vr_total_nret_princ:
                R2010.evento.infoServTom.ideEstabObra.idePrestServ.vlrTotalNRetPrinc.valor = formata_valor(self.origem.vr_total_nret_princ)
            if self.origem.vr_total_nret_adic:
                R2010.evento.infoServTom.ideEstabObra.idePrestServ.vlrTotalNRetAdic.valor = formata_valor(self.origem.vr_total_nret_adic)
            R2010.evento.infoServTom.ideEstabObra.idePrestServ.indCPRB.valor = '1' if self.origem.ind_cprb else '0'

            # Popula nfs
            for nfs in self.origem.nfs_ids:
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
                    R2010_infoTpServ.vlrBaseRet.valor = formata_valor(item.vr_base_ret)
                    R2010_infoTpServ.vlrRetencao.valor = formata_valor(item.vr_retencao)
                    if item.vr_ret_sub:
                        R2010_infoTpServ.vlrRetSub.valor = formata_valor(item.vr_ret_sub)
                    if item.vr_nret_princ:
                        R2010_infoTpServ.vlrNRetPrinc.valor = formata_valor(item.vr_nret_princ)
                    if item.vr_servicos_15:
                        R2010_infoTpServ.vlrServicos15.valor = formata_valor(item.vr_servicos_15)
                    if item.vr_servicos_20:
                        R2010_infoTpServ.vlrServicos20.valor = formata_valor(item.vr_servicos_20)
                    if item.vr_servicos_25:
                        R2010_infoTpServ.vlrServicos25.valor = formata_valor(item.vr_servicos_25)
                    if item.vr_adicional:
                        R2010_infoTpServ.vlrAdicional.valor = formata_valor(item.vr_adicional)
                    if item.vr_nret_adic:
                        R2010_infoTpServ.vlrNRetAdic.valor = formata_valor(item.vr_nret_adic)

                    # Adiciona infoTpServ em nfs
                    R2010_nfs.infoTpServ.append(R2010_infoTpServ)

                # Adiciona nfs em idePrestServ
                R2010.evento.infoServTom.ideEstabObra.idePrestServ.nfs.append(R2010_nfs)

            # Gera
            data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            dh_transmissao = datetime.now().strftime('%Y%m%d%H%M%S')
            R2010.gera_id_evento(dh_transmissao)
            processador = pysped.ProcessadorEFDReinf()

            processador.certificado.arquivo = arquivo.name
            processador.certificado.senha = self.company_id.nfe_a1_password
            processador.ambiente = int(self.ambiente)

            # Criar registro do Lote
            vals = {
                'tipo': 'efdreinf',
                'ambiente': self.ambiente,
                'transmissao_ids': [(4, self.id)],
                'data_hora_transmissao': data_hora_transmissao,
            }

            lote_id = self.env['sped.lote'].create(vals)
            self.lote_ids = [(4, lote_id.id)]
            self.data_hora_transmissao = data_hora_transmissao

            # Transmite
            processo = processador.enviar_lote([R2010])
            envio_xml = processo.envio.envioLoteEventos.eventos[0].xml
            envio_xml_nome = R2010.evento.Id.valor + '-R2010-env.xml'
            retorno_xml = processo.resposta.retornoEventos[0].xml
            retorno_xml_nome = R2010.evento.Id.valor + '-R2010-ret.xml'

        # Registro R-2099 - Fechamento de Eventos Periódicos
        elif self.registro == 'R-2099':

            # Calcula o Período de Apuração no formato YYYY-MM
            periodo = self.origem.periodo_id.code[3:7] + '-' + self.origem.periodo_id.code[0:2]

            # Cria o registro
            R2099 = pysped.efdreinf.leiaute.R2099_1()

            # Popula ideEvento
            R2099.evento.ideEvento.perApur.valor = periodo
            R2099.evento.ideEvento.tpAmb.valor = self.ambiente
            R2099.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
            R2099.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

            # Popula ideContri (Dados do Contribuinte)
            R2099.evento.ideContri.tpInsc.valor = '1'
            R2099.evento.ideContri.nrInsc.valor = limpa_formatacao(self.origem.company_id.cnpj_cpf)[0:8]

            # Popula ideRespInf
            R2099.evento.ideRespInf.nmResp.valor = self.origem.company_id.nmctt
            R2099.evento.ideRespInf.cpfResp.valor = self.origem.company_id.cpfctt
            if self.origem.company_id.cttfonefixo:
                R2099.evento.ideRespInf.telefone.valor = self.origem.company_id.cttfonefixo
            if self.origem.company_id.cttemail:
                R2099.evento.ideRespInf.email.valor = self.origem.company_id.cttemail

            # Popula infoFech
            R2099.evento.infoFech.evtServTm.valor = 'S' if self.origem.evt_serv_tm else 'N'
            R2099.evento.infoFech.evtServPr.valor = 'S' if self.origem.evt_serv_pr else 'N'
            R2099.evento.infoFech.evtAssDespRec.valor = 'S' if self.origem.evt_ass_desp_rec else 'N'
            R2099.evento.infoFech.evtAssDespRep.valor = 'S' if self.origem.evt_ass_desp_rep else 'N'
            R2099.evento.infoFech.evtComProd.valor = 'S' if self.origem.evt_com_prod else 'N'
            R2099.evento.infoFech.evtCPRB.valor = 'S' if self.origem.evt_cprb else 'N'
            R2099.evento.infoFech.evtPgtos.valor = 'S' if self.origem.evt_pgtos else 'N'
            if self.origem.comp_sem_movto_id:

                # Calcula o Período Inicial sem Movimento (se necessário)
                comp_sem_movto = self.origem.comp_sem_movto_id.code[3:7] + '-' + self.origem.comp_sem_movto_id.code[0:2]
                R2099.evento.infoFech.compSemMovto.valor = comp_sem_movto

            # Gera
            data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            dh_transmissao = datetime.now().strftime('%Y%m%d%H%M%S')
            R2099.gera_id_evento(dh_transmissao)
            processador = pysped.ProcessadorEFDReinf()
            processador.certificado.arquivo = arquivo.name
            processador.certificado.senha = self.company_id.nfe_a1_password
            processador.ambiente = int(self.ambiente)

            # Criar registro do Lote
            vals = {
                'tipo': 'efdreinf',
                'ambiente': self.ambiente,
                'transmissao_ids': [(4, self.id)],
                'data_hora_transmissao': data_hora_transmissao,
            }

            lote_id = self.env['sped.lote'].create(vals)
            self.lote_ids = [(4, lote_id.id)]
            self.data_hora_transmissao = data_hora_transmissao

            # Transmite
            processo = processador.enviar_lote([R2099])
            envio_xml = processo.envio.envioLoteEventos.eventos[0].xml
            envio_xml_nome = R2099.evento.Id.valor + '-R2099-env.xml'
            retorno_xml = processo.resposta.retornoEventos[0].xml
            retorno_xml_nome = R2099.evento.Id.valor + '-R2099-ret.xml'

        if self.registro not in ['S-1000']:
            # Processa retorno do EFD/Reinf
            if self.tipo == 'efdreinf':
                if processo:

                    # Limpar ocorrências
                    for ocorrencia in self.ocorrencia_ids:
                        ocorrencia.unlink()

                    if processo.resposta.ocorrencias:
                        for ocorrencia in processo.resposta.ocorrencias:
                            vals = {
                                'tipo': ocorrencia.tipo.valor,
                                'local': ocorrencia.localizacaoErroAviso.valor,
                                'codigo': ocorrencia.codigo.valor,
                                'descricao': ocorrencia.descricao.valor,
                            }
                            self.ocorrencia_ids.create(vals)

                    for evento in processo.resposta.retornoEventos:
                        if self.limpar_db:
                            self.cd_retorno = False
                            self.desc_retorno = False
                        else:
                            self.cd_retorno = evento.evtTotal.ideRecRetorno.ideStatus.cdRetorno.valor
                            self.desc_retorno = evento.evtTotal.ideRecRetorno.ideStatus.descRetorno.valor
                            self.recibo = evento.evtTotal.infoTotal.nrRecArqBase.valor
                            self.protocolo = evento.evtTotal.infoRecEv.nrProtEntr.valor

                        if evento.evtTotal.ideRecRetorno.ideStatus.regOcorrs:
                            for ocorrencia in evento.evtTotal.ideRecRetorno.ideStatus.regOcorrs:
                                vals = {
                                    'tipo': ocorrencia.tpOcorr.valor,
                                    'local': ocorrencia.localErroAviso.valor,
                                    'codigo': ocorrencia.codResp.valor,
                                    'descricao': ocorrencia.dscResp.valor,
                                }
                                self.ocorrencia_ids.create(vals)

                    if self.cd_retorno == '0':
                        self.situacao = '4'
                    elif self.cd_retorno == '1':
                        self.situacao = '3'
                    elif self.cd_retorno == '2':
                        self.situacao = '2'
                    else:
                        self.situacao = '1'

            # Popula retorno do e-Social
            elif self.tipo == 'esocial':
                if processo:

                    # Limpar ocorrências
                    for ocorrencia in self.ocorrencia_ids:
                        ocorrencia.unlink()

                    if processo.resposta.retornoEnvioLoteEventos.status.ocorrencias:
                        for ocorrencia in processo.resposta.retornoEnvioLoteEventos.status.ocorrencias:
                            vals = {
                                'transmissao_id': self.id,
                                'codigo': ocorrencia.codigo.valor,
                                'descricao': ocorrencia.descricao.valor,
                                'tipo': ocorrencia.tipo.valor,
                                'local': ocorrencia.localizacao.valor,
                            }
                            self.ocorrencia_ids.create(vals)
                        self.situacao = '3'
                    else:
                        self.situacao = '2'

                    if self.limpar_db:
                        self.cd_retorno = False
                        self.desc_retorno = False
                        self.situacao = '1'
                    else:
                        self.cd_retorno = processo.resposta.retornoEnvioLoteEventos.status.cdResposta.valor
                        self.desc_retorno = processo.resposta.retornoEnvioLoteEventos.status.descResposta.valor
                        self.protocolo = processo.resposta.retornoEnvioLoteEventos.dadosRecepcaoLote.protocoloEnvio.valor

                    # if self.cd_retorno == '0':
                    #     self.situacao = '4'
                    # elif self.cd_retorno == '1':
                    #     self.situacao = '3'
                    # elif self.cd_retorno == '201':
                    #     self.situacao = '2'
                    # else:
                    #     self.situacao = '1'

            # Popula dados de retorno
            data_hora_retorno = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            lote_id.data_hora_retorno = data_hora_retorno
            lote_id.situacao = '3' if self.situacao == 3 else '4'
            self.data_hora_retorno = data_hora_retorno

            if not self.protocolo:
                self.situacao == '1'

            # Grava anexos
            if envio_xml:
                if self.envio_xml_id:
                    envio = self.envio_xml_id
                    self.envio_xml_id = False
                    envio.unlink()
                anexo_id = self._grava_anexo(envio_xml_nome, envio_xml)
                self.envio_xml_id = anexo_id
            if retorno_xml:
                if self.retorno_xml_id:
                    retorno = self.retorno_xml_id
                    self.retorno_xml_id = False
                    retorno.unlink()
                anexo_id = self._grava_anexo(retorno_xml_nome, retorno_xml)
                self.retorno_xml_id = anexo_id

    @api.multi
    def consulta_esocial(self):
        self.ensure_one()

        if not self.protocolo:
            raise ValidationError("Protocolo não existe ! - Impossível consultar")

        # Gravar certificado em arquivo temporario
        arquivo = tempfile.NamedTemporaryFile()
        arquivo.seek(0)
        arquivo.write(
            base64.decodestring(self.company_id.nfe_a1_file)
        )
        arquivo.flush()

        processador = pysped.ProcessadorESocial()
        processador.certificado.arquivo = arquivo.name
        processador.certificado.senha = self.company_id.nfe_a1_password
        processador.ambiente = int(self.ambiente)

        # Consulta
        processo = processador.consultar_lote(self.protocolo)

        # Transmite
        consulta_xml = processo.resposta.xml
        consulta_xml_nome = 'Consulta_xml_retorno.xml'

        # Pega o status do Evento transmitido
        if len(processo.resposta.lista_eventos) >= 1:

            self.cd_retorno = processo.resposta.lista_eventos[0].codigo_retorno
            self.desc_retorno = processo.resposta.lista_eventos[0].descricao_retorno

            # Limpar ocorrências
            for ocorrencia in self.ocorrencia_ids:
                ocorrencia.unlink()

            # Atualiza o registro com o resultado
            if self.cd_retorno == '201':
                self.situacao = '4'

                if self.fechamento_xml_id:
                    fechamento = self.fechamento_xml_id
                    self.fechamento_xml_id = False
                    fechamento.unlink()
                fechamento_xml = processo.resposta.lista_eventos[0].xml
                fechamento_xml_nome = processo.resposta.lista_eventos[0].Id.valor + '-' + self.registro + '-consulta.xml'
                anexo_id = self._grava_anexo(fechamento_xml_nome, fechamento_xml)
                self.fechamento_xml_id = anexo_id
            else:
                self.situacao = '3'
                if processo.resposta.lista_eventos[0].lista_ocorrencias:
                    for ocorrencia in processo.resposta.lista_eventos[0].lista_ocorrencias:
                        vals = {
                            'transmissao_id': self.id,
                            'tipo': ocorrencia['tipo'],
                            'codigo': ocorrencia['codigo'],
                            'descricao': ocorrencia['descricao'],
                            'local': ocorrencia['localizacao'],
                        }
                        self.ocorrencia_ids.create(vals)

        # Grava anexos
        if consulta_xml:
            if self.consulta_xml_id:
                consulta = self.consulta_xml_id
                self.consulta_xml_id = False
                consulta.unlink()
            anexo_id = self._grava_anexo(consulta_xml_nome, consulta_xml)
            self.consulta_xml_id = anexo_id

    @api.multi
    def consulta_fechamento(self):
        self.ensure_one()

        if not self.protocolo:
            raise ValidationError("Protocolo não existe ! - Impossível consultar fechamento")

        # Gravar certificado em arquivo temporario
        arquivo = tempfile.NamedTemporaryFile()
        arquivo.seek(0)
        arquivo.write(
            base64.decodestring(self.company_id.nfe_a1_file)
        )
        arquivo.flush()

        processador = pysped.ProcessadorEFDReinf()

        processador.certificado.arquivo = arquivo.name
        processador.certificado.senha = self.company_id.nfe_a1_password
        processador.ambiente = int(self.ambiente)

        # Carrega os dados de consulta
        processador.tipoInscricaoContribuinte = '1'
        processador.numeroInscricaoContribuinte = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        processador.numeroProtocoloFechamento = self.protocolo

        # Consulta
        processo = processador.consultar_fechamento(ambiente=int(self.ambiente))
        self.cd_retorno = processo.resposta.cdResposta
        self.desc_retorno = processo.resposta.descResposta

        # Limpar ocorrências
        for ocorrencia in self.ocorrencia_ids:
            ocorrencia.unlink()

        # Atualiza o registro com o resultado
        if processo.resposta.cdResposta == '0':
            self.situacao = '4'

            if self.fechamento_xml_id:
                fechamento = self.fechamento_xml_id
                self.fechamento_xml_id = False
                fechamento.unlink()

            # Popula o registro EFD/Reinf como sucesso
            if self.origem.situacao != '2':
                self.origem.situacao = '3'

        else:
            for ocorrencia in processo.resposta.ocorrencias:
                vals = {
                    'transmissao_id': self.id,
                    'tipo': ocorrencia.tpOcorr.valor,
                    'local': ocorrencia.localErroAviso.valor,
                    'codigo': ocorrencia.codResp.valor,
                    'descricao': ocorrencia.dscResp.valor,
                }
                self.ocorrencia_ids.create(vals)

        # fechamento_xml = processo.resposta.xml
        fechamento_xml = processo.resposta.original
        fechamento_xml_nome = processo.resposta.evtTotalContrib.Id.valor + '-R2099-fechamento.xml'
        anexo_id = self._grava_anexo(fechamento_xml_nome, fechamento_xml)
        self.fechamento_xml_id = anexo_id


    # Este método será usado pelo lote na transmissão
    @api.multi
    def calcula_xml(self, sequencia=False):
        self.ensure_one()

        # Gera o XML usando o popula_xml da tabela intermediária
        registro = self.origem_intermediario.popula_xml(ambiente=self.ambiente, operacao=self.operacao)

        # Gera o ID do evento
        agora = datetime.now()
        data_hora_transmissao = agora.strftime('%Y-%m-%d %H:%M:%S')
        registro.gera_id_evento(agora.strftime('%Y%m%d%H%M%S'), sequencia)
        self.data_hora_transmissao = data_hora_transmissao

        # Grava o ID gerado
        self.id_evento = registro.evento.Id.valor

        # Grava o XML gerado
        if self.envio_xml_id:
            envio = self.envio_xml_id
            envio.envio_xml_id = False
            envio.unlink()
        envio_xml = registro.evento.xml
        envio_xml_nome = self.id_evento + '-envio.xml'
        anexo_id = self._grava_anexo(envio_xml_nome, envio_xml)
        self.envio_xml_id = anexo_id

        # Retorno XML preenchido
        return registro
