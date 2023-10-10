# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import xml.etree.cElementTree as xml
from odoo import _, models
from odoo.exceptions import UserError
import requests
import base64
from lxml import etree
from collections import Mapping
from dicttoxml import dicttoxml
from requests import Session

from erpbrasil.assinatura import certificado as cert
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    MODELO_FISCAL_NFSE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_REJEITADA,
)


def filter_focusnfe(record):
    if record.company_id.provedor_nfse == "focusnfe":
        return True
    return False

def filter_processador_edoc_nfse(record):
    if record.processador_edoc == PROCESSADOR_OCA and record.document_type_id.code in [
        MODELO_FISCAL_NFSE,
    ]:
        return True
    return False

class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _serialize(self, edocs):
        return self.serialize_focusnfe()

    def _serialize_focusnfe_dados_servico(self):
        self.fiscal_line_ids.ensure_one()
        dados = self._prepare_dados_servico()
        res = {
            "valor_servicos": dados["valor_servicos"],
            "valor_deducoes": dados["valor_deducoes"],
            "valor_pis": dados["valor_pis"],
            "valor_cofins": dados["valor_cofins"],
            "valor_inss": dados["valor_inss"],
            "valor_ir": dados["valor_ir"],
            "valor_csll": dados["valor_csll"],
            "iss_retido": dados["iss_retido"],
            "valor_iss": dados["valor_iss"],
            "valor_iss_retido": dados["valor_iss_retido"],
            "outras_retencoes": dados["outras_retencoes"],
            "base_calculo": dados["base_calculo"],
            "aliquota": dados["aliquota"],
            "desconto_incondicionado": "",
            "desconto_condicionado": "",
            "item_lista_servico": dados["item_lista_servico"],
            "codigo_cnae": dados["codigo_cnae"],
            "codigo_tributario_municipio": "",
            "discriminacao": dados["discriminacao"],
            "codigo_municipio": dados["codigo_municipio"],
            "percentual_total_tributos": "",
            "fonte_total_tributos": "",
        }
        return res

    def _serialize_focusnfe_dados_tomador(self):
        dados = self._prepare_dados_tomador()
        res = {
            "cpf": dados["cpf"],
            "cnpj": dados["cnpj"],
            "inscricao_municipal": dados["inscricao_municipal"],
            "razao_social": dados["razao_social"],
            "endereco": {
                "logradouro": dados["endereco"],
                "numero": dados["numero"],
                "complemento": dados["complemento"],
                "bairro": dados["bairro"],
                "codigo_municipio": dados["codigo_municipio"],
                "uf": dados["uf"],
                "cep": dados["cep"],
            },
        }

        return res

    def _serialize_focusnfe_lote_rps(self):
        dados = self._prepare_lote_rps()
        res = {
            "cnpj": dados["cnpj"],
            "inscricao_municipal": dados["inscricao_municipal"],
            "quantidade_rps": 1,
            "lista_rps": [self._serialize_focusnfe_rps(dados)],
        }
        return res

    def _serialize_focusnfe_rps(self, dados):
        res = {
          "data_emissao": dados["date_in_out"],
            "natureza_operacao": dados["natureza_operacao"],
            "regime_especial_tributacao": dados["regime_especial_tributacao"],
            "optante_simples_nacional": dados["optante_simples_nacional"],
            "incentivador_cultural": dados["incentivador_cultural"],
            "codigo_obra": dados["construcao_civil"],
            "art": "",
            "numero_rps_substituido": dados["numero"],
            "serie_rps_substituido": dados["serie"],
            "tipo_rps_substituido": dados["tipo"],
            "servico": self._serialize_focusnfe_dados_servico(),
            "prestador": {
                "cnpj": dados["cnpj"],
                "inscricao_municipal": dados["inscricao_municipal"],
                "codigo_municipio": self._serialize_focusnfe_dados_servico()["codigo_municipio"],
            },
            "tomador": self._serialize_focusnfe_dados_tomador(),
            "intermediario": dados["intermediario_servico"],
        }

        return res

    def serialize_focusnfe(self):
        lote_rps = self._serialize_focusnfe_lote_rps()
        return lote_rps

    # def _eletronic_document_send(self):
    # super()._eletronic_document_send()
    # for record in self.filtered(filter_oca_nfse).filtered(filter_focusnfe):
    # protocolo = record.authorization_protocol
    # vals = dict()

    def view_xml(self):
        self.ensure_one()
        xml_file = self.authorization_file_id or self.send_file_id
        if not xml_file:
            self._document_export()
            xml_file = self.authorization_file_id or self.send_file_id
        if not xml_file:
            raise UserError(_("No XML file generated!"))
        return self._target_new_tab(xml_file)

    def _eletronic_document_send(self):
        super()._eletronic_document_send()
    
    def _processador_focus_nfse(self):
        certificado  = cert.Certificado(
            arquivo=self.company_id.certificate_nfe_id.file,
            senha=self.company_id.certificate_nfe_id.password,
        )
        session = Session()
        session.verify = False
        # transmissao = TransmissaoSOAP(certificado, session)
    
    def _generatejson_to_string_etree(self, json_file):
        xml = dicttoxml(json_file, custom_root='EnviarLoteRpsEnvio', attr_type=False)
        return str(xml, 'UTF-8')
    
    def _document_export(self, pretty_print=True):
        # result = super(Document, self)._document_export()
        for record in self.filtered(filter_processador_edoc_nfse):
            if self.company_id.provedor_nfse == "focusnfe": 
                # processador = record._processador_focus_nfse()
                json_file = record._serialize_focusnfe_lote_rps()    
                xml_file = record._generatejson_to_string_etree(json_file)
                event_id = self.event_ids.create_event_save_xml(
                    company_id=self.company_id,
                    environment=(
                        EVENT_ENV_PROD
                        if self.nfse_environment == "1"
                        else EVENT_ENV_HML
                    ),
                    event_type="0",
                    xml_file=xml_file,
                    document_id=self,
                )
                record.make_pdf()
                result = xml_file
            else:
                result = super(Document, self)._document_export()
        return result