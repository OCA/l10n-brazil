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

    @api.depends('envio_xml_id', 'retorno_xml_id', 'fechamento_xml_id')
    def _compute_arquivo_xml(self):
        for documento in self:
            dados = {
                'envio_xml': False,
                'retorno_xml': False,
                'fechamento_xml': False,
            }

            if documento.envio_xml_id:
                dados['envio_xml'] = documento.envio_xml_id.conteudo_xml

            if documento.retorno_xml_id:
                dados['retorno_xml'] = documento.retorno_xml_id.conteudo_xml

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
        if self.company_id.tpAmb == '1':
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
            S1000.evento.ideEvento.tpAmb.valor = int(self.company_id.esocial_tpAmb)
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
            S1000.evento.infoEmpregador.infoCadastro.contato.foneFixo.valor = self.origem.esocial_fone_fixo
            # S1000.evento.infoEmpregador.infoCadastro.contato.foneCel.valor = self.origem.esocial_fone_cel
            # S1000.evento.infoEmpregador.infoCadastro.contato.email.valor = self.origem.esocial_email

            # Popula infoEmpregador.infoCadastro.infoComplementares.situacaoPJ
            S1000.evento.infoEmpregador.infoCadastro.indSitPJ.valor = self.origem.ind_sitpj

            # Gera
            data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            dh_transmissao = datetime.now().strftime('%Y%m%d%H%M%S')
            S1000.gera_id_evento(dh_transmissao)
            processador = pysped.ProcessadorESocial()

            processador.certificado.arquivo = arquivo.name
            processador.certificado.senha = self.company_id.nfe_a1_password
            processador.ambiente = int(self.company_id.esocial_tpAmb)

            # Define a Inscrição do Processados
            processador.tpInsc = '1'
            processador.nrInsc = limpa_formatacao(self.origem.cnpj_cpf)

            # Criar registro do Lote
            vals = {
                'tipo': 'esocial',
                'ambiente': self.origem.tpAmb,
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

        # Registro R-1000 - Informações do Contribuinte (EFD-REINF)
        if self.registro == 'R-1000':

            # Cria o registro
            R1000 = pysped.efdreinf.leiaute.R1000_1()

            # Popula ideEvento
            R1000.evento.ideEvento.tpAmb.valor = self.company_id.tpAmb
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
            processador.ambiente = int(self.company_id.tpAmb)

            # Criar registro do Lote
            vals = {
                'tipo': 'efdreinf',
                'ambiente': self.origem.tpAmb,
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

        # Registro R-1070 - Tabela de Processos Administrativos/Judiciais (EFD-REINF)
        if self.registro == 'R-1070':
            return "<xml>R-1070</xml>"

        # Registro R-2010 - Retenção Contribuição Previdenciária - Serviços Tomados (EFD-REINF)
        elif self.registro == 'R-2010':

            # Calcula o Período de Apuração no formato YYYY-MM
            periodo = self.origem.efdreinf_id.periodo_id.code[3:7] + '-' + self.origem.efdreinf_id.periodo_id.code[0:2]

            # Cria o registro
            R2010 = pysped.efdreinf.leiaute.R2010_1()

            # Popula ideEvento
            R2010.evento.ideEvento.tpAmb.valor = self.company_id.tpAmb
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
            processador.ambiente = int(self.company_id.tpAmb)

            # Criar registro do Lote
            vals = {
                'tipo': 'efdreinf',
                'ambiente': self.company_id.tpAmb,
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

        # Registro R-2020 - Retenção Contribuição Previdenciária - Serviços Prestados (EFD-REINF)
        elif self.registro == 'R-2020':
            return "<xml>R-2020</xml>"

        # Registro R-2030 - Recursos Recebidos por Associação Desportiva (EFD-REINF)
        elif self.registro == 'R-2030':
            return "<xml>R-2030</xml>"

        # Registro R-2040 - Recursos Repassados para Associação Desportiva (EFD-REINF)
        elif self.registro == 'R-2040':
            return "<xml>R-2040</xml>"

        # Registro R-2050 - Comercialização da Produção por Produtor Rural PJ/Agroindústria (EFD-REINF)
        elif self.registro == 'R-2050':
            return "<xml>R-2050</xml>"

        # Registro R-2060 - Contribuição Previdenciária sobre a Receita Bruta - CPRB (EFD-REINF)
        elif self.registro == 'R-2060':
            return "<xml>R-2060</xml>"

        # Registro R-2070 - Retenções na Fonte - IR, CSLL, Cofins, PIS/PASEP
        elif self.registro == 'R-2070':
            return "<xml>R-2070</xml>"

        # Registro R-2098 - Reabertura de Eventos Periódicos
        elif self.registro == 'R-2098':
            return "<xml>R-2098</xml>"

        # Registro R-2099 - Fechamento de Eventos Periódicos
        elif self.registro == 'R-2099':

            # Calcula o Período de Apuração no formato YYYY-MM
            periodo = self.origem.periodo_id.code[3:7] + '-' + self.origem.periodo_id.code[0:2]

            # Cria o registro
            R2099 = pysped.efdreinf.leiaute.R2099_1()

            # Popula ideEvento
            R2099.evento.ideEvento.perApur.valor = periodo
            R2099.evento.ideEvento.tpAmb.valor = self.company_id.tpAmb
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
            processador.ambiente = int(self.company_id.tpAmb)

            # Criar registro do Lote
            vals = {
                'tipo': 'efdreinf',
                'ambiente': self.origem.company_id.tpAmb,
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

        # Registro R-3010 - Receita de Espetáculo Desportivo
        elif self.registro == 'R-3010':
            return "<xml>R-3010</xml>"

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
        processador.ambiente = int(self.company_id.esocial_tpAmb)

        # Consulta
        processo = processador.consultar_lote(self.protocolo)

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
        processador.ambiente = int(self.company_id.tpAmb)

        # Carrega os dados de consulta
        processador.tipoInscricaoContribuinte = '1'
        processador.numeroInscricaoContribuinte = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        processador.numeroProtocoloFechamento = self.protocolo

        # Consulta
        processo = processador.consultar_fechamento(ambiente=int(self.company_id.tpAmb))
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


