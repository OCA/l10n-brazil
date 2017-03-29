# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


import logging
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from ...sped.constante_tributaria import *

_logger = logging.getLogger(__name__)

try:
    from pysped.nfe.leiaute import *
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import (parse_datetime, UTC, data_hora_horario_brasilia,
                               agora)
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)


class CartaCorrecao(models.Model):
    _description = u'Carta de Correção'
    _name = 'sped.documento.carta.correcao'
    _order = 'documento_id, sequencia desc'
    _rec_name = 'descricao'

    descricao = fields.Char(
        string=u'Carta de Correção',
        compute='_compute_descricao',
    )
    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string=u'Documento',
        ondelete='cascade',
    )
    sequencia = fields.Integer(
        string=u'Sequência',
    )
    correcao = fields.Text(
        string=u'Correção',
    )

    #
    # Os campos de anexos abaixo servem para que os anexos não possam
    # ser excluídos pelo usuário, somente através do sistema ou pelo
    # suporte
    #
    arquivo_xml_id = fields.Many2one(
        comodel_name='ir.attachment',
        string=u'XML',
        ondelete='restrict',
        copy=False,
    )
    arquivo_xml_autorizacao_id = fields.Many2one(
        comodel_name='ir.attachment',
        string=u'XML de autorização',
        ondelete='restrict',
        copy=False,
    )
    arquivo_pdf_id = fields.Many2one(
        comodel_name='ir.attachment',
        string=u'PDF DAEDE',
        ondelete='restrict',
        copy=False,
    )
    data_hora_autorizacao = fields.Datetime(
        string=u'Data de autorização',
        index=True,
    )
    data_autorizacao = fields.Date(
        string=u'Data de autorização',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )
    protocolo_autorizacao = fields.Char(
        string=u'Protocolo de autorização',
        size=60,
    )
    permite_alteracao = fields.Boolean(
        string=u'Permite alteração?',
        compute='_compute_permite_alteracao',
    )

    @api.depends('documento_id', 'sequencia')
    def _compute_descricao(self):
        for carta_correcao in self:
            txt = u'CC-e nº '
            txt += \
                formata_valor(carta_correcao.sequencia or 1, casas_decimais=0)
            txt += u' - '
            txt += carta_correcao.documento_id.descricao

            carta_correcao.descricao = txt

    @api.depends('data_hora_autorizacao')
    def _compute_permite_alteracao(self):
        for carta_correcao in self:
            if carta_correcao.data_hora_autorizacao:
                carta_correcao.permite_alteracao = False
            else:
                carta_correcao.permite_alteracao = True

    def _check_permite_alteracao(self, operacao='create', dados={}):
        for carta_correcao in self:
            if carta_correcao.permite_alteracao:
                if operacao == 'unlink':
                    mensagem = \
                        u'Não é permitido excluir esta carta de correção!'
                elif operacao == 'write':
                    mensagem = \
                        u'Não é permitido alterar esta carta de correção!'
                elif operacao == 'create':
                    mensagem = \
                        u'Não é permitido criar esta carta de correção!'

                raise ValidationError(mensagem)

    @api.depends('data_hora_autorizacao')
    def _compute_data_hora_separadas(self):
        for carta_correcao in self:
            if carta_correcao.data_hora_autorizacao:
                data_hora_autorizacao = data_hora_horario_brasilia(
                    parse_datetime(carta_correcao.data_hora_autorizacao))
                carta_correcao.data_autorizacao = \
                    str(data_hora_autorizacao)[:10]

    def _grava_anexo(self, nome_arquivo='', conteudo='',
                     tipo='application/xml'):
        self.ensure_one()

        attachment = self.env['ir.attachment']

        busca = [
            ('res_model', '=', 'sped.documento.carta.correcao'),
            ('res_id', '=', self.id),
            ('name', '=', nome_arquivo),
        ]
        attachment_ids = attachment.search(busca)
        attachment_ids.unlink()

        dados = {
            'name': nome_arquivo,
            'datas_fname': nome_arquivo,
            'res_model': 'sped.documento.carta.correcao',
            'res_id': self.id,
            'datas': conteudo.encode('base64'),
            'mimetype': tipo,
        }

        anexo_id = self.env['ir.attachment'].create(dados)

        return anexo_id

    def grava_xml(self, nfe, cce):
        nome_arquivo = nfe.chave + '-' + \
            str(self.sequencia or 1).zfill(3) + '-cce.xml'
        conteudo = cce.xml.encode('utf-8')
        self.arquivo_xml_id = False
        self.arquivo_xml_id = self._grava_anexo(nome_arquivo, conteudo).id

    def grava_pdf(self, nfe, daede_pdf):
        nome_arquivo = nfe.chave + '-' + \
            str(self.sequencia or 1).zfill(3) + '-cce.pdf'
        conteudo = daede_pdf
        self.arquivo_pdf_id = False
        self.arquivo_pdf_id = self._grava_anexo(nome_arquivo, conteudo,
                                                tipo='application/pdf').id

    def grava_xml_autorizacao(self, nfe, cce):
        nome_arquivo = nfe.chave + '-' + \
            str(self.sequencia or 1).zfill(3) + '-proc-nfe.xml'
        conteudo = cce.xml.encode('utf-8')
        self.arquivo_xml_autorizacao_id = False
        self.arquivo_xml_autorizacao_id = \
            self._grava_anexo(nome_arquivo, conteudo).id

    def envia_cce(self):
        self.ensure_one()

        processador = self.documento_id.processador_nfe()

        xml = self.documento_id.arquivo_xml_autorizacao_id.datas.decode('base64')
        xml = xml.decode('utf-8')

        procNFe = ProcNFe_310()

        procNFe.xml = xml
        procNFe.NFe.monta_chave()

        evento = EventoCCe_100()
        evento.infEvento.tpAmb.valor = procNFe.NFe.infNFe.ide.tpAmb.valor
        evento.infEvento.cOrgao.valor = procNFe.NFe.chave[:2]
        evento.infEvento.CNPJ.valor = procNFe.NFe.infNFe.emit.CNPJ.valor
        evento.infEvento.chNFe.valor = procNFe.NFe.chave
        evento.infEvento.dhEvento.valor = agora()

        #self.correcao =
        ##
        ## Correção ASP - Cláudia copiou e colou e veio esse caracter esquisito
        ##
        #if self.correcao:
            #self.correcao = self.correcao.replace(u'\u200b', ' ')

        evento.infEvento.detEvento.xCorrecao.valor = self.correcao or ''
        evento.infEvento.nSeqEvento.valor = self.sequencia or 1

        if processador.certificado:
            processador.certificado.assina_xmlnfe(evento)

        processador.salvar_arquivo = True
        processo = processador.enviar_lote_cce(lista_eventos=[evento])

        #
        # A CC-e foi aceita e vinculada à NF-e
        #
        import ipdb; ipdb.set_trace();
        if self.documento_id.chave in processo.resposta.dic_procEvento:
            procevento = \
                processo.resposta.dic_procEvento[self.documento_id.chave]

            retevento = procevento.retEvento

            import ipdb; ipdb.set_trace();
            if retevento.infEvento.cStat.valor not in ('135', '136'):
                mensagem = u'Erro na carta de correção'
                mensagem += u'\nCódigo: ' + retevento.infEvento.cStat.valor
                mensagem += u'\nMotivo: ' + \
                    retevento.infEvento.xMotivo.valor
                raise UserError(mensagem)

            self.grava_xml(procNFe.NFe, evento)
            self.grava_xml_autorizacao(procNFe.NFe, procevento)

            data_autorizacao = retevento.infEvento.dhRegEvento.valor
            data_autorizacao = UTC.normalize(data_autorizacao)

            #
            # Gera o DAEDE da nova CC-e
            #
            processador.daede.NFe = procNFe.NFe
            processador.daede.protNFe = procNFe.protNFe
            processador.daede.procEventos = [procevento]
            processador.daede.salvar_arquivo = False
            processador.daede.gerar_daede()
            self.grava_pdf(procNFe.NFe, processador.daede.conteudo_pdf)

            self.data_hora_autorizacao = data_autorizacao
            self.protocolo_autorizacao = \
                procevento.retEvento.infEvento.nProt.valor

    def unlink(self):
        self._check_permite_alteracao(operacao='unlink')
        return super(CartaCorrecao, self).unlink()

    def write(self, dados):
        self._check_permite_alteracao(operacao='write', dados=dados)
        return super(CartaCorrecao, self).write(dados)

    @api.onchange('documento_id')
    def _onchange_documento_id(self):
        self.ensure_one()

        pass
