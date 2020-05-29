# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
from nfselib.ginfes.v3_01.servico_enviar_lote_rps_envio_v03 import \
    EnviarLoteRpsEnvio

from erpbrasil.assinatura import certificado as cert
from erpbrasil.transmissao import TransmissaoSOAP
from erpbrasil.base import misc
from erpbrasil.edoc import NFSeFactory

from odoo import api, fields, models, _
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFSE,
    SITUACAO_EDOC_AUTORIZADA,
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

    def _generate_key(self):
        remaining = self - self.filtered(fiter_processador_edoc_nfse)
        if remaining:
            super(Document, remaining)._generate_key()

    def _processador_erpbrasil_nfse(self):
        certificado = cert.Certificado(
            arquivo=self.company_id.certificate_nfe_id.file,
            senha=self.company_id.certificate_nfe_id.password
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

    def _serialize_dados_servico(self):
        return tcDadosServico(
            Valores=tcValores(
                ValorServicos=float(self.line_ids[0].fiscal_price),
                ValorDeducoes=0.0,
                ValorPis=0.0,
                ValorCofins=0.0,
                ValorInss=0.0,
                ValorIr=0.0,
                ValorCsll=0.0,
                IssRetido='2',
                ValorIss=float(self.line_ids[0].issqn_value),
                ValorIssRetido=0.0,
                OutrasRetencoes=0.0,
                BaseCalculo=float(self.line_ids[0].issqn_base),
                Aliquota=float(self.line_ids[0].issqn_percent / 100),
                ValorLiquidoNfse=float(self.line_ids[0].amount_total),
                # ValorDeducoes=None,
                # ValorPis=None,
                # ValorCofins=None,
                # ValorInss=None,
                # ValorIr=None,
                # ValorCsll=None,
                # IssRetido='2',
                # ValorIss=None,
                # ValorIssRetido=None,
                # OutrasRetencoes=None,
                # BaseCalculo=None,
                # Aliquota=None,
                # ValorLiquidoNfse=None,
                # DescontoCondicionado=None,
                # DescontoIncondicionado=None,
            ),
            ItemListaServico='105',
            CodigoCnae=None,
            CodigoTributacaoMunicipio='6202300',
            Discriminacao=str(
                self.line_ids[0].name[:120] or ''),
            # Discriminacao=normalize('NFKD', str(
            #     self.line_ids[0].name[:120] or '')
            # ).encode('ASCII', 'ignore'),
            CodigoMunicipio=int('%s%s' % (
                self.company_id.partner_id.state_id.ibge_code,
                self.company_id.partner_id.city_id.ibge_code
            )) or None,
        )

    def _serialize_dados_tomador(self):
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
            # address_invoice_city = 'Exterior'
            address_invoice_city_code = int('9999999')
        else:
            address_invoice_state_code = self.partner_id.state_id.code
            # address_invoice_city = (normalize(
            #     'NFKD', str(
            #         self.partner_id.city_id.name or '')).encode(
            #     'ASCII', 'ignore'))
            address_invoice_city_code = int('%s%s' % (
                self.partner_id.state_id.ibge_code,
                self.partner_id.city_id.ibge_code))

        return tcDadosTomador(
            IdentificacaoTomador=tcIdentificacaoTomador(
                CpfCnpj=tcCpfCnpj(
                    Cnpj=tomador_cnpj,
                    Cpf=tomador_cpf,
                ),
                InscricaoMunicipal=misc.punctuation_rm(
                    self.partner_id.inscr_mun or ''
                ) or None
            ),
            RazaoSocial=str(
                    self.partner_id.legal_name[:60] or ''),
            # RazaoSocial=normalize('NFKD', str(
            #         self.partner_id.legal_name[:60] or ''
            #     )).encode('ASCII', 'ignore'),
            Endereco=tcEndereco(
                Endereco=str(self.partner_id.street or ''),
                # Endereco=normalize(
                #     'NFKD',
                #     str(self.partner_id.street or '')
                # ).encode('ASCII', 'ignore'),
                Numero=self.partner_id.street_number or '',
                Complemento=self.partner_shipping_id.street2 or None,
                Bairro=str(
                    self.partner_id.district or 'Sem Bairro'),
                # Bairro=normalize('NFKD', str(
                #     self.partner_id.district or 'Sem Bairro')
                #   ).encode('ASCII', 'ignore'),
                CodigoMunicipio=address_invoice_city_code,
                Uf=address_invoice_state_code,
                Cep=int(partner_cep),
            ) or None,
        )

    def _serialize_rps(self, prestador_cnpj, prestador_im):
        num_rps = self.number

        dh_emi = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(self.date)
        ).strftime('%Y-%m-%dT%H:%M:%S')

        return tcRps(
            InfRps=tcInfRps(
                Id='rps' + str(num_rps),
                IdentificacaoRps=tcIdentificacaoRps(
                    Numero=num_rps,
                    Serie=self.document_serie_id.code or '',
                    Tipo='1',
                ),
                DataEmissao=dh_emi,
                NaturezaOperacao='1',
                RegimeEspecialTributacao='1',
                OptanteSimplesNacional='1',
                IncentivadorCultural='2',
                Status='1',
                RpsSubstituido=None,
                Servico=self._serialize_dados_servico(),
                Prestador=tcIdentificacaoPrestador(
                    Cnpj=prestador_cnpj,
                    InscricaoMunicipal=prestador_im or None,
                ),
                Tomador=self._serialize_dados_tomador(),
                IntermediarioServico=None,
                ConstrucaoCivil=None,
            )
        )

    def _serialize_lote_rps(self):

        prestador_cnpj = misc.punctuation_rm(
            self.company_id.partner_id.cnpj_cpf)
        prestador_im = misc.punctuation_rm(
            self.company_id.partner_id.inscr_mun or '')

        return tcLoteRps(
            Cnpj=prestador_cnpj,
            InscricaoMunicipal=prestador_im or None,
            QuantidadeRps='1',
            ListaRps=ListaRpsType(
                Rps=[self._serialize_rps(prestador_cnpj, prestador_im)]
            )
        )

    def serialize_nfse(self):
        # numero_lote = 14
        lote_rps = EnviarLoteRpsEnvio(
            LoteRps=self._serialize_lote_rps()
        )
        return lote_rps

    @api.multi
    def _eletronic_document_send(self):
        super(Document, self)._eletronic_document_send()
        for record in self.filtered(fiter_processador_edoc_nfse):
            processador = record._processador_erpbrasil_nfse()

            protocolo = record.protocolo_autorizacao
            vals = dict()

            if not protocolo:
                for edoc in record.serialize():
                    processo = None
                    for p in processador.processar_documento(edoc):
                        processo = p

                        if processo.webservice == 'RecepcionarLoteRpsV3':
                            if not hasattr(processo.resposta, 'Protocolo'):
                                return
                            protocolo = processo.resposta.Protocolo

                    if processo.webservice == 'ConsultarSituacaoLoteRpsV3':
                        vals['codigo_situacao'] = processo.resposta.Situacao
            else:
                vals['codigo_situacao'] = 4

            if vals.get('codigo_situacao') == 1:
                vals['motivo_situacao'] = _('Não Recebido')

            elif vals.get('codigo_situacao') == 2:
                vals['motivo_situacao'] = _('Lote ainda não processado')

            elif vals.get('codigo_situacao') == 3:
                vals['motivo_situacao'] = _('Procesado com Erro')

            elif vals.get('codigo_situacao') == 4:
                vals['motivo_situacao'] = _('Procesado com Sucesso')
                vals['protocolo_autorizacao'] = protocolo

            if vals.get('codigo_situacao') in (3, 4):
                processo = processador.consultar_lote_rps(protocolo)

                if processo.resposta:
                    mensagem_completa = ''
                    if processo.resposta.ListaMensagemRetorno:
                        lista_msgs = processo.resposta.ListaMensagemRetorno
                        for mr in lista_msgs.MensagemRetorno:

                            correcao = ''
                            if mr.Correcao:
                                correcao = mr.Correcao

                            mensagem_completa += (
                                mr.Codigo + ' - ' +
                                mr.Mensagem +
                                ' - Correção: ' +
                                correcao + '\n'
                            )
                    vals['edoc_error_message'] = mensagem_completa

                if processo.resposta.ListaNfse:
                    xml_file = processador._generateds_to_string_etree(
                        processo.resposta)[0]
                    record.autorizacao_event_id.set_done(xml_file)
                    for comp in processo.resposta.ListaNfse.CompNfse:
                        vals['data_hora_autorizacao'] = \
                            comp.Nfse.InfNfse.DataEmissao
                    record._change_state(SITUACAO_EDOC_AUTORIZADA)

            record.write(vals)
        return
