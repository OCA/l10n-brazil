# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from nfselib.issnet.v1_00.servico_enviar_lote_rps_envio import (
    EnviarLoteRpsEnvio,
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

from odoo import _, api, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    MODELO_FISCAL_NFSE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_REJEITADA,
)

from ..constants.issnet import CONSULTAR_SITUACAO_LOTE_RPS, RECEPCIONAR_LOTE_RPS


def filter_processador_edoc_nfse(record):
    if record.processador_edoc == PROCESSADOR_OCA and record.document_type_id.code in [
        MODELO_FISCAL_NFSE,
    ]:
        return True
    return False


def fiter_provedor_issnet(record):
    if record.company_id.provedor_nfse == "issnet":
        return True
    return False


class Document(models.Model):

    _inherit = "l10n_br_fiscal.document"

    def _serialize(self, edocs):
        edocs = super(Document, self)._serialize(edocs)
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            fiter_provedor_issnet
        ):
            edocs.append(record.serialize_nfse_issnet())
        return edocs

    def _serialize_issnet_dados_servico(self):
        self.line_ids.ensure_one()
        dados = self._prepare_dados_servico()
        if self.company_id.nfse_environment == "1":
            municipio_prestacao_servico = (
                dados["municipio_prestacao_servico"] or dados["codigo_municipio"]
            )
        else:
            municipio_prestacao_servico = 999
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
                    tcValores, "ValorCsll", dados["valor_csll"]
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
                    tcValores, "Aliquota", str(float(dados["aliquota"]) * 100)
                ),
                ValorLiquidoNfse=self.convert_type_nfselib(
                    tcValores, "ValorLiquidoNfse", dados["valor_liquido_nfse"]
                ),
                DescontoIncondicionado=0,
                DescontoCondicionado=0,
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
            MunicipioPrestacaoServico=self.convert_type_nfselib(
                tcDadosServico, "MunicipioPrestacaoServico", municipio_prestacao_servico
            ),
        )

    def _serialize_issnet_dados_tomador(self):
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
                )
                if dados["codigo_municipio"]
                == int("%s" % (self.company_id.partner_id.city_id.ibge_code))
                else None,
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
                Cidade=self.convert_type_nfselib(
                    tcEndereco, "Cidade", dados["codigo_municipio"]
                ),
                Estado=self.convert_type_nfselib(tcEndereco, "Estado", dados["uf"]),
                Cep=self.convert_type_nfselib(tcEndereco, "Cep", dados["cep"]),
            )
            or None,
        )

    def _serialize_issnet_rps(self, dados):

        return tcRps(
            InfRps=tcInfRps(
                id=dados["id"],
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
                    tcInfRps, "DataEmissao", dados["data_emissao"]
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
                Servico=self._serialize_issnet_dados_servico(),
                Prestador=tcIdentificacaoPrestador(
                    CpfCnpj=tcCpfCnpj(
                        Cnpj=self.convert_type_nfselib(
                            tcCpfCnpj, "Cnpj", dados["cnpj"]
                        ),
                    ),
                    InscricaoMunicipal=self.convert_type_nfselib(
                        tcIdentificacaoPrestador,
                        "InscricaoMunicipal",
                        dados["inscricao_municipal"],
                    ),
                ),
                Tomador=self._serialize_issnet_dados_tomador(),
                IntermediarioServico=self.convert_type_nfselib(
                    tcInfRps, "IntermediarioServico", dados["intermediario_servico"]
                ),
                ConstrucaoCivil=self.convert_type_nfselib(
                    tcInfRps, "ConstrucaoCivil", dados["construcao_civil"]
                ),
            )
        )

    def _serialize_issnet_lote_rps(self):
        dados = self._prepare_lote_rps()
        return tcLoteRps(
            CpfCnpj=tcCpfCnpj(
                Cnpj=self.convert_type_nfselib(tcCpfCnpj, "Cnpj", dados["cnpj"]),
            ),
            InscricaoMunicipal=self.convert_type_nfselib(
                tcLoteRps, "InscricaoMunicipal", dados["inscricao_municipal"]
            ),
            QuantidadeRps=1,
            ListaRps=ListaRpsType(Rps=[self._serialize_issnet_rps(dados)]),
        )

    def serialize_nfse_issnet(self):
        lote_rps = EnviarLoteRpsEnvio(LoteRps=self._serialize_issnet_lote_rps())
        return lote_rps

    def cancel_document_issnet(self):
        for record in self.filtered(filter_processador_edoc_nfse):
            processador = record._processador_erpbrasil_nfse()
            processo = processador.cancela_documento(
                doc_numero=int(record.document_number)
            )

            status, message = processador.analisa_retorno_cancelamento(processo)

            if not status:
                raise UserError(_(message))

            record.cancel_event_id = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=(
                    EVENT_ENV_PROD if self.nfe_environment == "1" else EVENT_ENV_HML
                ),
                event_type="2",
                xml_file=processo.envio_xml,
                document_id=record,
            )

            return status

    def _document_status(self):
        for record in self.filtered(filter_processador_edoc_nfse):
            processador = record._processador_erpbrasil_nfse()
            processo = processador.consulta_nfse_rps(
                rps_number=int(record.rps_number),
                document_serie=record.document_serie,
                rps_type=int(record.rps_type),
            )

            return _(
                processador.analisa_retorno_consulta(
                    processo,
                    record.document_number,
                    record.company_cnpj_cpf,
                    record.company_legal_name,
                )
            )

    @api.multi
    def _eletronic_document_send(self):
        super(Document, self)._eletronic_document_send()
        edoc_nfse = self.filtered(filter_processador_edoc_nfse)
        for record in edoc_nfse.filtered(fiter_provedor_issnet):
            processador = record._processador_erpbrasil_nfse()

            protocolo = record.authorization_protocol
            vals = dict()

            if not protocolo:
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
                        if processo.resposta.Situacao is None:
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
                        else:
                            vals["status_code"] = processo.resposta.Situacao
            else:
                vals["status_code"] = 4

            vals = record._update_status(vals, protocolo)
            vals = record._get_status_lot_rps(vals, processador, protocolo)

            record.write(vals)
            if record.status_code == "4":
                record.make_pdf()
        return

    def _update_status(self, vals, protocolo):
        self.ensure_one()
        if vals.get("status_code") == 1:
            vals["status_name"] = _("Not received")

        elif vals.get("status_code") == 2:
            vals["status_name"] = _("Batch not yet processed")

        elif vals.get("status_code") == 3:
            vals["status_name"] = _("Processed with Error")

        elif vals.get("status_code") == 4:
            vals["status_name"] = _("Successfully Processed")
            vals["authorization_protocol"] = protocolo
        return vals

    def _get_status_lot_rps(self, vals, processador, protocolo):
        self.ensure_one()
        if vals.get("status_code") in (3, 4):
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
                    self._change_state(SITUACAO_EDOC_REJEITADA)

            if processo.resposta.ListaNfse:
                xml_file = processo.retorno
                for comp in processo.resposta.ListaNfse.CompNfse:
                    vals["document_number"] = comp.Nfse.InfNfse.Numero
                    vals["authorization_date"] = comp.Nfse.InfNfse.DataEmissao
                    vals["verify_code"] = comp.Nfse.InfNfse.CodigoVerificacao
                self.authorization_event_id.set_done(
                    status_code=vals["status_code"],
                    response=vals["status_name"],
                    protocol_date=vals["authorization_date"],
                    protocol_number=protocolo,
                    file_response_xml=xml_file,
                )
                self._change_state(SITUACAO_EDOC_AUTORIZADA)
        return vals

    def _exec_before_SITUACAO_EDOC_CANCELADA(self, old_state, new_state):
        super(Document, self)._exec_before_SITUACAO_EDOC_CANCELADA(old_state, new_state)
        return self.cancel_document_issnet()
