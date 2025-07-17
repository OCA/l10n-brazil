# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

from erpbrasil.base import misc
from erpbrasil.edoc.provedores.cidades import NFSeFactory
from erpbrasil.transmissao import TransmissaoSOAP
from requests import Session

from odoo import fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    MODELO_FISCAL_NFSE,
    PROCESSADOR_OCA,
    TAX_FRAMEWORK_SIMPLES_ALL,
)

from ..constants.nfse import (
    NFSE_ENVIRONMENTS,
    OPERATION_NATURE,
    RPS_TYPE,
    TAXATION_SPECIAL_REGIME,
)

_logger = logging.getLogger(__name__)


def filter_processador_edoc_nfse(record):
    if record.processador_edoc == PROCESSADOR_OCA and record.document_type_id.code in [
        MODELO_FISCAL_NFSE,
    ]:
        return True
    return False


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    edoc_error_message = fields.Text(
        readonly=True,
        copy=False,
    )

    rps_type = fields.Selection(
        selection=RPS_TYPE,
        default="1",
    )
    operation_nature = fields.Selection(
        selection=OPERATION_NATURE,
        default="1",
    )
    taxation_special_regime = fields.Selection(
        selection=TAXATION_SPECIAL_REGIME,
        default="1",
    )
    verify_code = fields.Char(
        copy=False,
    )
    nfse_environment = fields.Selection(
        selection=NFSE_ENVIRONMENTS,
        string="NFSe Environment",
        default=lambda self: self.env.company.nfse_environment,
    )

    civil_construction_code = fields.Char()
    civil_construction_art = fields.Char(
        string="Civil Construction ART",
    )

    def make_pdf(self):
        if not self.filtered(filter_processador_edoc_nfse):
            return super().make_pdf()
        pdf = self.env.ref("l10n_br_nfse.report_br_nfse_danfe")._render_qweb_pdf(
            self.ids
        )[0]

        if self.document_number:
            filename = "NFS-e-" + self.document_number + ".pdf"
        else:
            filename = "RPS-" + self.rps_number + ".pdf"

        vals_dict = {
            "name": filename,
            "res_model": self._name,
            "res_id": self.id,
            "datas": base64.b64encode(pdf),
            "mimetype": "application/pdf",
            "type": "binary",
        }
        if self.file_report_id:
            self.file_report_id.write(vals_dict)
        else:
            self.file_report_id = self.env["ir.attachment"].create(vals_dict)

    def _processador_erpbrasil_nfse(self):
        certificado = self.env.company._get_br_ecertificate()
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(certificado, session)
        return NFSeFactory(
            transmissao=transmissao,
            ambiente=self.nfse_environment,
            cidade_ibge=int(self.company_id.partner_id.city_id.ibge_code),
            cnpj_prestador=misc.punctuation_rm(self.company_id.partner_id.cnpj_cpf),
            im_prestador=misc.punctuation_rm(
                self.company_id.partner_id.l10n_br_im_code or ""
            ),
        )

    def _document_export(self, pretty_print=True):
        result = super()._document_export()
        for record in self.filtered(filter_processador_edoc_nfse):
            if record.company_id.provedor_nfse:
                edoc = record.serialize()[0]
                processador = record._processador_erpbrasil_nfse()
                xml_file = processador._generateds_to_string_etree(
                    edoc, pretty_print=pretty_print
                )[0]
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
                _logger.debug(xml_file)
                record.authorization_event_id = event_id
                record.make_pdf()
        return result

    def _prepare_dados_servico(self):
        lines = self.env["l10n_br_fiscal.document.line"]
        for line in self.fiscal_line_ids:
            if line.product_id:
                lines |= line

        result_line = {}

        valor_servicos = 0
        valor_deducoes = 0
        valor_pis = 0
        valor_pis_retido = 0
        valor_cofins = 0
        valor_cofins_retido = 0
        valor_inss = 0
        valor_inss_retido = 0
        valor_ir = 0
        valor_ir_retido = 0
        valor_csll = 0
        valor_csll_retido = 0
        valor_iss = 0
        valor_iss_retido = 0
        outras_retencoes = 0
        base_calculo = 0
        valor_liquido_nfse = 0
        valor_desconto_incondicionado = 0

        for line in lines:
            result_line.update(line.prepare_line_servico())
            valor_servicos += result_line.get("valor_servicos")
            valor_deducoes += result_line.get("valor_deducoes")
            valor_pis += result_line.get("valor_pis")
            valor_pis_retido += result_line.get("valor_pis_retido")
            valor_cofins += result_line.get("valor_cofins")
            valor_cofins_retido += result_line.get("valor_cofins_retido")
            valor_inss += result_line.get("valor_inss")
            valor_inss_retido += result_line.get("valor_inss_retido")
            valor_ir += result_line.get("valor_ir")
            valor_ir_retido += result_line.get("valor_ir_retido")
            valor_csll += result_line.get("valor_csll")
            valor_csll_retido += result_line.get("valor_csll_retido")
            valor_iss += result_line.get("valor_iss")
            valor_iss_retido += result_line.get("valor_iss_retido")
            outras_retencoes += result_line.get("outras_retencoes")
            base_calculo += result_line.get("base_calculo")
            valor_liquido_nfse += result_line.get("valor_liquido_nfse")
            valor_desconto_incondicionado += result_line.get(
                "valor_desconto_incondicionado"
            )

        result = {
            "valor_servicos": valor_servicos,
            "valor_deducoes": valor_deducoes,
            "valor_pis": valor_pis,
            "valor_pis_retido": valor_pis_retido,
            "valor_cofins": valor_cofins,
            "valor_cofins_retido": valor_cofins_retido,
            "valor_inss": valor_inss,
            "valor_inss_retido": valor_inss_retido,
            "valor_ir": valor_ir,
            "valor_ir_retido": valor_ir_retido,
            "valor_csll": valor_csll,
            "valor_csll_retido": valor_csll_retido,
            "iss_retido": "1" if self.fiscal_line_ids[0].issqn_wh_percent else "2",
            "valor_iss": valor_iss,
            "valor_iss_retido": valor_iss_retido,
            "outras_retencoes": outras_retencoes,
            "base_calculo": base_calculo,
            "aliquota": (self.fiscal_line_ids[0].issqn_percent / 100)
            or (self.fiscal_line_ids[0].issqn_wh_percent / 100),
            "valor_liquido_nfse": valor_liquido_nfse,
            "item_lista_servico": self.fiscal_line_ids[0].service_type_id.code
            and self.fiscal_line_ids[0].service_type_id.code.replace(".", ""),
            "codigo_tributacao_municipio": self.fiscal_line_ids[
                0
            ].city_taxation_code_id.code
            or "",
            "municipio_prestacao_servico": self.fiscal_line_ids[
                0
            ].issqn_fg_city_id.ibge_code
            or "",
            "discriminacao": str(self.fiscal_line_ids[0].name[:2000] or ""),
            "codigo_cnae": misc.punctuation_rm(self.fiscal_line_ids[0].cnae_id.code)
            or None,
            "valor_desconto_incondicionado": valor_desconto_incondicionado,
        }

        result.update(self.company_id.prepare_company_servico())

        return result

    def _prepare_dados_tomador(self):
        result = self.partner_id.prepare_partner_tomador(self.company_id.country_id.id)

        result.update({"complemento": self.partner_shipping_id.street2 or None})

        return result

    def _prepare_lote_rps(self):
        num_rps = self.rps_number
        return {
            "cnpj": misc.punctuation_rm(self.company_id.partner_id.cnpj_cpf),
            "inscricao_municipal": misc.punctuation_rm(
                self.company_id.partner_id.l10n_br_im_code or ""
            )
            or None,
            "id": "rps" + str(num_rps),
            "numero": num_rps,
            "serie": self.document_serie_id.code or "",
            "tipo": self.rps_type,
            "data_emissao": fields.Datetime.context_timestamp(
                self, fields.Datetime.from_string(self.document_date)
            ).strftime("%Y-%m-%dT%H:%M:%S"),
            "date_in_out": fields.Datetime.context_timestamp(
                self, self.date_in_out
            ).strftime("%Y-%m-%dT%H:%M:%S"),
            "natureza_operacao": self.operation_nature,
            "regime_especial_tributacao": self.taxation_special_regime,
            "optante_simples_nacional": "1"
            if self.company_id.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL
            else "2",
            "incentivador_cultural": "1" if self.company_id.cultural_sponsor else "2",
            "status": "1",
            "rps_substitiuido": None,
            "intermediario_servico": None,
            "codigo_obra": self.civil_construction_code or "",
            "art": self.civil_construction_art or "",
            "carga_tributaria": self.amount_tax,
            "total_recebido": self.amount_price_gross,
            "carga_tributaria_estimada": self.amount_estimate_tax,
            "customer_additional_data": self.customer_additional_data,
            "fiscal_additional_data": self.fiscal_additional_data,
        }

    def convert_type_nfselib(self, class_object, object_filed, value):
        if value is None:
            return value

        value_type = ""
        for field in class_object().member_data_items_:
            if field.name == object_filed:
                value_type = field.child_attrs.get("type", "").replace("xsd:", "")
                break

        if value_type in ("int", "byte", "nonNegativeInteger"):
            return int(value)
        elif value_type == "decimal":
            return float(value)
        elif value_type == "string":
            return str(value)
        else:
            return value
