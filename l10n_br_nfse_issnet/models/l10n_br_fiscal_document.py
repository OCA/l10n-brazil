# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import xml.etree.ElementTree as ET
from nfselib.issnet.v1_00.tipos_complexos import (
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
from nfselib.issnet.v1_00.servico_enviar_lote_rps_envio import \
    EnviarLoteRpsEnvio

from odoo import models, api, _
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFSE,
    SITUACAO_EDOC_AUTORIZADA,
)

from odoo.addons.l10n_br_nfse.models.res_company import PROCESSADOR

from ..constants.issnet import (
    RECEPCIONAR_LOTE_RPS,
    CONSULTAR_SITUACAO_LOTE_RPS,
    CANCELAR_NFSE,
)


def fiter_processador_edoc_nfse_issnet(record):
    if (record.processador_edoc == PROCESSADOR and
            record.document_type_id.code in [
                MODELO_FISCAL_NFSE,
            ]):
        return True
    return False


def fiter_provedor_issnet(record):
    if record.company_id.provedor_nfse == 'issnet':
        return True
    return False


class Document(models.Model):

    _inherit = 'l10n_br_fiscal.document'

    def _serialize(self, edocs):
        edocs = super(Document, self)._serialize(edocs)
        for record in self.filtered(
                fiter_processador_edoc_nfse_issnet).filtered(
                    fiter_provedor_issnet):
            edocs.append(record.serialize_nfse_issnet())
        return edocs

    def _serialize_dados_servico(self):
        self.line_ids.ensure_one()
        dados = self._prepare_dados_servico()
        return tcDadosServico(
            Valores=tcValores(
                ValorServicos=dados['valor_servicos'],
                ValorDeducoes=dados['valor_deducoes'],
                ValorPis=dados['valor_pis'],
                ValorCofins=dados['valor_cofins'],
                ValorInss=dados['valor_inss'],
                ValorIr=dados['valor_ir'],
                ValorCsll=dados['valor_csll'],
                IssRetido=dados['iss_retido'],
                ValorIss=dados['valor_iss'],
                ValorIssRetido=dados['valor_iss_retido'],
                OutrasRetencoes=dados['outras_retencoes'],
                BaseCalculo=dados['base_calculo'],
                Aliquota=str(float(dados['aliquota'])*100),
                ValorLiquidoNfse=dados['valor_liquido_nfse'],
                DescontoIncondicionado=0,
                DescontoCondicionado=0,
            ),
            ItemListaServico=dados['item_lista_servico'],
            CodigoCnae=dados['codigo_cnae'],
            CodigoTributacaoMunicipio=dados['codigo_tributacao_municipio'],
            Discriminacao=dados['discriminacao'],
            MunicipioPrestacaoServico=dados['codigo_municipio']
            if self.company_id.nfse_environment == '1'
            else '999',
        )

    def _serialize_dados_tomador(self):
        dados = self._prepare_dados_tomador()
        return tcDadosTomador(
            IdentificacaoTomador=tcIdentificacaoTomador(
                CpfCnpj=tcCpfCnpj(
                    Cnpj=dados['cnpj'],
                    Cpf=dados['cpf'],
                ),
                InscricaoMunicipal=dados['inscricao_municipal']
                if dados['codigo_municipio'] == int('%s%s' % (
                    self.company_id.partner_id.state_id.ibge_code,
                    self.company_id.partner_id.city_id.ibge_code
                )) else None,
            ),
            RazaoSocial=dados['razao_social'],
            Endereco=tcEndereco(
                Endereco=dados['endereco'],
                Numero=dados['numero'],
                Complemento=dados['complemento'],
                Bairro=dados['bairro'],
                Cidade=dados['codigo_municipio'],
                Estado=dados['uf'],
                Cep=dados['cep'],
            ) or None,
        )

    def _serialize_rps(self, dados):

        return tcRps(
            InfRps=tcInfRps(
                id=dados['id'],
                IdentificacaoRps=tcIdentificacaoRps(
                    Numero=dados['numero'],
                    Serie=dados['serie'],
                    Tipo=dados['tipo'],
                ),
                DataEmissao=dados['data_emissao'],
                NaturezaOperacao=dados['natureza_operacao'],
                RegimeEspecialTributacao=dados['regime_especial_tributacao'],
                OptanteSimplesNacional=dados['optante_simples_nacional'],
                IncentivadorCultural=dados['incentivador_cultural'],
                Status=dados['status'],
                RpsSubstituido=dados['rps_substitiuido'],
                Servico=self._serialize_dados_servico(),
                Prestador=tcIdentificacaoPrestador(
                    CpfCnpj=tcCpfCnpj(
                        Cnpj=dados['cnpj'],
                    ),
                    InscricaoMunicipal=dados['inscricao_municipal'],
                ),
                Tomador=self._serialize_dados_tomador(),
                IntermediarioServico=dados['intermediario_servico'],
                ContrucaoCivil=dados['construcao_civil'],
            )
        )

    def _serialize_lote_rps(self):
        dados = self._prepare_lote_rps()
        return tcLoteRps(
            CpfCnpj=tcCpfCnpj(
                Cnpj=dados['cnpj'],
            ),
            InscricaoMunicipal=dados['inscricao_municipal'],
            QuantidadeRps='1',
            ListaRps=ListaRpsType(
                Rps=[self._serialize_rps(dados)]
            )
        )

    def serialize_nfse_issnet(self):
        lote_rps = EnviarLoteRpsEnvio(
            LoteRps=self._serialize_lote_rps()
        )
        return lote_rps

    def cancelar_documento(self):
        for record in self.filtered(fiter_processador_edoc_nfse_issnet):
            processador = record._processador_erpbrasil_nfse()
            processo = processador.cancela_documento(doc_numero=self.number)

            if processo.webservice in CANCELAR_NFSE:
                mensagem_completa = ''
                situacao = True
                retorno = ET.fromstring(processo.retorno)

                sucesso = retorno.findall(
                    ".//{http://www.issnetonline.com.br/webserviceabrasf/vsd/"
                    "tipos_complexos.xsd}Sucesso")
                if not sucesso:
                    mensagem_erro = retorno.findall(
                        ".//{http://www.issnetonline.com.br/webserviceabrasf/vsd/"
                        "tipos_complexos.xsd}Mensagem")[
                        0].text
                    correcao = retorno.findall(
                        ".//{http://www.issnetonline.com.br/webserviceabrasf/vsd/"
                        "tipos_complexos.xsd}Correcao")[
                        0].text
                    codigo = retorno.findall(
                        ".//{http://www.issnetonline.com.br/webserviceabrasf/vsd/"
                        "tipos_complexos.xsd}Codigo")[
                        0].text
                    mensagem_completa += (
                        codigo + ' - ' +
                        mensagem_erro +
                        ' - Correção: ' +
                        correcao + '\n'
                    )
                    situacao = False

                return situacao, mensagem_completa

    def action_consultar_nfse_rps(self):
        for record in self.filtered(fiter_processador_edoc_nfse_issnet):
            processador = record._processador_erpbrasil_nfse()
            processo = processador.consulta_nfse_rps(
                self.rps_number, self.document_serie, self.rps_type)

            return _(
                processador.analisa_retorno_consulta(
                    processo,
                    self.number,
                    self.company_cnpj_cpf,
                    self.company_legal_name)
            )

    @api.multi
    def _eletronic_document_send(self):
        super(Document, self)._eletronic_document_send()
        for record in self.filtered(fiter_processador_edoc_nfse_issnet):
            for record in self.filtered(fiter_provedor_issnet):
                processador = record._processador_erpbrasil_nfse()

                protocolo = record.protocolo_autorizacao
                vals = dict()

                if not protocolo:
                    for edoc in record.serialize():
                        processo = None
                        for p in processador.processar_documento(edoc):
                            processo = p

                            if processo.webservice in RECEPCIONAR_LOTE_RPS:
                                if processo.resposta.Protocolo is None:
                                    mensagem_completa = ''
                                    if processo.resposta.ListaMensagemRetorno:
                                        lista_msgs = processo.resposta.\
                                            ListaMensagemRetorno
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
                                    vals['edoc_error_message'] = \
                                        mensagem_completa
                                    record.write(vals)
                                    return
                                protocolo = processo.resposta.Protocolo

                        if processo.webservice in CONSULTAR_SITUACAO_LOTE_RPS:
                            vals['codigo_situacao'] = \
                                processo.resposta.Situacao
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
                            vals['number'] = comp.Nfse.InfNfse.Numero
                            vals['data_hora_autorizacao'] = \
                                comp.Nfse.InfNfse.DataEmissao
                            vals['verify_code'] = \
                                comp.Nfse.InfNfse.CodigoVerificacao
                        record._change_state(SITUACAO_EDOC_AUTORIZADA)

                record.write(vals)
        return
