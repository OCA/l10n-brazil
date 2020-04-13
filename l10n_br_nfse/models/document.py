# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unicodedata import normalize
from requests import Session

from nfselib.ginfes.v3_01.tipos_v03 import (
    ListaRpsType,
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
from nfselib.ginfes.v3_01.servico_enviar_lote_rps_envio_v03 import EnviarLoteRpsEnvio

from erpbrasil.assinatura import certificado as cert
from erpbrasil.transmissao import TransmissaoSOAP
from erpbrasil.base import misc
from erpbrasil.edoc import NFSeFactory

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from odoo import api, fields, models, _
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFSE,
    SITUACAO_EDOC_A_ENVIAR,
)

from .res_company import PROCESSADOR


def fiter_processador_edoc_nfse(record):
    if (record.processador_edoc == PROCESSADOR and
            record.document_type_id.code in [
                MODELO_FISCAL_NFSE,
            ]):
        return True
    return False


def fiter_provedor_ginfes(record):
    if record.company_id.provedor_nfse == 'ginfes':
        return True
    return False


class Document(models.Model):

    _inherit = 'l10n_br_fiscal.document'

    edoc_error_message = fields.Text(
        readonly=True,
    )

    def _processador_erpbrasil_nfse(self):
        certificado = cert.Certificado(
            arquivo=self.company_id.nfe_a1_file,
            senha=self.company_id.nfe_a1_password
        )
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(certificado, session)
        return NFSeFactory(
            transmissao=transmissao,
            ambiente=2,
            cidade_ibge=int('%s%s' % (
                self.company_id.partner_id.state_id.ibge_code,
                self.company_id.partner_id.city_id.ibge_code
            )),
            cnpj_prestador=misc.punctuation_rm(
                self.company_id.partner_id.cnpj_cpf),
            im_prestador=misc.punctuation_rm(
                self.company_id.partner_id.inscr_mun or ''),
        )

    @api.multi
    def _document_export(self):
        super(Document, self)._document_export()
        for record in self.filtered(fiter_processador_edoc_nfse):
            edoc = record.serialize()[0]
            processador = record._processador_erpbrasil_nfse()
            xml_file = processador._generateds_to_string_etree(edoc)[0]
            event_id = self._gerar_evento(xml_file, event_type="0")
            record.autorizacao_event_id = event_id

    def _serialize(self, edocs):
        edocs = super(Document, self)._serialize(edocs)
        for record in self.filtered(
                fiter_processador_edoc_nfse).filtered(fiter_provedor_ginfes):
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
            tomador_cnpj = misc.punctuation_rm(
                self.partner_id.cnpj_cpf or '')
            tomador_cpf = None
        else:
            tomador_cnpj = None
            tomador_cpf = misc.punctuation_rm(
                self.partner_id.cnpj_cpf or '')

        partner_cep = misc.punctuation_rm(self.partner_id.zip)

        if self.partner_id.country_id.id != self.company_id.country_id.id:
            address_invoice_state_code = 'EX'
            address_invoice_city = 'Exterior'
            address_invoice_city_code = '9999999'
        else:
            address_invoice_state_code = self.partner_id.state_id.code
            address_invoice_city = (normalize(
                'NFKD', str(
                    self.partner_id.city_id.name or '')).encode(
                'ASCII', 'ignore'))
            address_invoice_city_code = ('%s%s') % (
                self.partner_id.state_id.ibge_code,
                self.partner_id.city_id.ibge_code)

        prestador_cnpj = misc.punctuation_rm(
            self.company_id.partner_id.cnpj_cpf)
        prestador_im = misc.punctuation_rm(
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
                        CodigoCnae=None,
                        CodigoTributacaoMunicipio='417/8511200',
                        Discriminacao=normalize('NFKD', str(
                            self.invoice_line_ids[0].name[:120] or '')
                        ).encode('ASCII', 'ignore'),
                        CodigoMunicipio=int('%s%s' % (
                            self.company_id.partner_id.state_id.ibge_code,
                            self.company_id.partner_id.city_id.ibge_code
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
                            InscricaoMunicipal=misc.punctuation_rm(
                                self.partner_id.inscr_mun or ''
                            ) or None
                        ),
                        RazaoSocial=normalize('NFKD', str(
                                self.partner_id.legal_name[:60] or ''
                            )).encode('ASCII', 'ignore'),
                        Endereco=tcEndereco(
                            Endereco=normalize(
                                'NFKD',
                                str(self.partner_id.street or '')
                            ).encode('ASCII', 'ignore'),
                            Numero=self.partner_id.number or '',
                            Complemento=self.partner_shipping_id.street2 or None,
                            Bairro=normalize('NFKD', str(
                                self.partner_id.district or 'Sem Bairro')
                              ).encode('ASCII', 'ignore'),
                            CodigoMunicipio=int('%s%s' % (
                                    self.partner_id.state_id.ibge_code,
                                    self.partner_id.city_id.ibge_code)),
                            Uf=address_invoice_state_code,
                            Cep=int(partner_cep),
                        ) or None,
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
    def _eletronic_document_send(self):
        super(Document, self)._eletronic_document_send()
        for record in self.filtered(fiter_processador_edoc_nfse):
            processador = record._processador_erpbrasil_nfse()

            protocolo = ''
            vals = dict()

            for edoc in record.serialize():
                processo = None
                for p in processador.processar_documento(edoc):
                    processo = p

                    if processo.webservice == 'RecepcionarLoteRpsV3':
                        protocolo = processo.resposta.Protocolo

                if processo.webservice == 'ConsultarSituacaoLoteRpsV3':
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
                        'codigo_situacao': processo.resposta.Situacao,
                        'motivo_situacao': mensagem,
                        'protocolo_autorizacao': protocolo,
                    }

                if processo.resposta.Situacao in (3, 4):
                    processo = processador.consultar_lote_rps(protocolo)

                    if processo.resposta:

                        if processo.resposta.ListaMensagemRetorno:
                            mensagem_completa = ''
                            for mr in processo.resposta.ListaMensagemRetorno.MensagemRetorno:

                                mensagem_completa += (
                                    mr.Codigo + ' - ' +
                                    mr.Mensagem +
                                    ' - Correção: ' +
                                    mr.Correcao + '\n'
                                )
                                vals['edoc_error_message'] = mensagem_completa

                        if processo.resposta.ListaNfse:
                            for nfse in processo.resposta.ListaNfse:
                                print('Foi porra!')

                record.write(vals)
        return
