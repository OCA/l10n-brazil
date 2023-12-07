# Copyright (C) 2023-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from nfselib.bindings.betha.servico_enviar_lote_rps_envio_v01 import EnviarLoteRpsEnvio
from nfselib.bindings.betha.tipos_nfe_v01 import (
    TcCpfCnpj,
    TcDadosServico,
    TcDadosTomador,
    TcEndereco,
    TcIdentificacaoPrestador,
    TcIdentificacaoRps,
    TcIdentificacaoTomador,
    TcInfRps,
    TcLoteRps,
    TcRps,
    TcValores,
)

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_REJEITADA,
)
from odoo.addons.l10n_br_nfse.models.document import filter_processador_edoc_nfse

from ..constants.betha import CONSULTAR_SITUACAO_LOTE_RPS


def filter_betha(record):
    if record.company_id.provedor_nfse == "betha":
        return True
    return False


class Document(models.Model):

    _inherit = "l10n_br_fiscal.document"

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_betha
        ):
            edocs.append(record.serialize_nfse_betha())
        return edocs

    def _serialize_betha_dados_servico(self):
        self.fiscal_line_ids.ensure_one()
        dados = self._prepare_dados_servico()
        return TcDadosServico(
            Valores=TcValores(
                ValorServicos=dados["valor_servicos"],
                ValorDeducoes=dados["valor_deducoes"],
                ValorPis=dados["valor_pis_retido"],
                ValorCofins=dados["valor_cofins_retido"],
                ValorInss=dados["valor_inss_retido"],
                ValorIr=dados["valor_ir_retido"],
                ValorCsll=dados["valor_csll_retido"],
                IssRetido=dados["iss_retido"],
                ValorIss=dados["valor_iss"],
                ValorIssRetido=dados["valor_iss_retido"],
                OutrasRetencoes=dados["outras_retencoes"],
                BaseCalculo=dados["base_calculo"],
                Aliquota=dados["aliquota"],
                ValorLiquidoNfse=dados["valor_liquido_nfse"],
            ),
            ItemListaServico=dados["item_lista_servico"],
            CodigoCnae=dados["codigo_cnae"],
            CodigoTributacaoMunicipio=dados["codigo_tributacao_municipio"],
            Discriminacao=dados["discriminacao"],
            CodigoMunicipio=dados["codigo_municipio"],
        )

    def _serialize_betha_dados_tomador(self):
        dados = self._prepare_dados_tomador()
        return TcDadosTomador(
            IdentificacaoTomador=TcIdentificacaoTomador(
                CpfCnpj=TcCpfCnpj(
                    Cnpj=dados["cnpj"],
                    Cpf=dados["cpf"],
                ),
                InscricaoMunicipal=dados["inscricao_municipal"],
            ),
            RazaoSocial=dados["razao_social"],
            Endereco=TcEndereco(
                Endereco=dados["endereco"],
                Numero=dados["numero"],
                Complemento=dados["complemento"],
                Bairro=dados["bairro"],
                CodigoMunicipio=dados["codigo_municipio"],
                Uf=dados["uf"],
                Cep=dados["cep"],
            )
            or None,
        )

    def _serialize_betha_rps(self, dados):
        return TcRps(
            InfRps=TcInfRps(
                Id=dados["id"],
                IdentificacaoRps=TcIdentificacaoRps(
                    Numero=dados["numero"],
                    Serie=dados["serie"],
                    Tipo=dados["tipo"],
                ),
                DataEmissao=dados["date_in_out"],
                NaturezaOperacao=dados["natureza_operacao"],
                RegimeEspecialTributacao=dados["regime_especial_tributacao"],
                OptanteSimplesNacional=dados["optante_simples_nacional"],
                IncentivadorCultural=dados["incentivador_cultural"],
                Status=dados["status"],
                RpsSubstituido=dados["rps_substitiuido"],
                Servico=self._serialize_betha_dados_servico(),
                Prestador=TcIdentificacaoPrestador(
                    Cnpj=dados["cnpj"],
                    InscricaoMunicipal=dados["inscricao_municipal"],
                ),
                Tomador=self._serialize_betha_dados_tomador(),
                IntermediarioServico=dados["intermediario_servico"],
                ConstrucaoCivil=dados["construcao_civil"],
            )
        )

    def _serialize_betha_lote_rps(self):
        dados = self._prepare_lote_rps()
        return TcLoteRps(
            Cnpj=dados["cnpj"],
            InscricaoMunicipal=dados["inscricao_municipal"],
            QuantidadeRps=1,
            ListaRps=TcLoteRps.ListaRps(Rps=[self._serialize_betha_rps(dados)]),
        )

    def serialize_nfse_betha(self):
        lote_rps = EnviarLoteRpsEnvio(LoteRps=self._serialize_betha_lote_rps())
        return lote_rps

    def cancel_document_betha(self):
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_betha
        ):
            processador = record._processador_erpbrasil_nfse()
            processo = processador.cancela_documento(record.document_number)
            resposta = processo.resposta

            # Verificar se houve erros.
            if resposta.lista_mensagem_retorno:
                formated_messages = []
                for msg_lista in resposta.lista_mensagem_retorno:
                    for msg in msg_lista.mensagem_retorno:
                        formated_messages.append(
                            f"Code: {msg.codigo} "
                            f"Message: {msg.mensagem} "
                            f"Correction: {msg.correcao}"
                        )
                all_msg = _(
                    f"It was not possible to cancel the NFS-e {record.document_number} \n"
                )
                all_msg += "\n".join(formated_messages)
                raise UserError(all_msg)

            # Registra o evento de cancelamento.
            record.cancel_event_id = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=(
                    EVENT_ENV_PROD if self.nfse_environment == "1" else EVENT_ENV_HML
                ),
                event_type="2",
                xml_file=processo.envio_xml,
                document_id=record,
            )
            self.state_edoc = SITUACAO_EDOC_CANCELADA
            self.cancel_event_id.set_done(
                status_code=None,
                response=None,
                protocol_date=None,
                protocol_number=None,
                file_response_xml=processo.retorno,
            )

    def _document_status(self):
        status = super()._document_status()
        for doc in self.filtered(filter_processador_edoc_nfse).filtered(filter_betha):
            processador = doc._processador_erpbrasil_nfse()
            processo = processador.consulta_nfse_rps(
                rps_number=doc.rps_number,
                rps_serie=doc.document_serie,
                rps_type=doc.rps_type,
            )
            if doc.state_edoc != SITUACAO_EDOC_AUTORIZADA:
                doc._save_nfse_data(processo.resposta.compl_nfse, processo.retorno)
            status = _("Situação Normal")
        return status

    def _eletronic_document_send(self):
        super()._eletronic_document_send()
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_betha
        ):
            processador = record._processador_erpbrasil_nfse()
            vals = {}
            for edoc in record.serialize():
                processo = None
                for p in processador.processar_documento(edoc):
                    processo = p
                    # TODO
                    # No processo 'envio do lote' armazenar o protocolo retornado.

                    if processo.webservice in CONSULTAR_SITUACAO_LOTE_RPS:
                        # Houve falha
                        if processo.resposta.lista_mensagem_retorno:
                            mensagem_completa = ""
                            lista_msgs = processo.resposta.lista_mensagem_retorno
                            for mr in lista_msgs.mensagem_retorno:
                                correcao = ""
                                if mr.correcao:
                                    correcao = mr.correcao
                                mensagem_completa += (
                                    mr.codigo
                                    + " - "
                                    + mr.mensagem
                                    + " - Correção: "
                                    + correcao
                                    + "\n"
                                )
                            vals["edoc_error_message"] = mensagem_completa
                            record._change_state(SITUACAO_EDOC_REJEITADA)

                        # Emissão com sucesso.
                        if processo.resposta.lista_nfse.compl_nfse:
                            record._save_nfse_data(
                                processo.resposta.lista_nfse.compl_nfse[0],
                                processo.retorno,
                            )
            record.write(vals)
        return

    def _save_nfse_data(self, compl_nfse, xml_file):
        self.ensure_one()
        self.document_number = compl_nfse.nfse.inf_nfse.numero
        self.authorization_date = (
            compl_nfse.nfse.inf_nfse.data_emissao.to_datetime().replace(tzinfo=None)
        )
        self.verify_code = compl_nfse.nfse.inf_nfse.codigo_verificacao
        self.nfse_preview_link = compl_nfse.nfse.inf_nfse.outras_informacoes
        self.authorization_event_id.set_done(
            status_code=None,
            response="NFS-e emitida com sucesso.",
            protocol_date=None,
            protocol_number=None,
            file_response_xml=xml_file,
        )
        self._change_state(SITUACAO_EDOC_AUTORIZADA)

    def _exec_before_SITUACAO_EDOC_CANCELADA(self, old_state, new_state):
        super()._exec_before_SITUACAO_EDOC_CANCELADA(old_state, new_state)
        return self.cancel_document_betha()
