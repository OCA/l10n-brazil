# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from unicodedata import normalize

from nfselib.v3_01.tipos_v03 import (
    ListaRpsType,
    tcContato,
    tcCpfCnpj,
    tcDadosServico,
    tcDadosTomador,
    tcEndereco,
    tcIdentificacaoPrestador,
    tcIdentificacaoRps,
    tcIdentificacaoTomador,
    tcInfRps,
    tcLoteRps,
    tcRps,
    tcValores,
)
from nfselib.v3_01.servico_enviar_lote_rps_envio_v03 import EnviarLoteRpsEnvio

from erpbrasil.assinatura.certificado import Certificado
from requests import Session
from erpbrasil.transmissao import TransmissaoSOAP
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from erpbrasil.edoc import NFSe

from odoo.tools import float_round
from odoo import api, fields, models, _
from odoo.addons.edoc_base.constantes import (
    AUTORIZADO,
    AUTORIZADO_OU_DENEGADO,
    CANCELADO,
    DENEGADO,
    LOTE_EM_PROCESSAMENTO,
    LOTE_PROCESSADO,
    LOTE_RECEBIDO,
    MODELO_FISCAL_NFSE,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_INUTILIZADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
    SITUACAO_FISCAL_COMPLEMENTAR,
    SITUACAO_FISCAL_COMPLEMENTAR_EXTEMPORANEO,
    SITUACAO_FISCAL_DENEGADO,
    SITUACAO_FISCAL_INUTILIZADO,
    SITUACAO_FISCAL_MERCADORIA_NAO_CIRCULOU,
    SITUACAO_FISCAL_MERCADORIA_NAO_RECEBIDA,
    SITUACAO_FISCAL_REGIME_ESPECIAL,
    SITUACAO_FISCAL_REGULAR,
    SITUACAO_FISCAL_REGULAR_EXTEMPORANEO,
)

from .res_company import PROCESSADOR


def fiter_processador_edoc_nfe(record):
    if (record.processador_edoc == PROCESSADOR and
            record.fiscal_document_id.code in [
                MODELO_FISCAL_NFSE,
            ]):
        return True
    return False


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    edoc_error_message = fields.Text(
        readonly=True,
    )

    def _procesador_erpbrasil_nfse(self):
        certificado = Certificado(
            arquivo=self.company_id.nfe_a1_file,
            senha=self.company_id.nfe_a1_password
        )
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(certificado, session)
        return NFSe(transmissao)

    @api.multi
    def _edoc_export(self):
        super(AccountInvoice, self)._edoc_export()
        for record in self.filtered(fiter_processador_edoc_nfe):
            edoc = record.serialize()[0]
            procesador = record._procesador_erpbrasil_nfse()
            xml_file = procesador._generateds_to_string_etree(edoc)[0]
            event_id = self._gerar_evento(xml_file, type="0")
            record.autorizacao_event_id = event_id
            record._change_state(SITUACAO_EDOC_A_ENVIAR)

    def _serialize(self, edocs):
        edocs = super(AccountInvoice, self)._serialize(edocs)
        for record in self.filtered(fiter_processador_edoc_nfe):
            edocs.append(record.serialize_nfse())
        return edocs

    def serialize_nfse(self):
        dh_emi = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(self.date_hour_invoice)
        )

        numero_rps = 1236
        numero_lote = 14

        lista_rps = []

        if self.partner_id.is_company:
            tomador_cnpj = punctuation_rm(
                self.partner_id.cnpj_cpf or '')
            tomador_cpf = None
        else:
            tomador_cnpj = None
            tomador_cpf = punctuation_rm(
                self.partner_id.cnpj_cpf or '')

        if self.partner_id.country_id.id != self.company_id.country_id.id:
            address_invoice_state_code = 'EX'
            address_invoice_city = 'Exterior'
            address_invoice_city_code = '9999999'
        else:
            address_invoice_state_code = self.partner_id.state_id.code
            address_invoice_city = (normalize(
                'NFKD', unicode(
                    self.partner_id.l10n_br_city_id.name or '')).encode(
                'ASCII', 'ignore'))
            address_invoice_city_code = ('%s%s') % (
                self.partner_id.state_id.ibge_code,
                self.partner_id.l10n_br_city_id.ibge_code)
            partner_cep = punctuation_rm(self.partner_id.zip)

        prestador_cnpj = punctuation_rm(self.company_id.partner_id.cnpj_cpf)
        prestador_im = punctuation_rm(
            self.company_id.partner_id.inscr_mun or '')

        lista_rps.append(
            tcRps(
                InfRps=tcInfRps(
                    Id='rps' + str(numero_rps),
                    IdentificacaoRps=tcIdentificacaoRps(
                        Numero=numero_rps,
                        Serie=self.document_serie_id.code or '',
                        Tipo='1',
                    ),
                    DataEmissao='2019-11-22T14:38:54',
                    NaturezaOperacao='1',
                    RegimeEspecialTributacao='1',
                    OptanteSimplesNacional='1',
                    IncentivadorCultural='2',
                    Status='1',
                    RpsSubstituido=None,
                    Servico=tcDadosServico(
                        Valores=tcValores(
                            ValorServicos=self.amount_total,
                            ValorDeducoes=None,
                            # ValorPis=self.pis_value,
                            # ValorCofins=self.cofins_value,
                            ValorInss=None,
                            ValorIr=None,
                            ValorCsll=None,
                            IssRetido='2',
                            ValorIss=None,
                            ValorIssRetido=None,
                            BaseCalculo=None,
                            Aliquota=None,
                            ValorLiquidoNfse=None,
                            DescontoCondicionado=None,
                            DescontoIncondicionado=None,
                        ),
                        ItemListaServico='417',
                        # ItemListaServico='105',
                        CodigoCnae=None,
                        # CodigoTributacaoMunicipio='105:6202300',
                        CodigoTributacaoMunicipio='417/8511200',
                        Discriminacao=normalize('NFKD', unicode(
                            self.invoice_line_ids[0].name[:120] or '')
                        ).encode('ASCII', 'ignore'),
                        CodigoMunicipio=int('%s%s' % (
                            self.company_id.partner_id.state_id.ibge_code,
                            self.company_id.partner_id.l10n_br_city_id.ibge_code
                        )) or None,
                    ),
                    Prestador=tcIdentificacaoPrestador(
                        Cnpj=prestador_cnpj,
                        InscricaoMunicipal=prestador_im or None,
                    ),
                    Tomador=tcDadosTomador(
                        IdentificacaoTomador=tcIdentificacaoTomador(
                            CpfCnpj=tcCpfCnpj(
                                Cnpj=tomador_cnpj,
                                Cpf=tomador_cpf,
                            ),
                            InscricaoMunicipal=punctuation_rm(
                                self.partner_id.inscr_mun or ''
                            ) or None
                        ),
                        RazaoSocial=normalize('NFKD', unicode(
                                self.partner_id.legal_name[:60] or ''
                            )).encode('ASCII', 'ignore'),
                        Endereco=tcEndereco(
                            Endereco=normalize(
                                'NFKD',
                                unicode(self.partner_id.street or '')
                            ).encode('ASCII', 'ignore'),
                            Numero=self.partner_id.number or '',
                            Complemento=self.partner_shipping_id.street2 or None,
                            Bairro=normalize('NFKD', unicode(
                                self.partner_id.district or 'Sem Bairro')
                              ).encode('ASCII', 'ignore'),
                            CodigoMunicipio=int('%s%s' % (
                                    self.partner_id.state_id.ibge_code,
                                    self.partner_id.l10n_br_city_id.ibge_code)),
                            Uf=address_invoice_state_code,
                            Cep=int(partner_cep),
                        ) or None,
                        # Contato=tcContato(
                        #     Telefone=punctuation_rm(self.partner_id.phone or ''
                        #         ).replace(' ', '')[:11] or None,
                        #     Email=self.partner_id.email or None,
                        # )
                    ),
                    IntermediarioServico=None,
                    ConstrucaoCivil=None,
                )
            )
        )
        lote = tcLoteRps(
                Cnpj=prestador_cnpj,
                InscricaoMunicipal=prestador_im or None,
                QuantidadeRps='1',
                ListaRps=ListaRpsType(Rps=lista_rps)
        )
        lote_rps = EnviarLoteRpsEnvio(
            LoteRps=lote
        )
        return lote_rps

    @api.multi
    def _edoc_send(self):
        super(AccountInvoice, self)._edoc_send()
        for record in self.filtered(fiter_processador_edoc_nfe):
            procesador = record._procesador_erpbrasil_nfse()

            protocolo = ''

            for edoc in record.serialize():
                processo = None
                for p in procesador.processar_documento(edoc):
                    processo = p

                    if processo.webservice == u'RecepcionarLoteRpsV3':
                        protocolo = processo.resposta.Protocolo

                if processo.webservice == u'ConsultarSituacaoLoteRpsV3':
                    mensagem = ''
                    if processo.resposta.Situacao == 1:
                        mensagem = _('Não Recebido')

                    elif processo.resposta.Situacao == 2:
                        mensagem = _('Lote ainda não processado')

                    elif processo.resposta.Situacao == 3:
                        mensagem = _('Procesado com Erro')

                    elif processo.resposta.Situacao == 4:
                        mensagem = _('Procesado com Sucesso')

                    vals = {
                        'edoc_status_code': processo.resposta.Situacao,
                        'edoc_status_message': mensagem,
                        'edoc_protocol_number': protocolo,
                    }

                if processo.resposta.Situacao in (3, 4):
                    processo = procesador.consultar_lote_rps(protocolo)

                    if processo.resposta:

                        if processo.resposta.ListaMensagemRetorno:
                            mensagem_completa = ''
                            for mr in processo.resposta.ListaMensagemRetorno.MensagemRetorno:

                                mensagem_completa += (
                                    mr.Codigo + ' - ' +
                                    mr.Mensagem +
                                    u' - Correção: ' +
                                    mr.Correcao + '\n'
                                )
                                vals['edoc_error_message'] = mensagem_completa

                        if processo.resposta.ListaNfse:
                            for nfse in processo.resposta.ListaNfse:
                                print('Foi porra!')

                record.write(vals)
        return
