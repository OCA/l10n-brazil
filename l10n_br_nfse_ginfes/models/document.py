# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from nfselib.ginfes.v3_01.servico_enviar_lote_rps_envio import (
    EnviarLoteRpsEnvio,
    ListaRpsType,
    tcCpfCnpj,
    tcDadosConstrucaoCivil,
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

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    MODELO_FISCAL_NFSE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_REJEITADA,
)

from ..constants.ginfes import CONSULTAR_SITUACAO_LOTE_RPS, RECEPCIONAR_LOTE_RPS


def filter_oca_nfse(record):
    if record.processador_edoc == PROCESSADOR_OCA and record.document_type_id.code in [
        MODELO_FISCAL_NFSE,
    ]:
        return True
    return False


def filter_ginfes(record):
    if record.company_id.provedor_nfse == "ginfes":
        return True
    return False


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_oca_nfse).filtered(filter_ginfes):
            edocs.append(record.serialize_nfse_ginfes())
        return edocs

    def _serialize_ginfes_dados_servico(self):
        self.fiscal_line_ids.ensure_one()
        dados = self._prepare_dados_servico()
        return tcDadosServico(
            Valores=tcValores(
                ValorServicos=self.convert_type_nfselib(
                    tcValores, "ValorServicos", dados["valor_servicos"]
                ),
                ValorDeducoes=self.convert_type_nfselib(
                    tcValores, "ValorDeducoes", dados["valor_deducoes"]
                ),
                ValorPis=self.convert_type_nfselib(
                    tcValores, "ValorPis", dados["valor_pis"]
                ),
                ValorCofins=self.convert_type_nfselib(
                    tcValores, "ValorCofins", dados["valor_cofins"]
                ),
                ValorInss=self.convert_type_nfselib(
                    tcValores, "ValorInss", dados["valor_inss"]
                ),
                ValorIr=self.convert_type_nfselib(
                    tcValores, "ValorIr", dados["valor_ir"]
                ),
                ValorCsll=self.convert_type_nfselib(
                    tcValores, "ValorIr", dados["valor_csll"]
                ),
                IssRetido=self.convert_type_nfselib(
                    tcValores, "IssRetido", dados["iss_retido"]
                ),
                ValorIss=self.convert_type_nfselib(
                    tcValores, "ValorIss", dados["valor_iss"]
                ),
                ValorIssRetido=self.convert_type_nfselib(
                    tcValores, "ValorIssRetido", dados["valor_iss_retido"]
                ),
                OutrasRetencoes=self.convert_type_nfselib(
                    tcValores, "OutrasRetencoes", dados["outras_retencoes"]
                ),
                BaseCalculo=self.convert_type_nfselib(
                    tcValores, "BaseCalculo", dados["base_calculo"]
                ),
                Aliquota=self.convert_type_nfselib(
                    tcValores, "Aliquota", dados["aliquota"]
                ),
                ValorLiquidoNfse=self.convert_type_nfselib(
                    tcValores, "ValorLiquidoNfse", dados["valor_liquido_nfse"]
                ),
            ),
            ItemListaServico=self.convert_type_nfselib(
                tcDadosServico, "ItemListaServico", dados["item_lista_servico"]
            ),
            CodigoCnae=self.convert_type_nfselib(
                tcDadosServico, "CodigoCnae", dados["codigo_cnae"]
            ),
            CodigoTributacaoMunicipio=self.convert_type_nfselib(
                tcDadosServico,
                "CodigoTributacaoMunicipio",
                dados["codigo_tributacao_municipio"],
            ),
            Discriminacao=self.convert_type_nfselib(
                tcDadosServico, "Discriminacao", dados["discriminacao"]
            ),
            CodigoMunicipio=self.convert_type_nfselib(
                tcDadosServico, "CodigoMunicipio", dados["codigo_municipio"]
            ),
        )

    def _serialize_ginfes_dados_tomador(self):
        dados = self._prepare_dados_tomador()
        return tcDadosTomador(
            IdentificacaoTomador=tcIdentificacaoTomador(
                CpfCnpj=tcCpfCnpj(
                    Cnpj=self.convert_type_nfselib(tcCpfCnpj, "Cnpj", dados["cnpj"]),
                    Cpf=self.convert_type_nfselib(tcCpfCnpj, "Cpf", dados["cpf"]),
                ),
                InscricaoMunicipal=self.convert_type_nfselib(
                    tcIdentificacaoTomador,
                    "InscricaoMunicipal",
                    dados["inscricao_municipal"],
                ),
            ),
            RazaoSocial=self.convert_type_nfselib(
                tcDadosTomador, "RazaoSocial", dados["razao_social"]
            ),
            Endereco=tcEndereco(
                Endereco=self.convert_type_nfselib(
                    tcEndereco, "Endereco", dados["endereco"]
                ),
                Numero=self.convert_type_nfselib(tcEndereco, "Numero", dados["numero"]),
                Complemento=self.convert_type_nfselib(
                    tcEndereco, "Complemento", dados["complemento"]
                ),
                Bairro=self.convert_type_nfselib(tcEndereco, "Bairro", dados["bairro"]),
                CodigoMunicipio=self.convert_type_nfselib(
                    tcEndereco, "CodigoMunicipio", dados["codigo_municipio"]
                ),
                Uf=self.convert_type_nfselib(tcEndereco, "Uf", dados["uf"]),
                Cep=self.convert_type_nfselib(tcEndereco, "Cep", dados["cep"]),
            )
            or None,
        )

    def _serialize_ginfes_rps(self, dados):
        return tcRps(
            InfRps=tcInfRps(
                Id=dados["id"],
                IdentificacaoRps=tcIdentificacaoRps(
                    Numero=self.convert_type_nfselib(
                        tcIdentificacaoRps, "Numero", dados["numero"]
                    ),
                    Serie=self.convert_type_nfselib(
                        tcIdentificacaoRps, "Serie", dados["serie"]
                    ),
                    Tipo=self.convert_type_nfselib(
                        tcIdentificacaoRps, "Tipo", dados["tipo"]
                    ),
                ),
                DataEmissao=self.convert_type_nfselib(
                    tcInfRps, "DataEmissao", dados["date_in_out"]
                ),
                NaturezaOperacao=self.convert_type_nfselib(
                    tcInfRps, "NaturezaOperacao", dados["natureza_operacao"]
                ),
                RegimeEspecialTributacao=self.convert_type_nfselib(
                    tcInfRps,
                    "RegimeEspecialTributacao",
                    dados["regime_especial_tributacao"],
                ),
                OptanteSimplesNacional=self.convert_type_nfselib(
                    tcInfRps,
                    "OptanteSimplesNacional",
                    dados["optante_simples_nacional"],
                ),
                IncentivadorCultural=self.convert_type_nfselib(
                    tcInfRps, "IncentivadorCultural", dados["incentivador_cultural"]
                ),
                Status=self.convert_type_nfselib(tcInfRps, "Status", dados["status"]),
                RpsSubstituido=self.convert_type_nfselib(
                    tcInfRps, "RpsSubstituido", dados["rps_substitiuido"]
                ),
                Servico=self._serialize_ginfes_dados_servico(),
                Prestador=tcIdentificacaoPrestador(
                    Cnpj=self.convert_type_nfselib(
                        tcIdentificacaoPrestador, "InscricaoMunicipal", dados["cnpj"]
                    ),
                    InscricaoMunicipal=self.convert_type_nfselib(
                        tcIdentificacaoPrestador,
                        "InscricaoMunicipal",
                        dados["inscricao_municipal"],
                    ),
                ),
                Tomador=self._serialize_ginfes_dados_tomador(),
                IntermediarioServico=self.convert_type_nfselib(
                    tcInfRps, "IntermediarioServico", dados["intermediario_servico"]
                ),
                ConstrucaoCivil=tcDadosConstrucaoCivil(
                    CodigoObra=self.convert_type_nfselib(
                        tcDadosConstrucaoCivil, "CodigoObra", dados["codigo_obra"]
                    ),
                    Art=self.convert_type_nfselib(
                        tcDadosConstrucaoCivil, "Art", dados["art"]
                    ),
                ),
            )
        )

    def _serialize_ginfes_lote_rps(self):
        dados = self._prepare_lote_rps()
        return tcLoteRps(
            Cnpj=self.convert_type_nfselib(tcLoteRps, "Cnpj", dados["cnpj"]),
            InscricaoMunicipal=self.convert_type_nfselib(
                tcLoteRps, "InscricaoMunicipal", dados["inscricao_municipal"]
            ),
            QuantidadeRps=1,
            ListaRps=ListaRpsType(Rps=[self._serialize_ginfes_rps(dados)]),
        )

    def serialize_nfse_ginfes(self):
        lote_rps = EnviarLoteRpsEnvio(LoteRps=self._serialize_ginfes_lote_rps())
        return lote_rps

    def cancel_document_ginfes(self):
        for record in self.filtered(filter_oca_nfse).filtered(filter_ginfes):
            processador = record._processador_erpbrasil_nfse()
            processo = processador.cancela_documento(
                doc_numero=int(record.document_number)
            )

            status, message = processador.analisa_retorno_cancelamento(processo)

            if not status:
                raise UserError(_(message))

            try:
                xml_file = processo.envio_xml.decode("utf-8")
            except Exception:
                xml_file = processo.envio_xml

            record.cancel_event_id = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=(
                    EVENT_ENV_PROD if self.nfe_environment == "1" else EVENT_ENV_HML
                ),
                event_type="2",
                xml_file=xml_file.envio_xml,
                document_id=record,
            )

            return status

    def _document_status(self):
        status = super()._document_status()
        for record in self.filtered(filter_oca_nfse).filtered(filter_ginfes):
            processador = record._processador_erpbrasil_nfse()
            processo = processador.consulta_nfse_rps(
                rps_number=int(record.rps_number),
                rps_serie=record.document_serie,
                rps_type=int(record.rps_type),
            )

            status = _(
                processador.analisa_retorno_consulta(
                    processo,
                    record.document_number,
                    record.company_cnpj_cpf,
                    record.company_legal_name,
                )
            )
        return status

    @staticmethod
    def _get_protocolo(record, processador, vals):
        for edoc in record.serialize():
            processo = None
            for p in processador.processar_documento(edoc):
                processo = p

                if processo.webservice in RECEPCIONAR_LOTE_RPS:
                    if processo.resposta.Protocolo is None:
                        mensagem_completa = ""
                        if processo.resposta.ListaMensagemRetorno:
                            lista_msgs = processo.resposta.ListaMensagemRetorno
                            for mr in lista_msgs.MensagemRetorno:
                                correcao = ""
                                if mr.Correcao:
                                    correcao = mr.Correcao

                                mensagem_completa += (
                                    mr.Codigo
                                    + " - "
                                    + mr.Mensagem
                                    + " - Correção: "
                                    + correcao
                                    + "\n"
                                )
                        vals["edoc_error_message"] = mensagem_completa
                        record._change_state(SITUACAO_EDOC_REJEITADA)
                        record.write(vals)
                        return
                    protocolo = processo.resposta.Protocolo

            if processo.webservice in CONSULTAR_SITUACAO_LOTE_RPS:
                vals["status_code"] = processo.resposta.Situacao

        return vals, protocolo

    @staticmethod
    def _set_response(record, processador, protocolo, vals):
        processo = processador.consultar_lote_rps(protocolo)

        if processo.resposta:
            mensagem_completa = ""
            if processo.resposta.ListaMensagemRetorno:
                lista_msgs = processo.resposta.ListaMensagemRetorno
                for mr in lista_msgs.MensagemRetorno:
                    correcao = ""
                    if mr.Correcao:
                        correcao = mr.Correcao

                    mensagem_completa += (
                        mr.Codigo
                        + " - "
                        + mr.Mensagem
                        + " - Correção: "
                        + correcao
                        + "\n"
                    )
            vals["edoc_error_message"] = mensagem_completa
            if vals.get("status_code") == 3:
                record._change_state(SITUACAO_EDOC_REJEITADA)

        if processo.resposta.ListaNfse:
            xml_file = processo.retorno
            for comp in processo.resposta.ListaNfse.CompNfse:
                vals["document_number"] = comp.Nfse.InfNfse.Numero
                vals["authorization_date"] = comp.Nfse.InfNfse.DataEmissao
                vals["verify_code"] = comp.Nfse.InfNfse.CodigoVerificacao
            record.authorization_event_id.set_done(
                status_code=vals["status_code"],
                response=vals["status_name"],
                protocol_date=vals["authorization_date"],
                protocol_number=protocolo,
                file_response_xml=xml_file,
            )
            record._change_state(SITUACAO_EDOC_AUTORIZADA)

        return vals

    def _eletronic_document_send(self):
        super()._eletronic_document_send()
        for record in self.filtered(filter_oca_nfse).filtered(filter_ginfes):
            processador = record._processador_erpbrasil_nfse()

            protocolo = record.authorization_protocol
            vals = dict()

            if not protocolo:
                vals, protocolo = self._get_protocolo(record, processador, vals)

            else:
                vals["status_code"] = 4

            if vals.get("status_code") == 1:
                vals["status_name"] = _("Not received")

            elif vals.get("status_code") == 2:
                vals["status_name"] = _("Batch not yet processed")

            elif vals.get("status_code") == 3:
                vals["status_name"] = _("Processed with Error")

            elif vals.get("status_code") == 4:
                vals["status_name"] = _("Successfully Processed")
                vals["authorization_protocol"] = protocolo

            if vals.get("status_code") in (3, 4):
                vals = self._set_response(record, processador, protocolo, vals)

            record.write(vals)
        return

    def _exec_before_SITUACAO_EDOC_CANCELADA(self, old_state, new_state):
        super()._exec_before_SITUACAO_EDOC_CANCELADA(old_state, new_state)
        return self.cancel_document_ginfes()
