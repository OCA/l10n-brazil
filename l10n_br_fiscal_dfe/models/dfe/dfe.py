# Copyright (C) 2023 KMEE Informatica LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
import gzip
import io
import logging
import re
import tempfile
from datetime import datetime

from erpbrasil.assinatura import certificado as cert
from erpbrasil.edoc.nfe import NFe as edoc_nfe
from erpbrasil.transmissao import TransmissaoSOAP
from lxml import objectify
from requests import Session

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DFe(models.Model):
    _name = "l10n_br_fiscal.dfe"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Consult DF-e"
    _order = "id desc"
    _rec_name = "display_name"

    display_name = fields.Char(compute="_compute_display_name")

    company_id = fields.Many2one(comodel_name="res.company", string="Company")

    last_nsu = fields.Char(string="Last NSU", size=25, default="0")

    last_query = fields.Datetime(string="Last query")

    recipient_xml_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.dfe_xml",
        inverse_name="dfe_id",
        string="XML Documents",
    )

    imported_document_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        inverse_name="dfe_id",
        string="Imported Documents",
    )

    imported_dfe_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.mde",
        inverse_name="dfe_id",
        string="Manifestações do Destinatário Importadas",
    )

    use_cron = fields.Boolean(
        default=False,
        string="Download new documents automatically",
        help="If activated, allows new manifestations to be automatically "
        "searched with a Cron",
    )

    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.company_id.name} - NSU: {record.last_nsu}"

    def action_manage_manifestations(self):
        return {
            "name": self.company_id.legal_name,
            "view_mode": "tree,form",
            "res_model": "l10n_br_fiscal.mde",
            "type": "ir.actions.act_window",
            "target": "current",
            "domain": [("company_id", "=", self.company_id.id)],
            "limit": self.env["l10n_br_fiscal.mde"].search_count(
                [("company_id", "=", self.company_id.id)]
            ),
        }

    def _get_certificate(self):
        certificate_id = self.company_id.certificate_nfe_id
        return cert.Certificado(
            arquivo=certificate_id.file,
            senha=certificate_id.password,
        )

    def _get_session(self):
        session = Session()
        session.verify = False

        return session

    def _get_processor(self):
        return edoc_nfe(
            TransmissaoSOAP(self._get_certificate(), self._get_session()),
            self.company_id.state_id.ibge_code,
            versao="1.01",
            ambiente=2,
        )

    def document_distribution(self):
        result = self._get_processor().consultar_distribuicao(
            cnpj_cpf=re.sub("[^0-9]", "", self.company_id.cnpj_cpf),
            ultimo_nsu=self._format_nsu(self.last_nsu),
        )

        if result.retorno.status_code != "200":
            return {
                "result": result,
                "message": result.resposta.xMotivo,
                "code": result.retorno.status_code,
                "file_sent": result.envio_xml,
                "file_returned": None,
            }

        if result.resposta.cStat not in ["137", "138"]:
            return {
                "result": result,
                "code": result.resposta.cStat,
                "message": result.resposta.xMotivo,
                "file_sent": result.envio_xml,
                "file_returned": result.retorno.text,
            }

        nfe_list = []
        if result.resposta.loteDistDFeInt:
            for doc in result.resposta.loteDistDFeInt.docZip:
                nfe_list.append(
                    {"xml": doc.valueOf_, "NSU": doc.NSU, "schema": doc.schema}
                )

        return {
            "result": result,
            "code": result.resposta.cStat,
            "file_returned": result.retorno.text,
            "list_nfe": nfe_list,
        }

    def parse_xml_document(self, doc_xml):
        """
        Converte um documento de XML para um objeto l10n_br_fiscal.document

        :param doc_xml: XML (str ou byte[]) do documento a ser convertido
        :return: Um novo objeto do modelo l10n_br_fiscal.document
        """

        from nfelib.v4_00 import leiauteNFe_sub as nfe_sub

        tmp_document = tempfile.NamedTemporaryFile(delete=True)
        tmp_document.seek(0)
        tmp_document.write(doc_xml)
        tmp_document.flush()

        obj = nfe_sub.parse(tmp_document.name)
        return (
            self.env["nfe.40.infnfe"]
            .with_context(tracking_disable=True)
            .build_from_binding(obj.infNFe)
        )

    def download_documents(self, mde_ids=None):
        """
        - Declara Ciência da Emissão para todas as manifestações já recebidas,
        - Realiza Download dos XMLs das NF-e
        - Cria um documento para cada XML importado

        :param mde_ids: Recordset de objetos l10n_br_fiscal.mde
        :return: Um recordset de l10n_br_fiscal.document instanciados
        """
        errors = []

        document_ids = self.env["l10n_br_fiscal.document"]
        if not mde_ids or isinstance(mde_ids, dict):
            mde_ids = self.env["l10n_br_fiscal.mde"].search(
                [("company_id", "=", self.company_id.id)]
            )

        for mde_id in mde_ids.filtered(lambda m: m.state not in ["pendente", "ciente"]):
            if mde_id.state == "pendente":
                try:
                    mde_id.action_ciencia_emissao()
                except Exception as e:
                    errors.append(("MDF-e", mde_id.id, e))

            nfe_result = self.download_nfe(mde_id.key)
            if nfe_result["code"] == "138":
                document_id = self.parse_xml_document(nfe_result["nfe"])
                mde_id.document_id = document_id
                document_ids += document_id
            else:
                errors.append(
                    (
                        "nfe",
                        False,
                        "{} - {}".format(
                            nfe_result.get("code", "???"), nfe_result.get("message", "")
                        ),
                    )
                )

        docs = document_ids.ids + self.imported_document_ids.ids
        self.imported_document_ids = [(6, False, docs)]
        return document_ids

    def _cron_search_documents(self, context=None):
        """Método chamado pelo agendador do sistema, processa
        automaticamente a busca de documentos conforme configuração do
        sistema.
        :param context:
        :return:
        """
        for consulta_id in self.env["l10n_br_fiscal.dfe"].search(
            [("use_cron", "=", True)]
        ):
            consulta_id.search_documents(raise_error=False)

    def search_documents(self, context=None, raise_error=True):
        nfe_mdes = []
        xml_ids = []
        for record in self:
            try:
                record.validate_document_configuration()
                nfe_result = record.document_distribution()
                record.last_query = fields.Datetime.now()
                _logger.info(
                    "%s.search_documents(), lastNSU: %s",
                    record.company_id.name,
                    record.last_nsu,
                )
            except Exception as e:
                _logger.error("Erro ao consultar Manifesto.\n%s" % e, exc_info=True)
                if raise_error:
                    raise UserError(_("Error on searching documents!\n '%s'") % e)
            else:
                if nfe_result["code"] not in ["137", "138"]:
                    if not nfe_result.get("code") and not nfe_result.get("message"):
                        raise ValidationError(
                            _(
                                "The service returned an incomprehensible answer. "
                                "Check the handling of the service response"
                            )
                        )

                    raise ValidationError(
                        _("{} - {}").format(
                            nfe_result.get("code", "???"), nfe_result.get("message", "")
                        )
                    )

                env_mde = self.env["l10n_br_fiscal.mde"]
                env_mde_xml = self.env["l10n_br_fiscal.dfe_xml"]

                xml_ids.append(
                    env_mde_xml.create(
                        {
                            "dfe_id": record.id,
                            "xml_type": "0",
                            # TODO: Inserir XML de fato. "envio_xml" é um
                            #  arquivo gz codificado em base64
                            "xml": nfe_result["result"].envio_xml,
                        }
                    ).id
                )
                xml_ids.append(
                    env_mde_xml.create(
                        {
                            "dfe_id": record.id,
                            "xml_type": "1",
                            # TODO: Inserir XML de fato. "retorno.text" é
                            #  um arquivo gz codificado em base64
                            "xml": nfe_result["result"].retorno.text,
                        }
                    ).id
                )
                xml_ids.append(
                    env_mde_xml.create(
                        {
                            "dfe_id": record.id,
                            "xml_type": "2",
                            # TODO: Obter o XML do loteDistDFeInt
                            # "xml": nfe_result[
                            #     "result"].resposta.loteDistDFeInt.xml
                        }
                    ).id
                )

                for nfe in nfe_result["list_nfe"]:
                    nsu_exists = env_mde.search(
                        [
                            ("nsu", "=", self._format_nsu(nfe["NSU"])),
                            ("company_id", "=", self.company_id.id),
                        ]
                    )

                    arq = io.BytesIO()
                    arq.write(base64.b64decode(nfe["xml"]))
                    arq.seek(0)

                    tmp_nfe_zip = gzip.GzipFile(mode="r", fileobj=arq)
                    nfe_xml = tmp_nfe_zip.read()

                    root = objectify.fromstring(nfe_xml)
                    self.last_nsu = nfe["NSU"]

                    if nfe["schema"] == "procNFe_v3.10.xsd" and not nsu_exists:
                        nfe_key = root.protNFe.infProt.chNFe
                        mde_id = env_mde.search([("key", "=", nfe_key)]).id

                        if mde_id and not mde_id.dfe_id:
                            mde_id.dfe_id = record.id

                        if not mde_id:
                            supplier_cnpj = record._mask_cnpj(
                                "%014d" % root.NFe.infNFe.emit.CNPJ
                            )
                            partner = self.env["res.partner"].search(
                                [("cnpj_cpf", "=", supplier_cnpj)]
                            )

                            obj_nfe = env_mde.create(
                                {
                                    "number": root.NFe.infNFe.ide.nNF,
                                    "key": nfe_key,
                                    "nsu": nfe["NSU"],
                                    "operation_type": str(root.NFe.infNFe.ide.tpNF),
                                    "document_value": root.NFe.infNFe.total.ICMSTot.vNF,
                                    "state": "pendente",
                                    "inclusion_datetime": datetime.now(),
                                    "cnpj_cpf": supplier_cnpj,
                                    "ie": root.NFe.infNFe.emit.IE,
                                    "partner_id": partner.id,
                                    "emission_datetime": datetime.strptime(
                                        str(root.NFe.infNFe.ide.dhEmi)[:19],
                                        "%Y-%m-%dT%H:%M:%S",
                                    ),
                                    "company_id": record.company.id,
                                    "dfe_id": record.id,
                                    "inclusion_mode": "Verificação agendada",
                                }
                            )
                            file_name = "resumo_nfe-%s.xml" % nfe["NSU"]
                            self.env["ir.attachment"].create(
                                {
                                    "name": file_name,
                                    "datas": base64.b64encode(nfe_xml),
                                    "datas_fname": file_name,
                                    "description": "NFe via manifest",
                                    "res_model": "l10n_br_fiscal.mde",
                                    "res_id": obj_nfe.id,
                                }
                            )

                            xml_ids.append(
                                env_mde_xml.create(
                                    {
                                        "dfe_id": record.id,
                                        "xml_type": "3",
                                        "xml": nfe["xml"],
                                    }
                                ).id
                            )

                    elif nfe["schema"] == "resNFe_v1.01.xsd" and not nsu_exists:
                        mde_id = env_mde.search([("key", "=", root.chNFe)])

                        if mde_id and not mde_id.dfe_id:
                            mde_id.dfe_id = record.id

                        if not mde_id:
                            supplier_cnpj = record._mask_cnpj("%014d" % root.CNPJ)
                            partner_id = self.env["res.partner"].search(
                                [("cnpj_cpf", "=", supplier_cnpj)]
                            )

                            obj_nfe = env_mde.create(
                                {
                                    "key": root.chNFe,
                                    "nsu": nfe["NSU"],
                                    "fornecedor": root.xNome,
                                    "operation_type": str(root.tpNF),
                                    "document_value": root.vNF,
                                    "situacao_nfe": str(root.cSitNFe),
                                    "state": "pendente",
                                    "inclusion_datetime": datetime.now(),
                                    "cnpj_cpf": supplier_cnpj,
                                    "ie": root.IE,
                                    "partner_id": partner_id.id,
                                    "emission_datetime": datetime.strptime(
                                        str(root.dhEmi)[:19], "%Y-%m-%dT%H:%M:%S"
                                    ),
                                    "company_id": record.company_id.id,
                                    "dfe_id": record.id,
                                    "inclusion_mode": "Verificação agendada -"
                                    " manifestada por outro app",
                                }
                            )
                            file_name = "resumo_nfe-%s.xml" % nfe["NSU"]
                            self.env["ir.attachment"].create(
                                {
                                    "name": file_name,
                                    "datas": base64.b64encode(nfe_xml),
                                    "datas_fname": file_name,
                                    "description": "NFe via manifesto",
                                    "res_model": "l10n_br_fiscal.mde",
                                    "res_id": obj_nfe.id,
                                }
                            )

                            xml_ids.append(
                                env_mde_xml.create(
                                    {
                                        "dfe_id": record.id,
                                        "xml_type": "3",
                                        "xml": nfe["xml"],
                                    }
                                ).id
                            )

                    nfe_mdes.append(nfe)

                self.write({"recipient_xml_ids": [(6, 0, xml_ids)]})

        return nfe_mdes

    def validate_document_configuration(self):
        missing_configs = []

        if not self.company_id.certificate_nfe_id.file:
            missing_configs.append(_("Company - NF-e A1 File"))
        if not self.company_id.certificate_nfe_id.password:
            missing_configs.append(_("Company - NF-e A1 Password"))

        if missing_configs:
            raise UserError(
                "The following configurations are missing\n\n".join(
                    [m for m in missing_configs]
                )
            )

    def send_event(self, nfe_key, method):
        self.validate_document_configuration(self.company_id)

        cnpj_partner = re.sub("[^0-9]", "", self.company_id.cnpj_cpf)
        processor = self._get_processor()
        EVENT_METHOD_TO_PROCESSOR_FUNCTION = {
            "ciencia_operacao": processor.ciencia_da_operacao,
            "confirma_operacao": processor.confirmacao_da_operacao,
            "desconhece_operacao": processor.desconhecimento_da_operacao,
            "nao_realizar_operacao": processor.operacao_nao_realizada,
            False: False,
        }

        result = EVENT_METHOD_TO_PROCESSOR_FUNCTION[method](nfe_key, cnpj_partner)

        if result.retorno.status_code != 200:
            return {
                "code": result.resposta.status,
                "message": result.resposta.reason,
                "file_sent": result.envio_xml,
                "file_returned": None,
            }

        if result.resposta.cStat == "128":
            inf_evento = result.resposta.retEvento[0].infEvento
            return {
                "code": inf_evento.cStat,
                "message": inf_evento.xMotivo,
                "file_sent": result.envio_xml,
                "file_returned": result.retorno.text,
            }

        else:
            return {
                "code": result.resposta.cStat,
                "message": result.resposta.xMotivo,
                "file_sent": result.envio_xml,
                "file_returned": result.retorno.text,
            }

    def download_nfe(self, nfe_key):
        self.validate_document_configuration()

        result = self._get_processor().consultar_distribuicao(
            cnpj_cpf=re.sub("[^0-9]", "", self.company_id.cnpj_cpf), chave=nfe_key
        )

        if result.retorno.status_code != 200:
            return {
                "code": result.resposta.status,
                "message": result.resposta.reason,
                "file_sent": result.envio_xml,
                "file_returned": None,
            }

        if result.resposta.cStat == "138":
            nfe_zip = result.resposta.loteDistDFeInt.docZip[0].valueOf_
            arq = io.BytesIO()
            arq.write(base64.b64decode(nfe_zip))
            arq.seek(0)

            orig_file_desc = gzip.GzipFile(mode="r", fileobj=arq)
            nfe = orig_file_desc.read()
            orig_file_desc.close()

            return {
                "code": result.resposta.cStat,
                "message": result.resposta.xMotivo,
                "file_sent": result.envio_xml,
                "file_returned": result.retorno.text,
                "nfe": nfe,
            }

        return {
            "code": result.resposta.cStat,
            "message": result.resposta.xMotivo,
            "file_sent": result.envio_xml,
            "file_returned": result.retorno.text,
        }

    @staticmethod
    def _mask_cnpj(cnpj):
        if cnpj:
            val = re.sub("[^0-9]", "", cnpj)
            if len(val) == 14:
                cnpj = "%s.%s.%s/%s-%s" % (
                    val[0:2],
                    val[2:5],
                    val[5:8],
                    val[8:12],
                    val[12:14],
                )
        return cnpj

    @staticmethod
    def _format_nsu(nsu):
        return str(nsu).zfill(15)


class DFeXML(models.Model):
    _name = "l10n_br_fiscal.dfe_xml"
    _description = "DF-e XML Document"

    dfe_id = fields.Many2one(
        string="DF-e Consult",
        comodel_name="l10n_br_fiscal.dfe",
    )

    xml_type = fields.Selection(
        selection=[
            ("0", "Envio"),
            ("1", "Resposta"),
            ("2", "Resposta-LoteDistDFeInt"),
            ("3", "Resposta-LoteDistDFeInt-DocZip(NFe)"),
        ],
        string="XML Type",
    )

    xml = fields.Char(
        string="XML",
        size=5000,
    )
