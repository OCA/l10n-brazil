# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
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

class SpedTransmissao(models.Model):
    _name = 'sped.transmissao'
    _inherit = []
    _description = 'Transmissão de registros SPED'
    _rec_name = 'registro'
    _order = "data_hora_origem DESC, situacao"

    tipo = fields.Selection(
        string='Tipo',
        selection=[
            ('efdreinf', 'EFD-Reinf'),
            ('esocial', 'e-Social'),
        ],
    )
    limpar_db = fields.Boolean(
        string='Limpar DB',
    )
    codigo = fields.Char(
        string='Código',
        default=lambda self: self.env['ir.sequence'].next_by_code('sped.transmissao'),
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
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
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
        comodel_name='sped.transmissao.lote',
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
        ondelete='restrict',
        copy=False,
    )
    envio_xml = fields.Text(
        string='XML',
        compute='_compute_arquivo_xml',
    )
    retorno_xml_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de retorno',
        ondelete='restrict',
        copy=False,
    )
    retorno_xml = fields.Text(
        string='XML',
        compute='_compute_arquivo_xml',
    )
    consulta_xml_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de consulta',
        ondelete='restrict',
        copy=False,
    )
    consulta_xml = fields.Text(
        string='XML',
        compute='_compute_arquivo_xml',
    )
    fechamento_xml_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de Fechamento',
        ondelete='restrict',
        copy=False,
    )
    fechamento_xml = fields.Text(
        string='XML',
        compute='_compute_arquivo_xml',
    )
    recibo = fields.Char(
        string='Recibo',
        size=60,
    )
    protocolo = fields.Char(
        string='Protocolo',
        size=60,
    )

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
            super(SpedTransmissao, registro).unlink()

        return True

    @api.multi
    def limpa_db(self):
        self.ensure_one()
        if self.ambiente == '1':
            raise ValidationError("Ambiente de Produção não suporta Limpeza de Banco de Dados !")

        self.limpar_db = True
        self.gera_xml()
        self.recibo = False
        self.protocolo = False
        self.limpar_db = False

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

            # Cria o registro
            S1000 = pysped.esocial.leiaute.S1000_2()

            # Popula ideEvento
            S1000.tpInsc = '1'
            S1000.nrInsc = limpa_formatacao(self.origem.cnpj_cpf)[0:8]
            S1000.evento.ideEvento.tpAmb.valor = int(self.ambiente)
            S1000.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
            S1000.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

            # Popula ideEmpregador (Dados do Empregador)
            S1000.evento.ideEmpregador.tpInsc.valor = '1'
            S1000.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(self.origem.cnpj_cpf)[0:8]

            # Popula infoEmpregador
            S1000.evento.infoEmpregador.operacao = 'I'
            S1000.evento.infoEmpregador.idePeriodo.iniValid.valor = self.origem.esocial_periodo_id.code[3:7] + '-' + self.origem.esocial_periodo_id.code[0:2]

            # Popula infoEmpregador.InfoCadastro
            S1000.evento.infoEmpregador.infoCadastro.nmRazao.valor = self.origem.legal_name
            S1000.evento.infoEmpregador.infoCadastro.classTrib.valor = self.origem.classificacao_tributaria_id.codigo
            S1000.evento.infoEmpregador.infoCadastro.natJurid.valor = limpa_formatacao(self.origem.natureza_juridica_id.codigo)
            S1000.evento.infoEmpregador.infoCadastro.indCoop.valor = self.origem.ind_coop
            S1000.evento.infoEmpregador.infoCadastro.indConstr.valor = self.origem.ind_constr
            S1000.evento.infoEmpregador.infoCadastro.indDesFolha.valor = self.origem.ind_desoneracao
            S1000.evento.infoEmpregador.infoCadastro.indOptRegEletron.valor = self.origem.ind_opt_reg_eletron
            S1000.evento.infoEmpregador.infoCadastro.indEntEd.valor = self.origem.ind_ent_ed
            S1000.evento.infoEmpregador.infoCadastro.indEtt.valor = self.origem.ind_ett
            if self.origem.nr_reg_ett:
                S1000.evento.infoEmpregador.infoCadastro.nrRegEtt.valor = self.origem.nr_reg_ett
            if self.limpar_db:
                S1000.evento.infoEmpregador.infoCadastro.nmRazao.valor = 'RemoverEmpregadorDaBaseDeDadosDaProducaoRestrita'
                S1000.evento.infoEmpregador.infoCadastro.classTrib.valor = '00'

            # Popula infoEmpregador.Infocadastro.contato
            S1000.evento.infoEmpregador.infoCadastro.contato.nmCtt.valor = self.origem.esocial_nm_ctt
            S1000.evento.infoEmpregador.infoCadastro.contato.cpfCtt.valor = self.origem.esocial_cpf_ctt
            S1000.evento.infoEmpregador.infoCadastro.contato.foneFixo.valor = limpa_formatacao(self.origem.esocial_fone_fixo)
            if self.origem.esocial_fone_cel:
                S1000.evento.infoEmpregador.infoCadastro.contato.foneCel.valor = limpa_formatacao(self.origem.esocial_fone_cel)
            if self.origem.esocial_email:
                S1000.evento.infoEmpregador.infoCadastro.contato.email.valor = self.origem.esocial_email

            # Popula infoEmpregador.infoCadastro.infoComplementares.situacaoPJ
            S1000.evento.infoEmpregador.infoCadastro.indSitPJ.valor = self.origem.ind_sitpj

            # Gera
            data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            dh_transmissao = datetime.now().strftime('%Y%m%d%H%M%S')
            S1000.gera_id_evento(dh_transmissao)
            processador = pysped.ProcessadorESocial()

            processador.certificado.arquivo = arquivo.name
            processador.certificado.senha = self.company_id.nfe_a1_password
            processador.ambiente = int(self.ambiente)

            # Define a Inscrição do Processador
            processador.tpInsc = '1'
            processador.nrInsc = limpa_formatacao(self.origem.cnpj_cpf)

            # Criar registro do Lote
            vals = {
                'tipo': 'esocial',
                'ambiente': self.ambiente,
                'transmissao_ids': [(4, self.id)],
                'data_hora_transmissao': data_hora_transmissao,
                'xml_transmissao': False,
            }

            lote_id = self.env['sped.transmissao.lote'].create(vals)
            self.lote_ids = [(4, lote_id.id)]
            self.data_hora_transmissao = data_hora_transmissao

            # Transmite
            processo = processador.enviar_lote([S1000])
            envio_xml = processo.envio.envioLoteEventos.eventos[0].xml
            envio_xml_nome = S1000.evento.Id.valor + '-S1000-env.xml'
            retorno_xml = processo.resposta.xml
            retorno_xml_nome = S1000.evento.Id.valor + '-S1000-ret.xml'

        # Registro S-1005 - Tabela de Estabelecimentos, Obras ou Unidades de Órgãos Públicos
        elif self.registro == 'S-1005':

            # Cria o registro
            S1005 = pysped.esocial.leiaute.S1005_2()

            # Popula ideEvento
            S1005.tpInsc = '1'
            S1005.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
            S1005.evento.ideEvento.tpAmb.valor = int(self.ambiente)
            S1005.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
            S1005.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

            # Popula ideEmpregador (Dados do Empregador)
            S1005.evento.ideEmpregador.tpInsc.valor = '1'
            S1005.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

            # Popula infoEstab (Informações do Estabelecimentou o Obra)
            S1005.evento.infoEstab.operacao = 'I'  # Inclusão TODO lidar com alteração e exclusão
            S1005.evento.infoEstab.ideEstab.tpInsc.valor = '1'
            S1005.evento.infoEstab.ideEstab.nrInsc.valor = limpa_formatacao(self.origem.estabelecimento_id.cnpj_cpf)
            S1005.evento.infoEstab.ideEstab.iniValid.valor = self.origem.esocial_id.periodo_id.code[3:7] + '-' + self.origem.esocial_id.periodo_id.code[0:2]
            S1005.evento.infoEstab.dadosEstab.cnaePrep.valor = limpa_formatacao(self.origem.estabelecimento_id.cnae_main_id.code)

            # Localiza o percentual de RAT e FAP para esta empresa neste período
            ano = self.origem.esocial_id.periodo_id.fiscalyear_id.code
            domain = [
                ('company_id', '=', self.origem.estabelecimento_id.id),
                ('year', '=', int(ano)),
            ]
            rat_fap = self.env['l10n_br.hr.rat.fap'].search(domain)
            if not rat_fap:
                raise Exception("Tabela de RAT/FAP não encontrada para este período")

            # Popula aligGilRat
            S1005.evento.infoEstab.dadosEstab.aliqGilrat.aliqRat.valor = int(rat_fap.rat_rate)
            S1005.evento.infoEstab.dadosEstab.aliqGilrat.fap.valor = formata_valor(rat_fap.fap_rate)
            S1005.evento.infoEstab.dadosEstab.aliqGilrat.aliqRatAjust.valor = formata_valor(rat_fap.rat_rate * rat_fap.fap_rate)
            
            # Popula infoCaepf
            if self.origem.estabelecimento_id.tp_caepf:
                S1005.evento.infoEstab.dadosEstab.infoCaepf.tpCaepf.valor = int(self.origem.estabelecimento_id.tp_caepf)

            # Popula infoTrab
            S1005.evento.infoEstab.dadosEstab.infoTrab.regPt.valor = self.origem.estabelecimento_id.reg_pt

            # Popula infoApr
            S1005.evento.infoEstab.dadosEstab.infoTrab.infoApr.contApr.valor = self.origem.estabelecimento_id.cont_apr
            S1005.evento.infoEstab.dadosEstab.infoTrab.infoApr.contEntEd.valor = self.origem.estabelecimento_id.cont_ent_ed

            # Popula infoEntEduc
            for entidade in self.origem.estabelecimento_id.info_ent_educ_ids:
                info_ent_educ = pysped.esocial.leiaute.InfoEntEduc_2()
                info_ent_educ.nrInsc = limpa_formatacao(entidade.cnpj_cpf)
                S1005.evento.infoEstab.dadosEstab.infoTrab.infoApr.infoEntEduc.append(info_ent_educ)

            # Popula infoPCD
            if self.origem.estabelecimento_id.cont_pcd:
                S1005.evento.infoEstab.dadosEstab.infoTrab.infoPCD.contPCD = self.origem.estabelecimento_id.cont_pcd

            # Gera
            data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            dh_transmissao = datetime.now().strftime('%Y%m%d%H%M%S')
            S1005.gera_id_evento(dh_transmissao)
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
                'xml_transmissao': False,
            }

            lote_id = self.env['sped.transmissao.lote'].create(vals)
            self.lote_ids = [(4, lote_id.id)]
            self.data_hora_transmissao = data_hora_transmissao

            # Transmite
            processo = processador.enviar_lote([S1005])
            envio_xml = processo.envio.envioLoteEventos.eventos[0].xml
            envio_xml_nome = S1005.evento.Id.valor + '-S1005-env.xml'
            # retorno_xml = processo.resposta.retornoEventos[0].xml
            retorno_xml = processo.resposta.xml
            retorno_xml_nome = S1005.evento.Id.valor + '-S1005-ret.xml'

        # Registro S-1010 - Tabela de Rubricas
        elif self.registro == 'S-1010':

            # Cria o registro
            S1010 = pysped.esocial.leiaute.S1010_2()

            # Popula ideEvento
            S1010.tpInsc = '1'
            S1010.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
            S1010.evento.ideEvento.tpAmb.valor = int(self.ambiente)
            S1010.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
            S1010.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

            # Popula ideEmpregador (Dados do Empregador)
            S1010.evento.ideEmpregador.tpInsc.valor = '1'
            S1010.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

            # Popula infoRubrica (Informações da Rubrica)
            S1010.evento.infoRubrica.operacao = 'I'  # Inclusão TODO lidar com alteração e exclusão
            S1010.evento.infoRubrica.ideRubrica.codRubr.valor = self.origem.rubrica_id.codigo
            S1010.evento.infoRubrica.ideRubrica.ideTabRubr.valor = self.origem.rubrica_id.identificador

            # Início da Validade neste evento
            S1010.evento.infoRubrica.ideRubrica.iniValid.valor = \
                self.origem.rubrica_id.ini_valid.code[3:7] + '-' + self.origem.rubrica_id.ini_valid.code[0:2]

            # Preencher dadosRubrica
            S1010.evento.infoRubrica.dadosRubrica.dscRubr.valor = self.origem.rubrica_id.name
            S1010.evento.infoRubrica.dadosRubrica.natRubr.valor = self.origem.rubrica_id.nat_rubr.codigo
            S1010.evento.infoRubrica.dadosRubrica.tpRubr.valor = self.origem.rubrica_id.tp_rubr
            S1010.evento.infoRubrica.dadosRubrica.codIncFGTS.valor = self.origem.rubrica_id.cod_inc_fgts
            S1010.evento.infoRubrica.dadosRubrica.codIncSIND.valor = self.origem.rubrica_id.cod_inc_sind

            # Preencher codIncCP
            if self.origem.rubrica_id.cod_inc_cp == '0':
                cod_inc_cp = self.origem.rubrica_id.cod_inc_cp_0
            elif self.origem.rubrica_id.cod_inc_cp == '1':
                cod_inc_cp = self.origem.rubrica_id.cod_inc_cp_1
            elif self.origem.rubrica_id.cod_inc_cp == '3':
                cod_inc_cp = self.origem.rubrica_id.cod_inc_cp_3
            elif self.origem.rubrica_id.cod_inc_cp == '5':
                cod_inc_cp = self.origem.rubrica_id.cod_inc_cp_5
            elif self.origem.rubrica_id.cod_inc_cp == '9':
                cod_inc_cp = self.origem.rubrica_id.cod_inc_cp_9
            S1010.evento.infoRubrica.dadosRubrica.codIncCP.valor = cod_inc_cp

            # Preencher codIncIRRF
            if self.origem.rubrica_id.cod_inc_irrf == '0':
                cod_inc_irrf = self.origem.rubrica_id.cod_inc_irrf_0
            elif self.origem.rubrica_id.cod_inc_irrf == '1':
                cod_inc_irrf = self.origem.rubrica_id.cod_inc_irrf_1
            elif self.origem.rubrica_id.cod_inc_irrf == '3':
                cod_inc_irrf = self.origem.rubrica_id.cod_inc_irrf_3
            elif self.origem.rubrica_id.cod_inc_irrf == '4':
                cod_inc_irrf = self.origem.rubrica_id.cod_inc_irrf_4
            elif self.origem.rubrica_id.cod_inc_irrf == '7':
                cod_inc_irrf = self.origem.rubrica_id.cod_inc_irrf_7
            elif self.origem.rubrica_id.cod_inc_irrf == '8':
                cod_inc_irrf = self.origem.rubrica_id.cod_inc_irrf_8
            elif self.origem.rubrica_id.cod_inc_irrf == '9':
                cod_inc_irrf = self.origem.rubrica_id.cod_inc_irrf_9
            S1010.evento.infoRubrica.dadosRubrica.codIncIRRF.valor = cod_inc_irrf

            # Preencher observação
            if self.origem.rubrica_id.note:
                S1010.evento.infoRubrica.dadosRubrica.observacao.valor = self.origem.rubrica_id.note

            # Gera
            data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            dh_transmissao = datetime.now().strftime('%Y%m%d%H%M%S')
            S1010.gera_id_evento(dh_transmissao)
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
                'xml_transmissao': False,
            }

            lote_id = self.env['sped.transmissao.lote'].create(vals)
            self.lote_ids = [(4, lote_id.id)]
            self.data_hora_transmissao = data_hora_transmissao

            # Transmite
            processo = processador.enviar_lote([S1010])
            envio_xml = processo.envio.envioLoteEventos.eventos[0].xml
            envio_xml_nome = S1010.evento.Id.valor + '-S1010-env.xml'
            retorno_xml = processo.resposta.xml
            retorno_xml_nome = S1010.evento.Id.valor + '-S1010-ret.xml'

        # Registro S-1020 - Tabela de Lotações Tributárias
        elif self.registro == 'S-1020':

            # Cria o registro
            S1020 = pysped.esocial.leiaute.S1020_2()

            # Popula ideEvento
            S1020.tpInsc = '1'
            S1020.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
            S1020.evento.ideEvento.tpAmb.valor = int(self.ambiente)
            S1020.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
            S1020.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

            # Popula ideEmpregador (Dados do Empregador)
            S1020.evento.ideEmpregador.tpInsc.valor = '1'
            S1020.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

            # Popula infoLotacao (Informações do Lotação Tributária)
            S1020.evento.infoLotacao.operacao = 'I'  # Inclusão TODO lidar com alteração e exclusão
            S1020.evento.infoLotacao.ideLotacao.codLotacao.valor = self.origem.lotacao_id.cod_lotacao
            S1020.evento.infoLotacao.ideLotacao.iniValid.valor = self.origem.esocial_id.periodo_id.code[
                                                             3:7] + '-' + self.origem.esocial_id.periodo_id.code[0:2]

            # Popula dadosLotacao
            S1020.evento.infoLotacao.dadosLotacao.tpLotacao.valor = self.origem.lotacao_id.tp_lotacao_id.codigo
            if self.origem.lotacao_id.tp_insc_id:
                S1020.evento.infoLotacao.dadosLotacao.tpInsc.valor = self.origem.lotacao_id.tp_insc_id.codigo
            if self.origem.lotacao_id.nr_insc:
                S1020.evento.infoLotacao.dadosLotacao.nrInsc.valor = self.origem.lotacao_id.nr_insc

            # Popula fpasLotacao
            S1020.evento.infoLotacao.dadosLotacao.fpasLotacao.fpas.valor = self.origem.lotacao_id.fpas_id.codigo
            S1020.evento.infoLotacao.dadosLotacao.fpasLotacao.codTercs.valor = self.origem.lotacao_id.cod_tercs
            # S1020.evento.infoLotacao.dadosLotacao.fpasLotacao.codTercs.valor = self.origem.lotacao_id.cod_tercs_id.codigo

            # Gera
            data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            dh_transmissao = datetime.now().strftime('%Y%m%d%H%M%S')
            S1020.gera_id_evento(dh_transmissao)
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
                'xml_transmissao': False,
            }

            lote_id = self.env['sped.transmissao.lote'].create(vals)
            self.lote_ids = [(4, lote_id.id)]
            self.data_hora_transmissao = data_hora_transmissao

            # Transmite
            processo = processador.enviar_lote([S1020])
            envio_xml = processo.envio.envioLoteEventos.eventos[0].xml
            envio_xml_nome = S1020.evento.Id.valor + '-S1020-env.xml'
            retorno_xml = processo.resposta.xml
            retorno_xml_nome = S1020.evento.Id.valor + '-S1020-ret.xml'

        # Registro S-1030 - Tabela de Cargos/Empregos Públicos
        elif self.registro == 'S-1030':

            # Cria o registro
            S1030 = pysped.esocial.leiaute.S1030_2()

            # Popula ideEvento
            S1030.tpInsc = '1'
            S1030.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
            S1030.evento.ideEvento.tpAmb.valor = int(self.ambiente)
            S1030.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
            S1030.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

            # Popula ideEmpregador (Dados do Empregador)
            S1030.evento.ideEmpregador.tpInsc.valor = '1'
            S1030.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

            # Popula infoCargo (Informações da Rubrica)
            S1030.evento.infoCargo.operacao = 'I'  # Inclusão TODO lidar com alteração e exclusão
            S1030.evento.infoCargo.ideCargo.codCargo.valor = self.origem.cargo_id.codigo

            # Início da Validade neste evento
            S1030.evento.infoCargo.ideCargo.iniValid.valor = \
                self.origem.cargo_id.ini_valid.code[3:7] + '-' + self.origem.cargo_id.ini_valid.code[0:2]

            # Preencher dadosCargo
            S1030.evento.infoCargo.dadosCargo.nmCargo.valor = self.origem.cargo_id.name
            S1030.evento.infoCargo.dadosCargo.codCBO.valor = self.origem.cargo_id.cbo_id.code

            # Preencher dados de cargoPublico (se for o caso)
            if self.origem.cargo_id.cargo_publico:
                CargoPublico = pysped.esocial.leiaute.S1030_CargoPublico_2()

                CargoPublico.acumCargo.valor = self.origem.cargo_id.acum_cargo
                CargoPublico.contagemEsp.valor = self.origem.cargo_id.contagem_esp
                CargoPublico.dedicExcl.valor = self.origem.cargo_id.dedic_excl
                CargoPublico.nrLei.valor = self.origem.cargo_id.nr_lei
                CargoPublico.dtLei.valor = self.origem.cargo_id.dt_lei
                CargoPublico.sitCargo.valor = self.origem.cargo_id.sit_cargo

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
                'xml_transmissao': False,
            }

            lote_id = self.env['sped.transmissao.lote'].create(vals)
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
            S1050 = pysped.esocial.leiaute.S1050_2()

            # Popula ideEvento
            S1050.tpInsc = '1'
            S1050.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
            S1050.evento.ideEvento.tpAmb.valor = int(self.ambiente)
            S1050.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
            S1050.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

            # Popula ideEmpregador (Dados do Empregador)
            S1050.evento.ideEmpregador.tpInsc.valor = '1'
            S1050.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
                self.company_id.cnpj_cpf)[0:8]

            # Popula ideHorContratual
            S1050.evento.infoHorContratual.operacao = 'I'
            S1050.evento.infoHorContratual.ideHorContratual.codHorContrat.valor = self.origem.sped_esocial_turnos_trabalho_id.cod_hor_contrat
            # S1050.evento.infoHorContratual.ideHorContratual.iniValid.valor = self.origem.sped_esocial_turnos_trabalho_id.ini_valid
            S1050.evento.infoHorContratual.ideHorContratual.iniValid.valor = self.origem.sped_esocial_turnos_trabalho_id.ini_valid.code[3:7] + '-' + self.origem.sped_esocial_turnos_trbalho_id.ini_valid.code[0:2]
            if self.origem.sped_esocial_turnos_trabalho_id.fim_valid:
                # S1050.evento.infoHorContratual.ideHorContratual.fimValid.valor = self.origem.sped_esocial_turnos_trabalho_id.fim_valid
                S1050.evento.infoHorContratual.ideHorContratual.fimValid.valor = self.origem.sped_esocial_turnos_trabalho_id.fim_valid.code[3:7] + '-' + self.origem.sped_esocial_turnos_trbalho_id.fim_valid.code[0:2]

            # Popula dadosHorContratual
            S1050.evento.infoHorContratual.dadosHorContratual.hrEntr.valor = self.origem.sped_esocial_turnos_trabalho_id.hr_entr.replace(":", "")
            S1050.evento.infoHorContratual.dadosHorContratual.hrSaida.valor = self.origem.sped_esocial_turnos_trabalho_id.hr_saida.replace(":", "")
            S1050.evento.infoHorContratual.dadosHorContratual.durJornada.valor = self.origem.sped_esocial_turnos_trabalho_id.dur_jornada
            S1050.evento.infoHorContratual.dadosHorContratual.perHorFlexivel.valor = self.origem.sped_esocial_turnos_trabalho_id.per_hor_flexivel

            for intervalo in self.origem.sped_esocial_turnos_trabalho_id.horario_intervalo_ids:
                sped_intervalo = pysped.esocial.leiaute.HorarioIntervalo_2()
                sped_intervalo.tpInterv.valor = intervalo.tp_interv
                sped_intervalo.durInterv.valor = intervalo.dur_interv
                sped_intervalo.iniInterv.valor = intervalo.ini_interv
                sped_intervalo.termInterv.valor = intervalo.term_interv

                S1050.evento.infoHorContratual.dadosHorContratual.\
                    horarioIntervalo.append(sped_intervalo)
            # Gera
            data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            dh_transmissao = datetime.now().strftime('%Y%m%d%H%M%S')
            S1050.gera_id_evento(dh_transmissao)
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
                'xml_transmissao': False,
            }

            lote_id = self.env['sped.transmissao.lote'].create(vals)
            self.lote_ids = [(4, lote_id.id)]
            self.data_hora_transmissao = data_hora_transmissao

            # Transmite
            processo = processador.enviar_lote([S1050])
            envio_xml = processo.envio.envioLoteEventos.eventos[0].xml
            envio_xml_nome = S1050.evento.Id.valor + '-S1050-env.xml'
            retorno_xml = processo.resposta.xml
            retorno_xml_nome = S1050.evento.Id.valor + '-S1050-ret.xml'

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
            S2200.evento.trabalhador.nascimento.codMunic.valor = self.origem.employee_id.naturalidade.ibge_code or ''
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
            Brasil.tpLograd.valor = self.origem.employee_id.tp_lograd.codigo or ''
            Brasil.dscLograd.valor = self.origem.employee_id.address_home_id.street or ''
            Brasil.nrLograd.valor = self.origem.employee_id.address_home_id.number or ''
            Brasil.complemento.valor = self.origem.employee_id.address_home_id.street2 or ''
            Brasil.bairro.valor = self.origem.employee_id.address_home_id.district or ''
            Brasil.cep.valor = limpa_formatacao(self.origem.employee_id.address_home_id.zip) or ''
            Brasil.codMunic.valor = self.origem.employee_id.address_home_id.l10n_br_city_id.ibge_code
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
                InfoCeletista.cnpjSindCategProf.valor = limpa_formatacao(self.origem.partner_union.cnpj_cpf)
                InfoCeletista.FGTS.opcFGTS.valor = self.origem.opc_fgts
                if self.origem.dt_opc_fgts:
                    InfoCeletista.FGTS.dtOpcFGTS.valor = self.origem.dt_opc_fgts
                S2200.evento.vinculo.infoRegimeTrab.infoCeletista.append(InfoCeletista)

            elif self.origem.labor_regime_id.code == '2':

                # Popula infoEstatutario  # TODO
                InfoEstatutario = pysped.esocial.leiaute.S2200_InfoEstatutario_2()


            # Popula vinculo.infoContrato
            # S2200.evento.vinculo.infoContrato.codCargo.valor =   # TODO Quando lidar com Estatutários
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
            LocalTrabGeral.nrInsc.valor = limpa_formatacao(self.company_id.cnpj_cpf)
            # LocalTrabGeral.descComp.valor = ''  # TODO Criar no contrato
            S2200.evento.vinculo.infoContrato.localTrabalho.localTrabGeral.append(LocalTrabGeral)

            # Popula vinculo.infoContrato.horContratual (Campos)
            HorContratual = pysped.esocial.leiaute.S2200_HorContratual_2()
            HorContratual.qtdHorSem.valor = formata_valor(self.origem.weekly_hours)
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
                SucessaoVinc.dtTransf.valor = limpa_formatacao(self.origem.date_start)  # Se for transf. a data de inicio do contrato é a correta neste campo
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
                'xml_transmissao': False,
            }

            lote_id = self.env['sped.transmissao.lote'].create(vals)
            self.lote_ids = [(4, lote_id.id)]
            self.data_hora_transmissao = data_hora_transmissao

            # Transmite
            processo = processador.enviar_lote([S2200])
            envio_xml = processo.envio.envioLoteEventos.eventos[0].xml
            envio_xml_nome = S2200.evento.Id.valor + '-S2200-env.xml'
            retorno_xml = processo.resposta.xml
            retorno_xml_nome = S2200.evento.Id.valor + '-S2200-ret.xml'

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
                'xml_transmissao': False,
            }

            lote_id = self.env['sped.transmissao.lote'].create(vals)
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
                'xml_transmissao': False,
            }

            lote_id = self.env['sped.transmissao.lote'].create(vals)
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
                'xml_transmissao': False,
            }

            lote_id = self.env['sped.transmissao.lote'].create(vals)
            self.lote_ids = [(4, lote_id.id)]
            self.data_hora_transmissao = data_hora_transmissao

            # Transmite
            processo = processador.enviar_lote([R2099])
            envio_xml = processo.envio.envioLoteEventos.eventos[0].xml
            envio_xml_nome = R2099.evento.Id.valor + '-R2099-env.xml'
            retorno_xml = processo.resposta.retornoEventos[0].xml
            retorno_xml_nome = R2099.evento.Id.valor + '-R2099-ret.xml'

        # Processa retorno do EFD/Reinf
        if self.tipo == 'efdreinf':
            if processo:

                # Limpar ocorrências
                for ocorrencia in self.ocorrencia_ids:
                    ocorrencia.unlink()

                if processo.resposta.retornoStatus.dadosRegistroOcorrenciaLote.ocorrencias:
                    for ocorrencia in processo.resposta.retornoStatus.dadosRegistroOcorrenciaLote.ocorrencias:
                        vals = {
                            'transmissao_id': self.id,
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
                                'transmissao_id': self.id,
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
        self.cd_retorno = processo.resposta.evtTotalContrib.ideRecRetorno.ideStatus.cdRetorno.valor
        self.desc_retorno = processo.resposta.evtTotalContrib.ideRecRetorno.ideStatus.descRetorno.valor

        # Limpar ocorrências
        for ocorrencia in self.ocorrencia_ids:
            ocorrencia.unlink()

        # Atualiza o registro com o resultado
        if processo.resposta.evtTotalContrib.ideRecRetorno.ideStatus.cdRetorno.valor == '0':
            self.situacao = '4'

            if self.fechamento_xml_id:
                fechamento = self.fechamento_xml_id
                self.fechamento_xml_id = False
                fechamento.unlink()
            # fechamento_xml = processo.resposta.xml
            fechamento_xml = processo.resposta.original
            fechamento_xml_nome = processo.resposta.evtTotalContrib.Id.valor + '-R2099-fechamento.xml'
            anexo_id = self._grava_anexo(fechamento_xml_nome, fechamento_xml)
            self.fechamento_xml_id = anexo_id

            # Popula o registro EFD/Reinf como sucesso
            if self.origem.situacao != '2':
                self.origem.situacao = '3'

        else:
            for ocorrencia in processo.resposta.evtTotalContrib.ideRecRetorno.regOcurrs:
                vals = {
                    'transmissao_id': self.id,
                    'tipo': ocorrencia.tipo.valor,
                    'local': ocorrencia.localizacaoErroAviso.valor,
                    'codigo': ocorrencia.codigo.valor,
                    'descricao': ocorrencia.descricao.valor,
                }
                self.ocorrencia_ids.create(vals)
