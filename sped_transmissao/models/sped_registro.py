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
    _rec_name = 'name'
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
    name = fields.Char(
        string='Nome',
        compute='_compute_name',
        store=True,
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
            ('6', 'Retificado'),
            ('7', 'Excluído'),
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
        string='Hash',
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

    @api.depends('registro', 'codigo', 'origem')
    def _compute_name(self):
        for registro in self:
            name = ''
            if registro.registro:
                name += registro.registro or ''
            if registro.codigo:
                name += ' ' if name else ''
                name += '('
                name += registro.codigo or ''
                name += ')'
            if registro.origem:
                name += ' - ' if name else ''
                name += registro.origem.display_name or ''
            registro.name = name

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
            self.origem_intermediario.limpar_db = True
            self.transmitir_lote()
            self.recibo = False
            self.protocolo = False
            self.origem_intermediario.limpar_db = False

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
        grupo = self.env['sped.criacao.wizard'].get_valor_grupo(self)
        vals = {
            'tipo': self.tipo,
            'company_id': self.company_id.id,
            'ambiente': self.ambiente,
            'grupo': grupo,
            'transmissao_ids': [(4, self.id)],
        }
        lote_id = self.env['sped.lote'].create(vals)
        self.lote_ids = [(4, lote_id.id)]

        # Transmite
        lote_id.transmitir()

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

    # Este método será chamado pelo lote quando a consulta for concluída com sucesso
    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        # Chama o método retorno_sucesso do registro de origem
        self.origem_intermediario.retorno_sucesso(evento)
