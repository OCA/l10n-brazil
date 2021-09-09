# Copyright (C) 2019  Renato Lima - Akretion
# Copyright (C) 2019  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    AUTORIZADO,
    CANCELADO,
    CANCELADO_DENTRO_PRAZO,
    CANCELADO_FORA_PRAZO,
    DENEGADO,
    SITUACAO_EDOC_AUTORIZADA,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    EVENTO_RECEBIDO,
    LOTE_PROCESSADO,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
)

def filter_processador_edoc_nfe(record):
    if record.processador_edoc == PROCESSADOR_OCA and record.document_type_id.code in [
        MODELO_FISCAL_NFE,
        MODELO_FISCAL_NFCE,
    ]:
        return True
    return False


class NFEletronic(models.AbstractModel):
    _name = "l10n_br_nfe.document.electronic"
    _description = "NF Eletronic Document"
    _inherit = "l10n_br_fiscal.document.electronic"

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.with_context({"lang": "pt_BR"}).filtered(
            filter_processador_edoc_nfe
        ):
            inf_nfe = record.export_ds()[0]

            tnfe = leiauteNFe.TNFe(infNFe=inf_nfe, infNFeSupl=None, Signature=None)
            tnfe.original_tagname_ = "NFe"

            edocs.append(tnfe)

        return edocs

    def _processador(self):
        if not self.company_id.certificate_nfe_id:
            raise UserError(_("Certificado não encontrado"))

        certificado = cert.Certificado(
            arquivo=self.company_id.certificate_nfe_id.file,
            senha=self.company_id.certificate_nfe_id.password,
        )
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(certificado, session)
        return edoc_nfe(
            transmissao,
            self.company_id.state_id.ibge_code,
            versao=self.nfe_version,
            ambiente=self.nfe_environment,
        )

    @api.multi
    def _document_export(self, pretty_print=True):
        super()._document_export()
        for record in self.filtered(filter_processador_edoc_nfe):
            record._export_fields_pagamentos()
            edoc = record.serialize()[0]
            processador = record._processador()
            xml_file = processador._generateds_to_string_etree(
                edoc, pretty_print=pretty_print
            )[0]
            _logger.debug(xml_file)
            event_id = self.event_ids.create_event_save_xml(
                company_id=self.company_id,
                environment=(
                    EVENT_ENV_PROD if self.nfe_environment == "1" else EVENT_ENV_HML
                ),
                event_type="0",
                xml_file=xml_file,
                document_id=self,
            )
            record.authorization_event_id = event_id

    def atualiza_status_nfe(self, infProt, xml_file):
        self.ensure_one()
        # TODO: Verificar a consulta de notas
        # if not infProt.chNFe == self.key:
        #     self = self.search([
        #         ('key', '=', infProt.chNFe)
        #     ])
        if infProt.cStat in AUTORIZADO:
            state = SITUACAO_EDOC_AUTORIZADA
        elif infProt.cStat in DENEGADO:
            state = SITUACAO_EDOC_DENEGADA
        else:
            state = SITUACAO_EDOC_REJEITADA
        if self.authorization_event_id and infProt.nProt:
            if type(infProt.dhRecbto) == datetime:
                protocol_date = fields.Datetime.to_string(infProt.dhRecbto)
            else:
                protocol_date = fields.Datetime.to_string(
                    datetime.fromisoformat(infProt.dhRecbto)
                )

            self.authorization_event_id.set_done(
                status_code=infProt.cStat,
                response=infProt.xMotivo,
                protocol_date=protocol_date,
                protocol_number=infProt.nProt,
                file_response_xml=xml_file,
            )
        self.write(
            {
                "status_code": infProt.cStat,
                "status_name": infProt.xMotivo,
            }
        )
        self._change_state(state)

    @api.multi
    def _eletronic_document_send(self):
        super()._eletronic_document_send()
        for record in self.filtered(filter_processador_edoc_nfe):
            record._export_fields_pagamentos()
            processador = record._processador()
            for edoc in record.serialize():
                processo = None
                for p in processador.processar_documento(edoc):
                    processo = p
                    if processo.webservice == "nfeAutorizacaoLote":
                        record.authorization_event_id._save_event_file(
                            processo.envio_xml.decode("utf-8"), "xml"
                        )

            if processo.resposta.cStat in LOTE_PROCESSADO + ["100"]:
                record.atualiza_status_nfe(
                    processo.protocolo.infProt, processo.processo_xml.decode("utf-8")
                )
                if processo.protocolo.infProt.cStat in AUTORIZADO:
                    try:
                        record.make_pdf()
                    except Exception as e:
                        # Não devemos interromper o fluxo
                        # E dar rollback em um documento
                        # autorizado, podendo perder dados.

                        # Se der problema que apareça quando
                        # o usuário clicar no gera PDF novamente.
                        _logger.error("DANFE Error \n {}".format(e))

            elif processo.resposta.cStat == "225":
                state = SITUACAO_EDOC_REJEITADA

                self._change_state(state)

                self.write(
                    {
                        "status_code": processo.resposta.cStat,
                        "status_name": processo.resposta.xMotivo,
                    }
                )
        return

    def temp_xml_autorizacao(self, xml_string):
        """ TODO: Migrate-me to erpbrasil.edoc.pdf ASAP"""
        root = etree.fromstring(xml_string)
        ns = {None: "http://www.portalfiscal.inf.br/nfe"}
        new_root = etree.Element("nfeProc", nsmap=ns)

        protNFe_node = etree.Element("protNFe")
        infProt = etree.SubElement(protNFe_node, "infProt")
        etree.SubElement(infProt, "tpAmb").text = "2"
        etree.SubElement(infProt, "verAplic").text = ""
        etree.SubElement(infProt, "dhRecbto").text = None
        etree.SubElement(infProt, "nProt").text = ""
        etree.SubElement(infProt, "digVal").text = ""
        etree.SubElement(infProt, "cStat").text = ""
        etree.SubElement(infProt, "xMotivo").text = ""

        new_root.append(root)
        new_root.append(protNFe_node)
        return etree.tostring(new_root)

    def _document_cancel(self, justificative):
        super()._document_cancel(justificative)
        online_event = self.filtered(filter_processador_edoc_nfe)
        if online_event:
            online_event._nfe_cancel()

    def _nfe_cancel(self):
        self.ensure_one()
        processador = self._processador()

        if not self.authorization_protocol:
            raise UserError(_("Authorization Protocol Not Found!"))

        evento = processador.cancela_documento(
            chave=self.document_key[3:],
            protocolo_autorizacao=self.authorization_protocol,
            justificativa=self.cancel_reason.replace("\n", "\\n"),
        )
        processo = processador.enviar_lote_evento(lista_eventos=[evento])
        # Gravamos o arquivo no disco e no filestore ASAP.

        self.cancel_event_id = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=(
                EVENT_ENV_PROD if self.nfe_environment == "1" else EVENT_ENV_HML
            ),
            event_type="2",
            xml_file=processo.envio_xml.decode("utf-8"),
            document_id=self,
        )

        for retevento in processo.resposta.retEvento:
            if not retevento.infEvento.chNFe == self.document_key[3:]:
                continue

            if retevento.infEvento.cStat not in CANCELADO:
                mensagem = "Erro no cancelamento"
                mensagem += "\nCódigo: " + retevento.infEvento.cStat
                mensagem += "\nMotivo: " + retevento.infEvento.xMotivo
                raise UserError(mensagem)

            if retevento.infEvento.cStat == CANCELADO_FORA_PRAZO:
                self.state_fiscal = SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO
            elif retevento.infEvento.cStat == CANCELADO_DENTRO_PRAZO:
                self.state_fiscal = SITUACAO_FISCAL_CANCELADO

            self.state_edoc = SITUACAO_EDOC_CANCELADA
            self.cancel_event_id.set_done(
                status_code=retevento.infEvento.cStat,
                response=retevento.infEvento.xMotivo,
                protocol_date=fields.Datetime.to_string(
                    datetime.fromisoformat(retevento.infEvento.dhRegEvento)
                ),
                protocol_number=retevento.infEvento.nProt,
                file_response_xml=processo.retorno.content.decode("utf-8"),
            )

    def _document_correction(self, justificative):
        super()._document_correction(justificative)
        online_event = self.filtered(filter_processador_edoc_nfe)
        if online_event:
            online_event._nfe_correction(justificative)

    def _nfe_correction(self, justificative):
        self.ensure_one()
        processador = self._processador()

        numeros = self.event_ids.filtered(
            lambda e: e.type == "14" and e.state == "done"
        ).mapped("sequence")

        sequence = str(int(max(numeros)) + 1) if numeros else "1"

        evento = processador.carta_correcao(
            chave=self.document_key[3:],
            sequencia=sequence,
            justificativa=justificative.replace("\n", "\\n"),
        )
        processo = processador.enviar_lote_evento(lista_eventos=[evento])
        # Gravamos o arquivo no disco e no filestore ASAP.
        event_id = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=(
                EVENT_ENV_PROD if self.nfe_environment == "1" else EVENT_ENV_HML
            ),
            event_type="14",
            xml_file=processo.envio_xml.decode("utf-8"),
            document_id=self,
            sequence=sequence,
            justification=justificative,
        )
        for retevento in processo.resposta.retEvento:
            if not retevento.infEvento.chNFe == self.document_key[3:]:
                continue

            if retevento.infEvento.cStat not in EVENTO_RECEBIDO:
                mensagem = "Erro na carta de correção"
                mensagem += "\nCódigo: " + retevento.infEvento.cStat
                mensagem += "\nMotivo: " + retevento.infEvento.xMotivo
                raise UserError(mensagem)

            event_id.set_done(
                status_code=retevento.infEvento.cStat,
                response=retevento.infEvento.xMotivo,
                protocol_date=fields.Datetime.to_string(
                    datetime.fromisoformat(retevento.infEvento.dhRegEvento)
                ),
                protocol_number=retevento.infEvento.nProt,
                file_response_xml=processo.retorno.content.decode("utf-8"),
            )
    
    def view_pdf(self):
        if not self.filtered(filter_processador_edoc_nfe):
            return super().view_pdf()
        if not self.authorization_file_id or not self.file_report_id:
            self.make_pdf()
        return self._target_new_tab(self.file_report_id)

    def make_pdf(self):
        if not self.filtered(filter_processador_edoc_nfe):
            return super().make_pdf()

        file_pdf = self.file_report_id
        self.file_report_id = False
        file_pdf.unlink()

        if self.authorization_file_id:
            arquivo = self.authorization_file_id
            xml_string = base64.b64decode(arquivo.datas).decode()
        else:
            arquivo = self.send_file_id
            xml_string = base64.b64decode(arquivo.datas).decode()
            xml_string = self.temp_xml_autorizacao(xml_string)

        pdf = base.ImprimirXml.imprimir(
            string_xml=xml_string,
            # output_dir=self.authorization_event_id.file_path
        )
        # TODO: Alterar a opção output_dir para devolter também o arquivo do XML
        # no retorno, evitando a releitura do arquivo.

        self.file_report_id = self.env["ir.attachment"].create(
            {
                "name": self.document_key + ".pdf",
                "datas_fname": self.document_key + ".pdf",
                "res_model": self._name,
                "res_id": self.id,
                "datas": base64.b64encode(pdf),
                "mimetype": "application/pdf",
                "type": "binary",
            }
        )