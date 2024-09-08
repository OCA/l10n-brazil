# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import re
import string
import threading
from datetime import datetime

from erpbrasil.base.fiscal import cnpj_cpf
from erpbrasil.base.fiscal.edoc import ChaveEdoc
from erpbrasil.transmissao import TransmissaoSOAP
from lxml import etree
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc
from nfelib.nfe.bindings.v4_0.nfe_v4_00 import Nfe
from nfelib.nfe.ws.edoc_legacy import NFCeAdapter as edoc_nfce
from nfelib.nfe.ws.edoc_legacy import NFeAdapter as edoc_nfe
from requests import Session
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.models.datatype import XmlDateTime

from odoo import _, api, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    AUTORIZADO,
    CANCELADO,
    CANCELADO_DENTRO_PRAZO,
    CANCELADO_FORA_PRAZO,
    DENEGADO,
    DOCUMENT_ISSUER_COMPANY,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    EVENTO_RECEBIDO,
    FISCAL_PAYMENT_MODE,
    LOTE_PROCESSADO,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
    PROCESSADOR_OCA,
    SERVICO_PARALIZADO,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
)
from odoo.addons.l10n_br_fiscal.tools import remove_non_ascii_characters
from odoo.addons.spec_driven_model.models import spec_models

from ..constants.nfe import (
    NFCE_DANFE_LAYOUTS,
    NFE_DANFE_LAYOUTS,
    NFE_ENVIRONMENTS,
    NFE_TRANSMISSIONS,
    NFE_VERSIONS,
)

PRODUCT_CODE_FISCAL_DOCUMENT_TYPES = ["55", "01"]
NFE_XML_NAMESPACE = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

_logger = logging.getLogger(__name__)


def filter_processador_edoc_nfe(record):
    if record.processador_edoc == PROCESSADOR_OCA and record.document_type_id.code in [
        MODELO_FISCAL_NFE,
        MODELO_FISCAL_NFCE,
    ]:
        return True
    return False


class NFe(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "nfe.40.infnfe", "nfe.40.fat"]
    _stacked = "nfe.40.infnfe"
    _field_prefix = "nfe40_"
    _schema_name = "nfe"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_nfe"
    _spec_module = "odoo.addons.l10n_br_nfe_spec.models.v4_0.leiaute_nfe_v4_00"
    _spec_tab_name = "NFe"
    _nfe_search_keys = ["nfe40_Id"]

    # all m2o at this level will be stacked even if not required:
    _force_stack_paths = (
        "infnfe.total",
        "infnfe.infAdic",
        "infnfe.exporta",
        "infnfe.cobr",
        "infnfe.cobr.fat",
    )

    # When dynamic stacking is applied the NFe structure is:
    INFNFE_TREE = """
> <infnfe>
    > <ide>
        ≡ <NFref> l10n_br_fiscal.document.related
    - <emit> res.company
    - <avulsa>
    - <dest> res.partner
    - <retirada> res.partner
    - <entrega> res.partner
    ≡ <autXML> res.partner
    ≡ <det> l10n_br_fiscal.document.line
    > <total>
        > <ICMSTot>
        > <ISSQNtot>
        > <retTrib>
    > <transp>
        - <transporta> res.partner
        - <retTransp>
        - <veicTransp>
        ≡ <reboque>
        ≡ <vol>
    > <cobr>
        > <fat>
        ≡ <dup>
    > <pag>
        ≡ <detPag>
    - <infIntermed>
    > <infAdic>
        ≡ <obsCont>
        ≡ <obsFisco>
        ≡ <procRef>
    > <exporta>
    - <compra>
    - <cana>
    - <infRespTec> res.partner
    - <infSolicNFF>"""

    ##########################
    # NF-e spec related fields
    ##########################

    ##########################
    # NF-e tag: infNFe
    ##########################

    nfe40_versao = fields.Char(related="document_version")

    nfe_version = fields.Selection(
        selection=NFE_VERSIONS,
        string="NFe Version",
        copy=False,
        default=lambda self: self.env.company.nfe_version,
    )

    nfe40_Id = fields.Char(
        compute="_compute_id_tag",
        inverse="_inverse_nfe40_Id",
    )

    ##########################
    # NF-e tag: id
    # Compute Methods
    ##########################

    @api.depends("document_type_id", "document_key")
    def _compute_id_tag(self):
        """Set schema data which are not just related fields"""

        for record in self.filtered(filter_processador_edoc_nfe):
            # id
            if (
                record.document_type_id
                and record.document_type_id.prefix
                and record.document_key
            ):
                record.nfe40_Id = "{}{}".format(
                    record.document_type_id.prefix, record.document_key
                )
            else:
                record.nfe40_Id = None

    ##########################
    # NF-e tag: id
    # Inverse Methods
    ##########################

    def _inverse_nfe40_Id(self):
        for record in self:
            if record.nfe40_Id:
                record.document_key = re.findall(r"\d+", str(record.nfe40_Id))[0]

    ##########################
    # NF-e tag: ide
    ##########################

    # TODO criar uma função para tratar quando for entrada, hoje é campo calculado
    nfe40_cUF = fields.Char(
        related="company_id.partner_id.state_id.ibge_code",
        string="nfe40_cUF",
    )

    # <cNF>17983659</cNF> TODO

    nfe40_natOp = fields.Char(related="operation_name")

    nfe40_mod = fields.Char(related="document_type_id.code", string="nfe40_mod")

    nfe40_serie = fields.Char(related="document_serie")

    nfe40_nNF = fields.Char(related="document_number")

    nfe40_dhEmi = fields.Datetime(related="document_date")

    nfe40_dhSaiEnt = fields.Datetime(
        compute="_compute_nfe40_dhSaiEnt",
        inverse="_inverse_nfe40_dhSaiEnt",
    )

    nfe40_tpNF = fields.Selection(
        compute="_compute_ide_data",
        inverse="_inverse_nfe40_tpNF",
    )

    nfe_dhCont = fields.Date(
        readonly=True,
        copy=False,
    )

    nfe_xJust = fields.Char(
        readonly=True,
    )

    nfe40_idDest = fields.Selection(compute="_compute_nfe40_idDest")

    nfe40_cMunFG = fields.Char(related="company_id.partner_id.city_id.ibge_code")

    nfe40_tpImp = fields.Selection(
        compute="_compute_ide_data",
        inverse="_inverse_nfe40_tpImp",
    )

    danfe_layout = fields.Selection(
        selection=NFE_DANFE_LAYOUTS + NFCE_DANFE_LAYOUTS,
    )

    nfe40_tpEmis = fields.Selection(
        related="nfe_transmission"
    )  # TODO no caso de entrada

    nfe_transmission = fields.Selection(
        selection=NFE_TRANSMISSIONS,
        string="NFe Transmission",
        copy=False,
        default=lambda self: self.env.company.nfe_transmission,
    )

    # <cDV>0</cDV> TODO

    nfe40_tpAmb = fields.Selection(related="nfe_environment")

    nfe_environment = fields.Selection(
        selection=NFE_ENVIRONMENTS,
        string="NFe Environment",
        copy=False,
        default=lambda self: self.env.company.nfe_environment,
    )

    nfe40_finNFe = fields.Selection(related="edoc_purpose")

    nfe40_indFinal = fields.Selection(related="ind_final")

    nfe40_indPres = fields.Selection(related="ind_pres")

    nfe40_procEmi = fields.Selection(default="0")

    nfe40_verProc = fields.Char(
        copy=False,
        default=lambda s: s.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_br_nfe.version.name", default="Odoo Brasil OCA v14"),
    )

    ##########################
    # NF-e tag: ide
    # Compute Methods
    ##########################

    @api.depends("fiscal_operation_type", "nfe_transmission")
    def _compute_ide_data(self):
        """Set schema data which are not just related fields"""
        for record in self:
            # tpNF
            if record.fiscal_operation_type:
                operation_2_tpNF = {
                    "out": "1",
                    "in": "0",
                }
                record.nfe40_tpNF = operation_2_tpNF[record.fiscal_operation_type]

            # tpImp
            if record.issuer == DOCUMENT_ISSUER_COMPANY:
                if record.document_type_id.code == MODELO_FISCAL_NFE:
                    record.nfe40_tpImp = record.company_id.nfe_danfe_layout

                if record.document_type_id.code == MODELO_FISCAL_NFCE:
                    record.nfe40_tpImp = record.company_id.nfce_danfe_layout

    @api.depends("partner_id", "company_id", "partner_shipping_id")
    def _compute_nfe40_idDest(self):
        for doc in self:
            company_partner = doc.company_id.partner_id
            partner = doc.partner_id
            partner_shipping = doc.partner_shipping_id
            if (
                partner_shipping
                and company_partner == partner
                and partner.state_id != partner_shipping.state_id
            ):
                doc.nfe40_idDest = "2"
            elif company_partner.state_id == partner.state_id:
                doc.nfe40_idDest = "1"
            elif company_partner.country_id == partner.country_id:
                doc.nfe40_idDest = "2"
            else:
                doc.nfe40_idDest = "3"

    @api.depends("date_in_out")
    def _compute_nfe40_dhSaiEnt(self):
        for doc in self:
            if doc.document_type == MODELO_FISCAL_NFCE:
                doc.nfe40_dhSaiEnt = None
            else:
                doc.nfe40_dhSaiEnt = doc.date_in_out

    ##########################
    # NF-e tag: ide
    # Inverse Methods
    ##########################

    def _inverse_nfe40_tpNF(self):
        for doc in self:
            if doc.nfe40_tpNF:
                tpNF_2_operation = {
                    "1": "out",
                    "0": "in",
                }
                doc.fiscal_operation_type = tpNF_2_operation[doc.nfe40_tpNF]

    def _inverse_nfe40_tpImp(self):
        for doc in self:
            if doc.nfe40_tpImp:
                doc.danfe_layout = doc.nfe40_tpImp

    def _inverse_nfe40_tpEmis(self):
        for doc in self:
            if doc.nfe40_tpEmis:
                doc.nfe_transmission = doc.nfe40_tpEmis

    def _inverse_nfe40_dhSaiEnt(self):
        for doc in self:
            if doc.document_type == MODELO_FISCAL_NFCE:
                doc.nfe40_dhSaiEnt = None
            else:
                doc.date_in_out = doc.nfe40_dhSaiEnt

    ##########################
    # NF-e tag: NFref
    ##########################

    nfe40_NFref = fields.One2many(
        comodel_name="l10n_br_fiscal.document.related",
        related="document_related_ids",
        inverse_name="document_id",
    )

    ##########################
    # NF-e tag: emit
    ##########################

    # emit and dest are not related fields as their related fields
    # can change depending if it's and incoming our outgoing NFe
    # specially when importing (ERP NFe migration vs supplier Nfe).
    nfe40_emit = fields.Many2one(
        comodel_name="res.company",
        compute="_compute_emit_data",
        string="Emit",
    )

    nfe40_CRT = fields.Selection(
        related="company_tax_framework",
        string="Código de Regime Tributário (NFe)",
    )

    ##########################
    # NF-e tag: emit
    # Compute Methods
    ##########################

    def _compute_emit_data(self):
        for doc in self:  # TODO if out
            doc.nfe40_emit = doc.company_id

    ##########################
    # NF-e tag: dest
    ##########################

    nfe40_dest = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_dest_data",
        readonly=True,
        string="Dest",
    )

    nfe40_indIEDest = fields.Selection(
        related="partner_ind_ie_dest",
        string="Contribuinte do ICMS (NFe)",
    )

    ##########################
    # NF-e tag: dest
    # Compute Methods
    ##########################

    @api.depends("partner_id")
    def _compute_dest_data(self):
        for doc in self:  # TODO if out
            if (
                doc.partner_id.is_anonymous_consumer
                and not doc.partner_id.cnpj_cpf
                and doc.document_type == MODELO_FISCAL_NFCE
            ):
                doc.nfe40_dest = None
            else:
                doc.nfe40_dest = doc.partner_id
            doc._set_nfe40_IEST()

    def _set_nfe40_IEST(self):
        self.ensure_one()
        iest = ""
        if self.partner_id:
            dest_state_id = self.partner_id.state_id
            if dest_state_id in self.company_id.state_tax_number_ids.mapped("state_id"):
                stn_id = self.company_id.state_tax_number_ids.filtered(
                    lambda stn: stn.state_id == dest_state_id
                )
                iest = stn_id.inscr_est
        self.company_inscr_est_st = iest

    ##########################
    # NF-e tag: entrega
    ##########################

    nfe40_entrega = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_entrega_data",
        string="Entrega",
    )

    ##########################
    # NF-e tag: entrega
    # Compute Methods
    ##########################

    @api.depends("partner_shipping_id")
    def _compute_entrega_data(self):
        for rec in self:
            if (
                rec.document_type == MODELO_FISCAL_NFCE
                and rec.partner_shipping_id.is_anonymous_consumer
            ):
                rec.nfe40_entrega = None
            elif rec.partner_id == rec.partner_shipping_id:
                # local de entrega: informar apenas se diferente do destinatário
                rec.nfe40_entrega = None
            else:
                rec.nfe40_entrega = rec.partner_shipping_id

    ##########################
    # NF-e tag: retirada
    ##########################

    nfe40_retirada = fields.Many2one(comodel_name="res.partner")

    ##########################
    # NF-e tag: det
    ##########################

    nfe40_det = fields.One2many(
        comodel_name="l10n_br_fiscal.document.line",
        inverse_name="document_id",
        related="fiscal_line_ids",
    )

    ##########################
    # NF-e tag: ICMSTot
    ##########################

    nfe40_vBC = fields.Monetary(string="BC do ICMS", related="amount_icms_base")

    nfe40_vICMS = fields.Monetary(related="amount_icms_value")

    # <vICMSDeson>0.00</vICMSDeson> TODO

    nfe40_vFCPUFDest = fields.Monetary(related="amount_icmsfcp_value")

    nfe40_vICMSUFDest = fields.Monetary(related="amount_icms_destination_value")

    nfe40_vICMSUFRemet = fields.Monetary(related="amount_icms_origin_value")

    # <vFCP>0.00</vFCP> TODO

    nfe40_vBCST = fields.Monetary(related="amount_icmsst_base")

    nfe40_vST = fields.Monetary(related="amount_icmsst_value")

    nfe40_vFCPST = fields.Monetary(related="amount_icmsfcpst_value")

    # <vFCPSTRet>0.00</vFCPSTRet> TODO

    nfe40_vProd = fields.Monetary(related="amount_price_gross")

    nfe40_vFrete = fields.Monetary(related="amount_freight_value")

    nfe40_vSeg = fields.Monetary(related="amount_insurance_value")

    # TODO  Verificar as operações de bonificação se o desconto sai correto
    # nfe40_vDesc = fields.Monetary(related="amount_financial_discount_value")
    # nfe40_vDesc = fields.Monetary(related="amount_discount_value")
    nfe40_vDesc = fields.Monetary(
        string="Montante de Desconto",
        related="amount_discount_value",
    )

    nfe40_vII = fields.Monetary(related="amount_ii_value")

    nfe40_vIPI = fields.Monetary(related="amount_ipi_value")

    # <vIPIDevol>0.00</vIPIDevol> TODO

    nfe40_vPIS = fields.Monetary(
        string="Valor do PIS (NFe)", related="amount_pis_value"
    )

    nfe40_vCOFINS = fields.Monetary(
        string="valor do COFINS (NFe)", related="amount_cofins_value"
    )

    nfe40_vOutro = fields.Monetary(
        string="Outros Custos",
        related="amount_other_value",
    )

    nfe40_vNF = fields.Monetary(related="amount_total")

    nfe40_vTotTrib = fields.Monetary(related="amount_estimate_tax")

    ##########################
    # NF-e tag: ISSQNtot
    ##########################

    # TODO

    ##########################
    # NF-e tag: retTrib
    ##########################

    nfe40_vRetPIS = fields.Monetary(related="amount_pis_wh_value")

    nfe40_vRetCOFINS = fields.Monetary(related="amount_cofins_wh_value")

    nfe40_vRetCSLL = fields.Monetary(related="amount_csll_wh_value")

    nfe40_vBCIRRF = fields.Monetary(related="amount_irpj_wh_base")

    nfe40_vIRRF = fields.Monetary(related="amount_irpj_wh_value")

    ##########################
    # NF-e tag: transp
    ##########################

    nfe40_modFrete = fields.Selection(default="9")

    ##########################
    # NF-e tag: transporta
    ##########################

    nfe40_transporta = fields.Many2one(comodel_name="res.partner")

    ##########################
    # NF-e tag: infAdic
    ##########################

    nfe40_infAdFisco = fields.Char(compute="_compute_nfe40_additional_data")

    ##########################
    # NF-e tag: infCpl
    ##########################

    nfe40_infCpl = fields.Char(
        compute="_compute_nfe40_additional_data",
    )

    nfe40_infNFeSupl = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.supplement",
    )

    @api.depends("fiscal_additional_data", "fiscal_additional_data")
    def _compute_nfe40_additional_data(self):
        for record in self:
            record.nfe40_infCpl = False
            record.nfe40_infAdFisco = False
            if record.fiscal_additional_data:
                record.nfe40_infAdFisco = remove_non_ascii_characters(
                    record.fiscal_additional_data
                )
            if record.customer_additional_data:
                record.nfe40_infCpl = remove_non_ascii_characters(
                    record.customer_additional_data
                )

    ##########################
    # NF-e tag: fat
    ##########################

    nfe40_nFat = fields.Char(related="document_number")

    nfe40_vOrig = fields.Monetary(related="amount_financial_total_gross")

    nfe40_vLiq = fields.Monetary(related="amount_financial_total")

    ##########################
    # NF-e tag: infRespTec
    ##########################

    nfe40_infRespTec = fields.Many2one(
        comodel_name="res.partner",
        related="company_id.technical_support_id",
    )

    ##########################
    # NF-e tag: autXML
    # Compute Methods
    ##########################

    def _default_nfe40_autxml(self):
        company = self.env.company
        authorized_partners = []
        if company.accountant_id and company.nfe_authorize_accountant_download_xml:
            authorized_partners.append(company.accountant_id.id)
        if (
            company.technical_support_id
            and company.nfe_authorize_technical_download_xml
        ):
            authorized_partners.append(company.technical_support_id.id)
        return authorized_partners

    ##########################
    # NF-e tag: autXML
    ##########################

    nfe40_autXML = fields.One2many(default=_default_nfe40_autxml)

    ################################
    # Framework Spec model's methods
    ################################

    def _export_field(self, xsd_field, class_obj, member_spec, export_value=None):
        if xsd_field == "nfe40_tpAmb":
            self.env.context = dict(self.env.context)
            self.env.context.update({"tpAmb": self[xsd_field]})
        return super()._export_field(xsd_field, class_obj, member_spec, export_value)

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        """
        Overriden to avoid creating inner tag for m2o if none of the
        denormalized inner attribute has been set.
        """
        self.ensure_one()
        if field_name in self._stacking_points.keys():
            if field_name == "nfe40_ISSQNtot" and not any(
                t == "issqn"
                for t in self.nfe40_det.mapped("product_id.tax_icms_or_issqn")
            ):
                return False

            elif (not xsd_required) and field_name not in ["nfe40_enderDest"]:
                comodel = self.env[self._stacking_points.get(field_name).comodel_name]
                fields = [
                    f
                    for f in comodel._fields
                    if f.startswith(self._field_prefix)
                    and f in self._fields.keys()
                    and f
                    # don't try to nfe40_fat id when reading nfe40_cobr for instance
                    not in self._stacking_points.keys()
                ]
                sub_tag_read = self.read(fields)[0]
                if not any(
                    v
                    for k, v in sub_tag_read.items()
                    if k.startswith(self._field_prefix)
                ):
                    return False

        return super()._export_many2one(field_name, xsd_required, class_obj)

    def _export_one2many(self, field_name, class_obj=None):
        res = super()._export_one2many(field_name, class_obj)
        i = 0
        for field_data in res:
            i += 1
            if class_obj._fields[field_name].comodel_name == "nfe.40.det":
                field_data.nItem = i
        return res

    @api.model
    def _prepare_import_dict(
        self, values, model=None, parent_dict=None, defaults_model=None
    ):
        return {
            **super()._prepare_import_dict(values, model, parent_dict, defaults_model),
            "imported_document": True,
        }

    def _build_attr(self, node, fields, vals, path, attr):
        key = f"nfe40_{attr[0]}"  # TODO schema wise
        value = getattr(node, attr[0])

        if key == "nfe40_mod":
            vals["document_type_id"] = (
                self.env["l10n_br_fiscal.document.type"]
                .search([("code", "=", value)], limit=1)
                .id
            )

        return super()._build_attr(node, fields, vals, path, attr)

    def _build_many2one(self, comodel, vals, new_value, key, value, path):
        if key == "nfe40_entrega" and self.env.context.get("edoc_type") == "in":
            enderEntreg_value = self.env["res.partner"].build_attrs(value, path=path)
            new_value.update(enderEntreg_value)
            parent_domain = [("nfe40_CNPJ", "=", new_value.get("nfe40_CNPJ"))]
            parent_partner_match = self.env["res.partner"].search(
                parent_domain, limit=1
            )
            new_vals = {
                "nfe40_CNPJ": False,
                "type": "delivery",
                "parent_id": parent_partner_match.id,
                "company_type": "person",
            }
            new_value.update(new_vals)
            super()._build_many2one(
                self.env["res.partner"], vals, new_value, key, value, path
            )
        elif key == "nfe40_emit" and self.env.context.get("edoc_type") == "in":
            enderEmit_value = self.env["res.partner"].build_attrs(
                value.enderEmit, path=path
            )
            new_value.update(enderEmit_value)
            company_cnpj = self.env.company.cnpj_cpf.translate(
                str.maketrans("", "", string.punctuation)
            )
            emit_cnpj = new_value.get("nfe40_CNPJ").translate(
                str.maketrans("", "", string.punctuation)
            )
            if company_cnpj != emit_cnpj:
                vals["issuer"] = "partner"
            new_value["is_company"] = True
            new_value["cnpj_cpf"] = emit_cnpj
            super()._build_many2one(
                self.env["res.partner"], vals, new_value, "partner_id", value, path
            )
        elif key == "nfe40_dest" and self.env.context.get("edoc_type") == "out":
            enderDest_value = self.env["res.partner"].build_attrs(
                value.enderDest, path=path
            )
            new_value.update(enderDest_value)
            company_cnpj = self.env.company.cnpj_cpf.translate(
                str.maketrans("", "", string.punctuation)
            )
            dest_cnpj = new_value.get("nfe40_CNPJ").translate(
                str.maketrans("", "", string.punctuation)
            )
            if company_cnpj != dest_cnpj:
                vals["issuer"] = "partner"
            new_value["is_company"] = True
            new_value["cnpj_cpf"] = dest_cnpj
            super()._build_many2one(
                self.env["res.partner"], vals, new_value, "partner_id", value, path
            )
        elif (
            self.env.context.get("edoc_type") == "in"
            and key
            in [
                "nfe40_dest",
                "nfe40_enderDest",
            ]
        ) or (
            self.env.context.get("edoc_type") == "out"
            and key
            in [
                "nfe40_emit",
                "nfe40_enderEmit",
            ]
        ):
            # this would be the emit/company data, but we won't update it on
            # NFe import so just do nothing
            return
        elif (
            self._name == "account.invoice"
            and comodel._name == "l10n_br_fiscal.document"
        ):
            # module l10n_br_account_nfe
            # stacked m2o
            vals.update(new_value)
        else:
            super()._build_many2one(comodel, vals, new_value, key, value, path)

    ################################
    # Business Model Methods
    ################################

    @api.constrains("document_type", "state_edoc", "fiscal_line_ids")
    def _check_product_default_code(self):
        for rec in self:
            if (
                rec.document_type in PRODUCT_CODE_FISCAL_DOCUMENT_TYPES
                and rec.state_edoc == "a_enviar"
            ):
                for line in rec.fiscal_line_ids:
                    if not line.product_id.default_code and not line.nfe40_cProd:
                        raise ValidationError(
                            _(
                                f"The product {line.product_id.display_name} "
                                f"must have a default code or the product code"
                                f"line field (nfe40_cProd) should be filled."
                            )
                        )

    @api.constrains("document_date", "document_key", "state_edoc")
    def _check_document_date_key(self):
        for rec in self:
            if rec.document_key:
                key_date_str = rec.document_key[2:6]
                key_date = datetime.strptime(key_date_str, "%y%m")

                document_date = fields.Datetime.from_string(rec.document_date)
                if (
                    rec.document_type in ["55", "65"]
                    and rec.state_edoc in ["a_enviar", "autorizada"]
                    and (
                        key_date.year != document_date.year
                        or key_date.month != document_date.month
                    )
                ):
                    raise ValidationError(
                        _(
                            "The document date does not match the date in the document "
                            "key."
                        )
                    )

    def _document_number(self):
        # TODO: Criar campos no fiscal para codigo aleatorio e digito verificador,
        # pois outros modelos também precisam dessescampos: CT-e, MDF-e etc
        result = super()._document_number()
        for record in self.filtered(filter_processador_edoc_nfe):
            if record.document_key:
                try:
                    chave = ChaveEdoc(record.document_key)
                    record.nfe40_cNF = chave.codigo_aleatorio
                    record.nfe40_cDV = chave.digito_verificador
                except Exception as e:
                    raise ValidationError(
                        _(
                            "%(name)s:\n %(error)s",
                            name=record.document_type_id.name,
                            error=e,
                        )
                    ) from e
        return result

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.with_context(lang="pt_BR").filtered(
            filter_processador_edoc_nfe
        ):
            record.flush()
            record.invalidate_cache()
            inf_nfe = record.export_ds()[0]

            inf_nfe_supl = None
            if record.nfe40_infNFeSupl:
                inf_nfe_supl = record.nfe40_infNFeSupl.export_ds()[0]

            nfe = Nfe(infNFe=inf_nfe, infNFeSupl=inf_nfe_supl, signature=None)
            edocs.append(nfe)
        return edocs

    def _processador(self):
        self._check_nfe_environment()
        certificado = self.company_id._get_br_ecertificate()
        session = Session()
        session.verify = False

        params = {
            "transmissao": TransmissaoSOAP(certificado, session),
            "uf": self.company_id.state_id.ibge_code,
            "versao": self.nfe_version,
            "ambiente": self.nfe_environment,
        }

        if self.document_type == MODELO_FISCAL_NFE:
            params.update(
                envio_sincrono=self.company_id.nfe_enable_sync_transmission,
                contingencia=self.company_id.nfe_enable_contingency_ws,
            )
            return edoc_nfe(**params)

        if self.document_type == MODELO_FISCAL_NFCE:
            params.update(
                csc_token=self.company_id.nfce_csc_token,
                csc_code=self.company_id.nfce_csc_code,
            )
            return edoc_nfce(**params)

    def _check_nfe_environment(self):
        self.ensure_one()
        company_nfe_environment = self.company_id.nfe_environment
        if self.nfe_environment != company_nfe_environment:
            raise UserError(
                _(
                    f"Nf-e environment: {self.nfe_environment}"
                    " cannot be different from what is configured "
                    f"in the company: {company_nfe_environment}"
                )
            )

    def _document_export(self, pretty_print=True):
        result = super()._document_export()
        for record in self.filtered(filter_processador_edoc_nfe):
            edoc = record.serialize()[0]
            processador = record._processador()
            xml_file = processador.render_edoc_xsdata(edoc, pretty_print=pretty_print)[
                0
            ]
            # Delete previous authorization events in draft
            if (
                record.authorization_event_id
                and record.authorization_event_id.state == "draft"
            ):
                record.sudo().authorization_event_id.unlink()

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
            xml_assinado = processador.assina_raiz(edoc, edoc.infNFe.Id)
            self._valida_xml(xml_assinado)
        return result

    def _nfe_update_status_and_save_data(self, process):
        """
        Updates the NFe status based on the webservice response,
        handling different scenarios.
        """
        self.ensure_one()
        force_change_status = False
        response = process.resposta
        webservice = process.webservice
        if hasattr(process, "protocolo"):
            inf_prot = process.protocolo.infProt
        else:
            # The ´nfeRetAutorizacaoLote´ webservice allows
            # querying a batch of NFe, therefore in this case the return of protNFe
            # is a list, but the localization only sends one NFe per batch.
            if webservice == "nfeRetAutorizacaoLote":
                inf_prot = response.protNFe[0].infProt
            else:
                inf_prot = response.protNFe.infProt
        nfe_proc_xml = getattr(process, "processo_xml", None)
        if nfe_proc_xml:
            nfe_proc_xml = nfe_proc_xml.decode()
        self._nfe_save_protocol(inf_prot, nfe_proc_xml)
        # For ´nfeConsultaNF´ webservice, the status is checked in the main response.
        # This is crucial because for canceled NFes, the current status does not
        # reflect the authorization protocol status.
        if webservice == "nfeConsultaNF":
            c_stat = response.cStat
            x_motivo = response.xMotivo
            force_change_status = True
        else:
            c_stat = inf_prot.cStat
            x_motivo = inf_prot.xMotivo
        # update document
        self.update(
            {
                "status_code": c_stat,
                "status_name": x_motivo,
            }
        )
        # change state
        state_map = {
            **dict.fromkeys(AUTORIZADO, SITUACAO_EDOC_AUTORIZADA),
            **dict.fromkeys(DENEGADO, SITUACAO_EDOC_DENEGADA),
            **dict.fromkeys(CANCELADO, SITUACAO_EDOC_CANCELADA),
        }
        state = state_map.get(c_stat, SITUACAO_EDOC_REJEITADA)
        self._change_state(state, force_change_status)

    def _nfe_save_protocol(self, inf_prot, nfe_proc_xml=None):
        if not self.authorization_event_id:
            # TODO: create new event.
            pass
        if type(inf_prot.dhRecbto) is datetime:
            protocol_date = fields.Datetime.to_string(inf_prot.dhRecbto)
        # When the bidding comes from xsdata, the date comes as XmlDateTime
        elif type(inf_prot.dhRecbto) is XmlDateTime:
            dt = inf_prot.dhRecbto.to_datetime()
            protocol_date = fields.Datetime.to_string(dt)
        else:
            protocol_date = fields.Datetime.to_string(
                datetime.fromisoformat(inf_prot.dhRecbto)
            )
        self.authorization_event_id.set_done(
            status_code=inf_prot.cStat,
            response=inf_prot.xMotivo,
            protocol_date=protocol_date,
            protocol_number=inf_prot.nProt,
            file_response_xml=nfe_proc_xml,
        )

    def _valida_xml(self, xml_file):
        self.ensure_one()
        erros = Nfe.schema_validation(xml_file)
        erros = "\n".join(erros)
        self.write({"xml_error_message": erros or False})

    def _exec_after_SITUACAO_EDOC_AUTORIZADA(self, old_state, new_state):
        self.ensure_one()
        if (
            self.document_type_id.code in [MODELO_FISCAL_NFE]
            and self.issuer == DOCUMENT_ISSUER_COMPANY
        ):
            try:
                self.make_pdf()
            except Exception as e:
                # Não devemos interromper o fluxo
                # E dar rollback em um documento
                # autorizado, podendo perder dados.
                # Se der problema que apareça quando
                # o usuário clicar no gerar PDF novamente.
                _logger.error(f"DANFE Error \n {e}")
        return super()._exec_after_SITUACAO_EDOC_AUTORIZADA(old_state, new_state)

    def _generate_key(self):
        for record in self.filtered(filter_processador_edoc_nfe):
            date = fields.Datetime.context_timestamp(record, record.document_date)

            required_fields_gen_edoc = []
            if not record.company_cnpj_cpf:
                required_fields_gen_edoc.append("CNPJ/CPF")
            elif not record.company_state_id:
                required_fields_gen_edoc.append("State Company")
            elif not record.document_type_id:
                required_fields_gen_edoc.append("Document Type")
            elif not record.document_number:
                required_fields_gen_edoc.append("Document Number")
            elif not record.document_serie:
                required_fields_gen_edoc.append("Document Serie")

            for field in required_fields_gen_edoc:
                raise ValidationError(
                    _("To Generate EDoc Key, you need to fill the %s field.") % field
                )

            chave_edoc = ChaveEdoc(
                ano_mes=date.strftime("%y%m").zfill(4),
                cnpj_cpf_emitente=record.company_cnpj_cpf,
                codigo_uf=(
                    record.company_state_id and record.company_state_id.ibge_code or ""
                ),
                forma_emissao=int(self.nfe_transmission),
                modelo_documento=record.document_type_id.code or "",
                numero_documento=record.document_number or "",
                numero_serie=record.document_serie or "",
                validar=False,
            )
            record.document_key = chave_edoc.chave

    def _nfe_consult_receipt(self):
        self.ensure_one()
        processor = self._processador()
        # Consult receipt and process the response
        rec_num = self.authorization_event_id.lot_receipt_number
        receipt_process = processor.consulta_recibo(numero=rec_num)
        if receipt_process.resposta.cStat == "104":  # Lote Processado
            self._nfe_response_add_proc(receipt_process)
        self._nfe_process_authorization(receipt_process)

    def _nfe_response_add_proc(self, ws_response_process):
        """
        Inject the final NF-e, tag `nfeProc`, into the response.
        """
        xml_soap = ws_response_process.retorno.content
        tree_soap = etree.fromstring(xml_soap)
        prot_nfe_element = tree_soap.xpath(
            "//nfe:protNFe", namespaces=NFE_XML_NAMESPACE
        )[0]
        proc_nfe_xml = self._nfe_create_proc(prot_nfe_element)
        if proc_nfe_xml:
            # it is not always possible to create nfeProc.
            parser = XmlParser()
            nfe_proc = parser.from_string(proc_nfe_xml.decode(), TnfeProc)
            ws_response_process.processo = nfe_proc
            ws_response_process.processo_xml = proc_nfe_xml

    def _nfe_create_proc(self, prot_nfe_element):
        """
        Create the `nfeProc` XML by combining the NF-e and the authorization protocol.

        This method decodes the saved `enviNFe` message, extracts the <NFe> tag,
        and combines it with the provided authorization protocol element to create
        the `nfeProc` XML, which represents the finalized NF-e document.

        Args:
            prot_nfe_element: The XML element containing the authorization protocol.

        Returns:
            The assembled `nfeProc` XML, or None if the `send_file_id` data is not
            found.

        Note:
            Useful for recreating the final NF-e XML, as SEFAZ does not provide the
            complete XML upon consultation, only the authorization protocol.
        """
        self.ensure_one()

        if not self.send_file_id.datas:
            _logger.info(
                "NF-e data not found when trying to assemble the "
                "xml with the authorization protocol (nfeProc)"
            )
            return None

        processor = self._processador()

        # Extract the <NFe> tag from the `enviNFe` message, which represents the NF-e
        nfe_send_xml = base64.b64decode(self.send_file_id.datas)
        tree_envi_nfe = etree.fromstring(nfe_send_xml)
        element_nfe = tree_envi_nfe.xpath("//nfe:NFe", namespaces=NFE_XML_NAMESPACE)[0]

        # Assemble the `nfeProc` using the erpbrasil.edoc library.
        proc_nfe_xml = processor.monta_nfe_proc(
            nfe=element_nfe, prot_nfe=prot_nfe_element
        )

        return proc_nfe_xml

    def _document_status(self):
        self.ensure_one()
        status = super()._document_status()
        if filter_processador_edoc_nfe(self):
            status = self.check_nfe_status_in_sefaz()
        return status

    def check_nfe_status_in_sefaz(self):
        """
        Checks the status and protocol of an NF-e against SEFAZ's database.
        It updates the NF-e status and saves the data if the NF-e is found
        with specific status codes.
        Returns the response status message.
        """

        def _is_nfe_found(c_stat):
            """
            Determines if the NF-e is registered in SEFAZ by analyzing the status code:
            - 100: NF-e authorized - found and valid.
            - 101: NF-e cancellation approved - found but cancelled.
            - 110: NF-e use denied - present but restricted.
            Returns True for these codes, indicating the NF-e's registration in SEFAZ.
            """
            return c_stat in ["100", "101", "110"]

        nfe_manager = self._processador()
        check_response = nfe_manager.consulta_documento(chave=self.document_key)
        status = check_response.resposta.xMotivo

        if _is_nfe_found(check_response.resposta.cStat):
            if not self.authorization_file_id:
                # There's no need to assemble and persist the NFe file (nfeproc)
                #  if it is already saved.
                self._nfe_response_add_proc(check_response)
            # Updates the information if it is inconsistent in the system.
            self._nfe_update_status_and_save_data(check_response)
        return status

    def _prepare_nfce_send(self):
        self.ensure_one()
        self._prepare_payments_for_nfce()
        self.nfe40_infNFeSupl = self.env["l10n_br_fiscal.document.supplement"].create(
            {
                "nfe40_qrCode": self.get_nfce_qrcode(),
                "nfe40_urlChave": self.get_nfce_qrcode_url(),
            }
        )

    def _eletronic_document_send(self):
        super()._eletronic_document_send()
        for record in self.filtered(filter_processador_edoc_nfe):
            if record.xml_error_message:
                return  # Skip
            if record.state_edoc not in ["enviada", "a_enviar"]:
                return  # Skip
            if record.document_type == MODELO_FISCAL_NFCE:
                record._prepare_nfce_send()
            if record.state_edoc == "enviada":
                record._nfe_consult_receipt()
            if record.state_edoc == "a_enviar":
                record._nfe_send_for_authorization()

    def _nfe_send_for_authorization(self):
        """
        Serialize and send a NFe for authorizaion
        """
        serialized_nfe = self.serialize()[0]
        nfe_manager = self._processador()
        authorization_response = None
        for service_response in nfe_manager.processar_documento(serialized_nfe):
            if service_response.webservice not in [
                "nfeAutorizacaoLote",
                "nfeRetAutorizacaoLote",
            ]:
                continue
            if service_response.webservice == "nfeAutorizacaoLote":
                if (
                    service_response.resposta.cStat in SERVICO_PARALIZADO
                    and self.document_type == MODELO_FISCAL_NFCE
                ):
                    # Offline contingency is only allowed for NFC-e (65)
                    self._update_nfce_for_offline_contingency()
                    return
                if service_response.resposta.infRec:
                    # Only ASYNC: The receipt is only applicable for asynchronous
                    # transmission.
                    self._nfe_process_send_asynchronous(service_response)
                    # Commit to secure receipt info for future queries.
                    in_testing = getattr(threading.current_thread(), "testing", False)
                    if not in_testing:
                        self.env.cr.commit()  # pylint: disable=invalid-commit

                    # Check if 'nfe_separate_async_process' is set in the company
                    # settings. If True, skip the receipt consultation in this
                    # transaction. The user will need to manually trigger the
                    # consultation later to obtain the usage protocol.
                    skip_consult_receipt = self.env.company.nfe_separate_async_process
                    if skip_consult_receipt:
                        break
                    else:
                        continue
            authorization_response = service_response
        if authorization_response:
            self._nfe_process_authorization(authorization_response)

    def _nfe_process_send_asynchronous(self, send_process):
        self.authorization_event_id._save_event_file(
            send_process.envio_xml.decode("utf-8"), "xml"
        )
        self.authorization_event_id.lot_receipt_number = (
            send_process.resposta.infRec.nRec
        )
        self.state_edoc = "enviada"

    def _nfe_process_authorization(self, authorization_process):
        """
        Processes the response to the authorization request (batch processing).
        This can be called the transmission result or the processing result
        of the NF-e batch submission message.

        The responses can be in two formats:
        - 'retEnviNFe' for synchronous.
        - 'retConsReciNFe' for asynchronous.
        """
        self.ensure_one()
        if authorization_process.resposta.cStat in LOTE_PROCESSADO:
            # Processes the individual result of each NF-e (protNFe).
            self._nfe_update_status_and_save_data(authorization_process)
        else:
            # Batch processing failure.
            self._change_state(SITUACAO_EDOC_REJEITADA)
            self.write(
                {
                    "status_code": authorization_process.resposta.cStat,
                    "status_name": authorization_process.resposta.xMotivo,
                }
            )

    def view_pdf(self):
        if not self.filtered(filter_processador_edoc_nfe):
            return super().view_pdf()

        if self.document_type == MODELO_FISCAL_NFCE:
            return self.action_danfe_nfce_report()

        if not self.authorization_file_id or not self.file_report_id:
            self.make_pdf()
        return self._target_new_tab(self.file_report_id)

    def make_pdf(self):
        if not self.filtered(filter_processador_edoc_nfe):
            return super().make_pdf()

        attachment_data = {
            "name": self.document_key + ".pdf",
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": "application/pdf",
            "type": "binary",
        }
        report = self.env.ref("l10n_br_nfe.report_danfe")
        pdf_data = report._render_qweb_pdf(self.fiscal_line_ids.document_id.ids)
        attachment_data["datas"] = base64.b64encode(pdf_data[0])
        file_pdf = self.file_report_id
        self.file_report_id = False
        file_pdf.unlink()

        self.file_report_id = self.env["ir.attachment"].create(attachment_data)

    def import_binding_nfe(self, binding, edoc_type="out"):
        document = (
            self.env["nfe.40.infnfe"]
            .with_context(tracking_disable=True, edoc_type=edoc_type, dry_run=False)
            .build_from_binding(binding.NFe.infNFe)
        )

        if edoc_type == "in" and document.company_id.cnpj_cpf != cnpj_cpf.formata(
            binding.NFe.infNFe.emit.CNPJ
        ):
            document.fiscal_operation_type = "in"
            document.issuer = "partner"

        return document

    def _document_cancel(self, justificative):
        if self.document_type_id.code in [MODELO_FISCAL_NFE]:
            if not justificative or len(justificative) < 15:
                raise ValidationError(
                    _(
                        "Please enter a justification that is at least 15 characters "
                        "long."
                    )
                )
        result = super()._document_cancel(justificative)
        online_event = self.filtered(filter_processador_edoc_nfe)
        if online_event:
            online_event._nfe_cancel()
        return result

    def _need_compute_nfe_tags(self):
        if (
            self.state_edoc in [SITUACAO_EDOC_EM_DIGITACAO, SITUACAO_EDOC_A_ENVIAR]
            and self.processador_edoc == PROCESSADOR_OCA
            and self.document_type_id.code in [MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE]
            and self.issuer == DOCUMENT_ISSUER_COMPANY
        ):
            return True
        else:
            return False

    def _nfe_cancel(self):
        self.ensure_one()
        processador = self._processador()

        if not self.authorization_protocol:
            raise UserError(_("Authorization Protocol Not Found!"))

        evento = processador.cancela_documento(
            chave=self.document_key,
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
            if retevento.infEvento.cStat not in CANCELADO:
                mensagem = "Erro no cancelamento"
                mensagem += "\nCódigo: " + retevento.infEvento.cStat
                mensagem += "\nMotivo: " + retevento.infEvento.xMotivo
                raise UserError(mensagem)

            if retevento.infEvento.chNFe == self.document_key:
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
        result = super()._document_correction(justificative)
        online_event = self.filtered(filter_processador_edoc_nfe)
        if online_event:
            online_event._nfe_correction(justificative)
        return result

    def _nfe_correction(self, justificative):
        self.ensure_one()
        processador = self._processador()

        numeros = self.event_ids.filtered(
            lambda e: e.type == "14" and e.state == "done"
        ).mapped("sequence")

        sequence = str(int(max(numeros)) + 1) if numeros else "1"

        evento = processador.carta_correcao(
            chave=self.document_key,
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
            if not retevento.infEvento.chNFe == self.document_key:
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

    def _update_nfce_for_offline_contingency(self):
        self.write(
            {
                "nfe_transmission": "9",  # 9: contingência off-line (tpEmis)
                "nfe40_dhCont": fields.Datetime.now().strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT
                ),
                "nfe40_xJust": "Sem comunicação com o servidor da Sefaz.",
            }
        )

    def get_nfce_qrcode(self):
        if self.document_type != MODELO_FISCAL_NFCE:
            return
        processador = self._processador()
        if self.nfe_transmission == "1":
            return processador.monta_qrcode(self.document_key)

        serialized_doc = self.serialize()[0]
        xml = processador.assina_raiz(serialized_doc, serialized_doc.infNFe.Id)
        return processador._generate_qrcode_contingency(serialized_doc, xml)

    def get_nfce_qrcode_url(self):
        if self.document_type != MODELO_FISCAL_NFCE:
            return

        return self._processador().consulta_qrcode_url

    def _prepare_payments_for_nfce(self):
        for rec in self.filtered(lambda d: d.document_type == MODELO_FISCAL_NFCE):
            rec.nfe40_detPag.filtered(lambda p: p.nfe40_tPag == "99").write(
                {"nfe40_xPag": "Outros"}
            )

    def action_danfe_nfce_report(self):
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", "l10n_br_nfe.report_danfe_nfce")],
                limit=1,
            )
            .report_action(self, data=self._prepare_nfce_danfe_values())
        )

    def _prepare_nfce_danfe_values(self):
        return {
            "company_ie": self.company_id.inscr_est,
            "company_cnpj": self.company_id.cnpj_cpf,
            "company_legal_name": self.company_id.legal_name,
            "company_street": self.company_id.street,
            "company_number": self.company_id.street_number,
            "company_district": self.company_id.district,
            "company_city": self.company_id.city_id.display_name,
            "company_state": self.company_id.state_id.name,
            "lines": self._prepare_nfce_danfe_line_values(),
            "total_product_quantity": len(
                self.fiscal_line_ids.filtered(lambda line: line.product_id)
            ),
            "amount_total": self.amount_total,
            "amount_discount_value": self.amount_discount_value,
            "amount_freight_value": self.amount_freight_value,
            "payments": self._prepare_nfce_danfe_payment_values(),
            "amount_change": self.nfe40_vTroco,
            "nfce_url": self.get_nfce_qrcode_url(),
            "document_key": self.document_key,
            "document_number": self.document_number,
            "document_serie": self.document_serie,
            "document_date": self.document_date.astimezone().strftime(
                "%d/%m/%y %H:%M:%S"
            ),
            "authorization_protocol": self.authorization_protocol,
            "document_qrcode": self.get_nfce_qrcode(),
            "system_env": self.nfe40_tpAmb,
            "unformatted_amount_freight_value": self.amount_freight_value,
            "unformatted_amount_discount_value": self.amount_discount_value,
            "contingency": self.nfe_transmission != "1",
            "homologation_environment": self.nfe_environment == "2",
        }

    def _prepare_nfce_danfe_line_values(self):
        lines_list = []
        lines = self.fiscal_line_ids.filtered(lambda line: line.product_id)
        for index, line in enumerate(lines):
            product_id = line.product_id
            lines_list.append(
                {
                    "product_index": index + 1,
                    "product_default_code": product_id.default_code,
                    "product_name": product_id.name,
                    "product_quantity": line.quantity,
                    "product_uom": product_id.uom_name,
                    "product_unit_value": product_id.lst_price,
                    "product_unit_total": line.quantity * product_id.lst_price,
                }
            )
        return lines_list

    def _prepare_nfce_danfe_payment_values(self):
        payments_list = []
        for payment in self.nfe40_detPag:
            payments_list.append(
                {
                    "method": dict(FISCAL_PAYMENT_MODE)[payment.nfe40_tPag],
                    "value": payment.nfe40_vPag,
                }
            )
        return payments_list
