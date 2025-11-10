# Copyright 2023 - KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import unicodedata
from decimal import Decimal

from nfselib.barueri.NFeLoteEnviarArquivo import NFeLoteEnviarArquivo
from nfselib.barueri.rps import (
    RPS,
    RegistroTipo1,
    RegistroTipo2,
    RegistroTipo3,
    RegistroTipo9,
)

from odoo import _, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFSE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_REJEITADA,
)

from ..constants.barueri import CONSULTAR_NFSE_POR_RPS, CONSULTAR_SITUACAO_LOTE_RPS


def filter_oca_nfse(record):
    if record.processador_edoc == PROCESSADOR_OCA and record.document_type_id.code in [
        MODELO_FISCAL_NFSE,
    ]:
        return True
    return False


def filter_barueri(record):
    if record.company_id.provedor_nfse == "barueri":
        return True
    return False


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_oca_nfse).filtered(filter_barueri):
            edocs.append(record.serialize_nfse_barueri())
        return edocs

    def _serialize_barueri_dados_servico(self):
        self.fiscal_line_ids.ensure_one()
        dados = self._prepare_dados_servico()
        return dados

    def _serialize_barueri_dados_tomador(self):
        dados = self._prepare_dados_tomador()
        return dados

    def formata_cpf_cnpj(self, valor):
        if not valor:
            return "0" * 14

        # Garante string
        valor = str(valor).strip()

        # Se vier com espaços, remove
        valor = valor.replace(" ", "")

        # Se vier com máscara (nunca se sabe), remove qualquer não dígito
        valor = "".join(ch for ch in valor if ch.isdigit())

        # Agora já está limpo
        if len(valor) == 14:
            return valor

        if len(valor) == 11:
            return valor.zfill(14)
        return valor.zfill(14)

    def discrimina(self):
        partes = []

        if self.customer_additional_data:
            partes.append(f"Pedido: {self.customer_additional_data}")
        if self.amount_total:
            partes.append(f"Valor Total: {self.amount_total:.2f}")
        if self.fiscal_additional_data:
            partes.append(f"Descricao do Servico: {self.fiscal_additional_data}")
        if self.customer_additional_data:
            partes.append(f"Obs Cliente: {self.customer_additional_data}")
        if self.document_date:
            partes.append(f"Data: {self.document_date.strftime('%d/%m/%Y')}")
            partes.append(f"Competencia: {self.document_date.strftime('%m/%Y')}")
        if self.partner_city_id:
            partes.append(f"Cidade Tomador: {self.partner_city_id.name}")
        if self.partner_phone:
            partes.append(f"Telefone: {self.partner_phone}")
        if self.partner_id.email:
            partes.append(f"Email Tomador: {self.partner_id.email}")
        if self.amount_pis_value or self.amount_cofins_value or self.amount_issqn_value:
            partes.append(
                f"Impostos: "
                f"PIS {self.amount_pis_value or 0:.2f} | "
                f"COFINS {self.amount_cofins_value or 0:.2f} | "
                f"ISS {self.amount_issqn_value or 0:.2f}"
            )
        if self.manual_fiscal_additional_data:
            partes.append(f"Obs: {self.manual_fiscal_additional_data}")

        texto = "|".join(partes)
        texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()

        return texto[:1000]

    def _serialize_barueri_lote_rps(self):
        dados = self._prepare_lote_rps()
        dados_servico = self._serialize_barueri_dados_servico()
        dados_tomador = self._serialize_barueri_dados_tomador()
        # Registro tipo 1 - Cabeçalho do arquivo RPS
        registro_tipo1 = RegistroTipo1()
        registro_tipo1.TipoRegistro = 1
        registro_tipo1.InscricaoContribuinte = "4BA3842"
        registro_tipo1.InicioPeriodo = (
            dados["data_emissao"].split("T")[0].replace("-", "")
        )
        registro_tipo1.TerminoPeriodo = (
            dados["date_in_out"].split("T")[0].replace("-", "")
        )
        registro_tipo1.VersaoLayout = "PMB002"
        registro_tipo1.IdentificacaoRemessaContribuinte = "00092864189"
        # Registro tipo 2 - Dados do RPS
        registro_tipo2 = RegistroTipo2()
        registro_tipo2.TipoRegistro = 2
        registro_tipo2.SerieNFe = ""
        registro_tipo2.NumeroNFe = dados["numero"]
        registro_tipo2.DataNFe = dados["data_emissao"].split("T")[0].replace("-", "")
        registro_tipo2.HoraNFe = dados["data_emissao"].split("T")[1].replace(":", "")
        registro_tipo2.SerieRPS = ""
        registro_tipo2.NumeroRPS = self.rps_number
        registro_tipo2.CodigoAutenticidade = ""
        registro_tipo2.Tributacao = 3
        registro_tipo2.ISSRetido = "N"
        registro_tipo2.SituacaoNFe = "A"
        registro_tipo2.DataCancelamento = ""
        registro_tipo2.NumeroGuia = 0
        registro_tipo2.DataPagamentoGuia = ""
        cnpj = dados_tomador.get("cnpj") or ""
        cpf = dados_tomador.get("cpf") or ""
        valor = cnpj if cnpj else cpf
        registro_tipo2.CPFCNPJTomador = self.formata_cpf_cnpj(valor)
        registro_tipo2.RazaoSocialNomeTomador = dados_tomador["razao_social"]
        registro_tipo2.EnderecoLogradouroTomador = "R Pedra Sabao"
        registro_tipo2.NumeroLogradouroTomador = dados_tomador["numero"]
        registro_tipo2.ComplementoLogradouroTomador = dados_tomador["complemento"]
        registro_tipo2.BairroLogradouroTomador = dados_tomador["bairro"]
        registro_tipo2.CidadeLogradouroTomador = dados_tomador["descricao_municipio"]
        registro_tipo2.UFLogradouroTomador = dados_tomador["uf"]
        registro_tipo2.CEPLogradouroTomador = dados_tomador["cep"]
        registro_tipo2.PaisLogradouroTomador = "Brasil"
        registro_tipo2.EmailTomador = "palomafernades@gmail.com"  # teste isso
        registro_tipo2.DiscriminacaoServico = self.discrimina()
        # Registro tipo 3 - Valores do serviço
        registro_tipo3 = RegistroTipo3()
        registro_tipo3.TipoRegistro = 3
        registro_tipo3.QuantidadeServico = 1
        registro_tipo3.DescricaoServico = dados_servico["discriminacao"]
        registro_tipo3.CodigoServico = "000001712"
        valor = Decimal(str(dados_servico["valor_servicos"]).replace(",", "."))
        registro_tipo3.ValorUnitarioServico = str(int(valor * 100)).rjust(15, "0")
        aliquota = Decimal(str(dados_servico["aliquota"])).quantize(Decimal("0.0000"))
        registro_tipo3.AliquotaServico = str(int(aliquota * 10000)).rjust(4, "0")
        # RegistroTipo4 - Informações adicionais do RPS
        # registro_tipo4 = RegistroTipo4()
        # registro_tipo4.CodigoOutrosValores
        # registro_tipo4.TipoRegistro = 4
        # registro_tipo4.Valor = dados_servico["valor_servicos"]
        # Registro tipo 9 - Rodapé do arquivo RPS
        registro_tipo9 = RegistroTipo9()
        registro_tipo9.TipoRegistro = 9
        registro_tipo9.NumeroTotalLinhas = "0000004"
        registro_tipo9.ValorTotalServicos = "000000000100"
        registro_tipo9.ValorTotalValores = "00000000000000102"
        rps = RPS(
            [registro_tipo1, registro_tipo2, registro_tipo3, registro_tipo9]
        ).exportar()

        if isinstance(rps, str):
            rps = rps.encode("utf-8")
        if not isinstance(rps, bytes):
            raise ValueError(
                "O conteúdo fornecido para a codificação base64 não está em formato"
                " de bytes."
            )

        rps = base64.b64encode(rps)
        return rps

    def serialize_nfse_barueri(self):
        lote_rps = NFeLoteEnviarArquivo(
            InscricaoMunicipal=self.convert_type_nfselib(
                NFeLoteEnviarArquivo, "InscricaoMunicipal", self.company_inscr_mun
            ),
            CPFCNPJContrib=self.convert_type_nfselib(
                NFeLoteEnviarArquivo,
                "CPFCNPJContrib",
                "".join([char for char in self.company_cnpj_cpf if char.isdigit()]),
            ),
            NomeArquivoRPS=self.convert_type_nfselib(
                NFeLoteEnviarArquivo,
                "NomeArquivoRPS",
                "{}{}".format(self.display_name, ".txt"),
            ),
            ApenasValidaArq=self.convert_type_nfselib(
                NFeLoteEnviarArquivo, "ApenasValidaArq", False
            ),
            ArquivoRPSBase64=self.convert_type_nfselib(
                NFeLoteEnviarArquivo,
                "ArquivoRPSBase64",
                self._serialize_barueri_lote_rps(),
            ),
        )
        return lote_rps

    def _document_status(self):
        status = super()._document_status()
        for record in self.filtered(filter_oca_nfse).filtered(filter_barueri):
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

                if processo.webservice in CONSULTAR_NFSE_POR_RPS:
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
        for record in self.filtered(filter_oca_nfse).filtered(filter_barueri):
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
