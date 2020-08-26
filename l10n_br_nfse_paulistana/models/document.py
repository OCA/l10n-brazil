# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import xml.etree.ElementTree as ET
from datetime import datetime
from erpbrasil.base import misc

from nfselib.paulistana.v02.TiposNFe_v01 import (
    tpEndereco,
    tpCPFCNPJ,
    tpRPS,
    tpChaveRPS,
)

from nfselib.paulistana.v02.PedidoEnvioLoteRPS_v01 import (
    CabecalhoType,
    PedidoEnvioLoteRPS,
)

from odoo import models, api
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFSE,
)

from odoo.addons.l10n_br_nfse.models.res_company import PROCESSADOR


def fiter_processador_edoc_nfse_paulistana(record):
    if (record.processador_edoc == PROCESSADOR and
            record.document_type_id.code in [
                MODELO_FISCAL_NFSE,
            ]):
        return True
    return False


def fiter_provedor_paulistana(record):
    if record.company_id.provedor_nfse == 'paulistana':
        return True
    return False


class Document(models.Model):

    _inherit = 'l10n_br_fiscal.document'

    def _serialize(self, edocs):
        edocs = super(Document, self)._serialize(edocs)
        for record in self.filtered(
                fiter_processador_edoc_nfse_paulistana).filtered(
                    fiter_provedor_paulistana):
            edocs.append(record.serialize_nfse_paulistana())
        return edocs

    def serialize_nfse_paulistana(self):
        dados_lote_rps = self._prepare_lote_rps()
        dados_servico = self._prepare_dados_servico()
        lote_rps = PedidoEnvioLoteRPS(
            Cabecalho=self._serialize_cabecalho(dados_lote_rps),
            RPS=[self._serialize_lote_rps(dados_lote_rps, dados_servico)],
        )
        return lote_rps

    def _serialize_cabecalho(self, dados_lote_rps):
        return CabecalhoType(
            CPFCNPJRemetente=tpCPFCNPJ(CNPJ=dados_lote_rps['cnpj']),
            transacao=False,  # TOOD: Verficar origem do dado
            dtInicio=dados_lote_rps['data_emissao'],
            dtFim=dados_lote_rps['data_emissao'],
            QtdRPS='1',
            ValorTotalServicos=dados_lote_rps['total_recebido'],
            ValorTotalDeducoes=dados_lote_rps['carga_tributaria'],
        )

    def _serialize_lote_rps(self, dados_lote_rps, dados_servico):
        dados_tomador = self._prepare_dados_tomador()
        return tpRPS(
            Assinatura=self.assinatura_rps(dados_lote_rps, dados_servico,
                                           dados_tomador),
            ChaveRPS=tpChaveRPS(
                InscricaoPrestador=dados_lote_rps['inscricao_municipal'].zfill(
                    8),
                SerieRPS=dados_lote_rps['serie'],
                NumeroRPS=dados_lote_rps['numero'],
            ),
            TipoRPS='RPS',  # FIXME: Hardcoded
            DataEmissao=dados_lote_rps['data_emissao'],
            StatusRPS='N',  # FIXME: Hardcoded
            TributacaoRPS='T',  # FIXME: Hardcoded
            ValorServicos=dados_servico['valor_servicos'],
            ValorDeducoes=dados_servico['valor_deducoes'],
            ValorPIS=dados_servico['valor_pis'],
            ValorCOFINS=dados_servico['valor_cofins'],
            ValorINSS=dados_servico['valor_inss'],
            ValorIR=dados_servico['valor_ir'],
            ValorCSLL=dados_servico['valor_csll'],
            CodigoServico=dados_servico['codigo_tributacao_municipio'],
            AliquotaServicos=dados_servico['aliquota'],
            ISSRetido=False,  # FIXME: Hardcoded
            CPFCNPJTomador=tpCPFCNPJ(CNPJ=dados_tomador['cnpj']),
            InscricaoMunicipalTomador=dados_tomador['inscricao_municipal'],
            InscricaoEstadualTomador=dados_tomador['inscricao_estadual'],
            RazaoSocialTomador=dados_tomador['razao_social'],
            EnderecoTomador=tpEndereco(
                Logradouro=dados_tomador['endereco'],
                NumeroEndereco=dados_tomador['numero'],
                ComplementoEndereco=dados_tomador['complemento'],
                Bairro=dados_tomador['bairro'],
                Cidade=dados_tomador['municipio'],
                UF=dados_tomador['uf'],
                CEP=str(dados_tomador['cep']),
            ),
            EmailTomador=dados_tomador['email'],
            Discriminacao=dados_servico['discriminacao'],
            ValorCargaTributaria=dados_lote_rps['carga_tributaria'],
            FonteCargaTributaria=dados_lote_rps['total_recebido'],
            MunicipioPrestacao=dados_servico['codigo_municipio'],
        )

    def _serialize_rps(self, dados):
        return tpRPS(
            InscricaoMunicipalTomador=dados['inscricao_municipal'],
            CPFCNPJTomador=tpCPFCNPJ(
                Cnpj=dados['cnpj'],
                Cpf=dados['cpf'],
            ),
            RazaoSocialTomador=dados['razao_social'],
            EnderecoTomador=tpEndereco(
                # TipoLogradouro='Rua', # TODO: Verificar se este campo é necessario
                Logradouro=dados['endereco'],
                NumeroEndereco=dados['numero'],
                ComplementoEndereco=dados['complemento'],
                Bairro=dados['bairro'],
                Cidade=dados['codigo_municipio'],
                UF=dados['uf'],
                CEP=dados['cep'],
            ) or None,
        )

    def assinatura_rps(self, dados_lote_rps, dados_servico, dados_tomador ):
        assinatura = ''

        assinatura += dados_lote_rps['inscricao_municipal'].zfill(8)
        assinatura += dados_lote_rps['serie'].ljust(5, '0')
        assinatura += dados_lote_rps['numero'].zfill(12)
        assinatura += datetime.strptime(dados_lote_rps['data_emissao'],
                                        '%Y-%m-%dT%H:%M:%S').strftime("%Y%m%d")
        assinatura += 'T'  # FIXME: Verificar tipo de tributação
        assinatura += 'N'  # FIXME: Verificar status do RPS
        assinatura += 'N'
        assinatura += str(
            dados_lote_rps['total_recebido']).replace('.', '').zfill(15)
        assinatura += str(
            dados_lote_rps['carga_tributaria']).replace('.', '').zfill(15)
        assinatura += dados_servico['codigo_tributacao_municipio'].zfill(5)
        assinatura += '2'  # FIXME: Manter sempre CNPJ?
        assinatura += dados_tomador['cnpj'].zfill(14)
        # assinatura += '3'
        # assinatura += ''.zfill(14)
        # assinatura += 'N'

        return assinatura.encode()

    @api.multi
    def _eletronic_document_send(self):
        super(Document, self)._eletronic_document_send()
        for record in self.filtered(fiter_processador_edoc_nfse_paulistana):
            for record in self.filtered(fiter_provedor_paulistana):
                processador = record._processador_erpbrasil_nfse()

                protocolo = record.protocolo_autorizacao
                vals = dict()

                if not protocolo:
                    for edoc in record.serialize():
                        processo = None
                        for p in processador.processar_documento(edoc):
                            processo = p

                            retorno = ET.fromstring(processo.retorno)

                            if retorno:
                                mensagem_erro = ''
                                for erro in retorno.findall("Erro"):
                                    codigo = erro.find('Codigo').text
                                    descricao = erro.find('Descricao').text
                                    mensagem_erro += codigo + ' - ' + descricao + '\n'

                                vals['edoc_error_message'] = mensagem_erro
                record.write(vals)
        return



