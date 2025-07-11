# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import sys
from enum import Enum

from odoo import api, fields

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    CFOP_DESTINATION_EXTERNAL,
    EDOC_PURPOSE_COMPLEMENTAR,
    EDOC_PURPOSE_DEVOLUCAO,
    FINAL_CUSTOMER_NO,
)
from odoo.addons.l10n_br_fiscal.constants.icms import ICMS_CST, ICMS_SN_CST
from odoo.addons.l10n_br_fiscal.tools import remove_non_ascii_characters
from odoo.addons.spec_driven_model.models import spec_models

ICMSSN_CST_CODES_USE_102 = ("102", "103", "300", "400")
ICMSSN_CST_CODES_USE_202 = ("202", "203")
ICMS_ST_CST_CODES = ["60", "10"]

ICMS_SUB_TAGS = [
    "ICMS00",
    "ICMS10",
    "ICMS20",
    "ICMS30",
    "ICMS40",
    "ICMS51",
    "ICMS60",
    "ICMS70",
    "ICMS90",
    "ICMSPart",
    "ICMSST",
    "ICMSSN101",
    "ICMSSN102",
    "ICMSSN202",
    "ICMSSN500",
    "ICMSSN900",
]

ICMS_SELECTION = list(map(lambda tag: (f"nfe40_{tag}", tag), ICMS_SUB_TAGS))

PIS_SUB_TAGS = [
    "PISAliq",
    "PISQtde",
    "PISNT",
    "PISOutr",
]

PIS_SELECTION = list(map(lambda tag: (f"nfe40_{tag}", tag), PIS_SUB_TAGS))

COFINS_SUB_TAGS = [
    "COFINSAliq",
    "COFINSQtde",
    "COFINSNT",
    "COFINSOutr",
]

COFINS_SELECTION = list(map(lambda tag: (f"nfe40_{tag}", tag), COFINS_SUB_TAGS))


class NFeLine(spec_models.StackedModel):
    """Classe para mapear a linha do documento fiscal com a linha da NF-e

    Observações: Não deve ser definido nenhum related para o campo nfe40_vBC,
    O nome desse campo colide com campos de vários objetos como nfe.40.icms,
    nfe.40.ipi, nfe.40.pis, nfe.40.cofins. O campo nfe40_vBC deve ser populado
    através dos métodos _export_fields_*
    """

    _name = "l10n_br_fiscal.document.line"
    _inherit = ["l10n_br_fiscal.document.line", "nfe.40.det"]

    _nfe40_odoo_module = "odoo.addons.l10n_br_nfe_spec.models.v4_0.leiaute_nfe_v4_00"
    _nfe40_stacking_mixin = "nfe.40.det"
    # all m2o below this level will be stacked even if not required:
    _nfe40_stacking_force_paths = ("det.imposto.",)
    _nfe40_stacking_skip_paths = ("nfe40_det_infNFe_id",)

    # When dynamic stacking is applied, the NFe line has the following structure:
    DET_TREE = """
> <det>
    > <prod>
        ≡ <gCred>
        ≡ <DI>
        ≡ <detExport>
        ≡ <rastro>
        - <infProdNFF>
        - <infProdEmb>
        - <veicProd>
        - <med>
        ≡ <arma>
        - <comb>
    > <imposto>
        > <ICMS>
            > <ICMSPart>
            > <ICMSST>
        > <IPI>
            > <IPITrib>
            > <IPINT>
        > <II>
        > <ISSQN>
        > <PIS>
            > <PISAliq>
            > <PISQtde>
            > <PISNT>
            > <PISOutr>
        > <PISST>
        > <COFINS>
            > <COFINSAliq>
            > <COFINSQtde>
            > <COFINSNT>
            > <COFINSOutr>
        > <COFINSST>
        > <ICMSUFDest>
    - <impostoDevol>
    - <obsItem>
    - <DFeReferenciado>"""

    ##########################
    # NF-e spec related fields
    ##########################

    ######################################
    # NF-e tag: det
    # Grupo I. Produtos e Serviços da NF-e
    ######################################

    nfe40_det_infNFe_id = fields.Many2one(related="document_id")

    ######################################
    # NF-e tag: prod
    # Grupo I. Produtos e Serviços da NF-e
    ######################################

    # nfe40_cProd = fields.Char(related="product_id.default_code")

    nfe40_cEAN = fields.Char(related="product_id.barcode")

    # nfe40_xProd = fields.Char(related="name") TODO

    nfe40_NCM = fields.Char(related="ncm_id.code_unmasked")

    # NVE TODO

    nfe40_CEST = fields.Char(related="cest_id.code_unmasked")

    # indEscala TODO

    # CNPJFab TODO

    nfe40_cBenef = fields.Char(related="icms_tax_benefit_code")

    # TODO em uma importação de XML deve considerar esse campo na busca do
    # ncm_id
    nfe40_EXTIPI = fields.Char(related="ncm_id.exception")

    nfe40_CFOP = fields.Char(related="cfop_id.code")

    nfe40_uCom = fields.Char(related="uom_id.code")

    nfe40_qCom = fields.Float(string="nfe40 qCom", related="quantity")

    nfe40_vUnCom = fields.Float(
        related="price_unit",
        string="Valor unitário de comercialização",
    )

    nfe40_vProd = fields.Monetary(related="price_gross")

    nfe40_cEANTrib = fields.Char(related="product_id.barcode")

    nfe40_uTrib = fields.Char(related="uot_id.code")

    nfe40_qTrib = fields.Float(string="nfe40_qTrib", related="fiscal_quantity")

    nfe40_vUnTrib = fields.Float(
        related="fiscal_price",
        string="Valor unitário de tributação",
    )

    nfe40_vFrete = fields.Monetary(related="freight_value")

    nfe40_vSeg = fields.Monetary(related="insurance_value")

    nfe40_vDesc = fields.Monetary(related="discount_value")

    nfe40_vOutro = fields.Monetary(related="other_value")

    # nfe40_vBC = fields.Monetary(string="FIXME Não usar esse campo!")

    # NFE_IND_TOT = { TODO
    #     "0": "0=Valor do item (vProd) não compõe o valor total da NF-e",
    #     "1": "Valor do item (vProd) compõe o valor total da NF- e (vProd) (v2.0)",
    # }
    #
    nfe40_indTot = fields.Selection(default="1")

    ##########################
    # NF-e tag: id
    # Compute Methods
    ##########################

    # TODO

    ##########################
    # NF-e tag: id
    # Inverse Methods
    ##########################

    # TODO

    ################################
    # Framework Spec model's methods
    ################################

    def _export_fields_nfe_40_prod(self, xsd_fields, class_obj, export_dict):
        nfe40_cProd = self.product_id.default_code or self.nfe40_cProd or ""
        export_dict["cProd"] = nfe40_cProd

        nfe40_xProd = (
            self.product_id.with_context(
                display_default_code=False,
                lang=self._context.get("force_product_lang")  # used for tests
                or self._context.get("lang"),
            ).display_name
            or self.name
            or ""
        )
        export_dict["xProd"] = nfe40_xProd[:120].replace("\n", " ").strip()

        nfe40_cEAN = self.product_id.barcode or "SEM GTIN"
        export_dict["cEAN"] = export_dict["cEANTrib"] = nfe40_cEAN

    ###########################################################
    # NF-e tag: DI
    # Grupo I01. Produtos e Serviços / Declaração de Importação
    ###########################################################

    # TODO

    ######################################################
    # NF-e tag: detExport
    # Grupo I03. Produtos e Serviços / Grupo de Exportação
    ######################################################

    # TODO

    ###################################################
    # NF-e tag: xPed e nItemPed
    # Grupo I05. Produtos e Serviços / Pedido de Compra
    ####################################################

    nfe40_xPed = fields.Char(related="partner_order")

    nfe40_nItemPed = fields.Char(related="partner_order_line")

    #################################################
    # NF-e tag: nFCI
    # Grupo I07. Produtos e Serviços / Grupo Diversos
    #################################################

    # TODO

    #######################################
    # NF-e tag: rastro
    # Grupo I80. Rastreabilidade de produto
    #######################################

    # TODO

    #######################################
    # NF-e tag: veicProd, med, arma, comb
    # Grupo J. Produto Específico
    #######################################

    # Overriden to define default value for normal product
    nfe40_choice_prod = fields.Selection(
        selection=[
            ("normal", "Produto Normal"),
            ("nfe40_veicProd", "Veículo"),
            ("nfe40_med", "Medicamento"),
            ("nfe40_arma", "Arma"),
            ("nfe40_comb", "Combustível"),
            ("nfe40_nRECOPI", "Número do RECOPI"),
        ],
        string="Tipo de Produto",
        default="normal",
    )

    #####################################################
    # NF-e tag: veicProd
    # Grupo JA. Detalhamento Específico de Veículos novos
    #####################################################

    # TODO

    ######################################################
    # NF-e tag: med
    # Grupo K. Detalhamento Específico de Medicamento e de
    # matérias-primas farmacêuticas
    ######################################################

    # TODO

    ################################################
    # NF-e tag: arma
    # Grupo L. Detalhamento Específico de Armamentos
    ################################################

    # TODO

    ###################################################
    # NF-e tag: comb
    # Grupo LA. Detalhamento Específico de Combustíveis
    ###################################################

    # TODO

    #################################################################
    # NF-e tag: nRECOPI
    # Grupo LB. Detalhamento Específico para Operação com Papel Imune
    #################################################################

    # TODO

    #################################################################
    # NF-e tag: imposto
    # Grupo M. Tributos incidentes no Produto ou Serviço
    #################################################################

    nfe40_vTotTrib = fields.Monetary(related="estimate_tax")

    def _export_fields_nfe_40_imposto(self, xsd_fields, class_obj, export_dict):
        if self.nfe40_choice_imposto == "nfe40_ICMS":
            xsd_fields.remove("nfe40_ISSQN")
        else:
            xsd_fields.remove("nfe40_ICMS")
            xsd_fields.remove("nfe40_II")

        if (
            not self.icms_value
            or self.partner_id.ind_ie_dest != "9"
            or self.partner_id.state_id == self.company_id.state_id
            or self.partner_id.country_id != self.company_id.country_id
        ):
            xsd_fields.remove("nfe40_ICMSUFDest")

        if not self.pisst_value:
            xsd_fields.remove("nfe40_PISST")

        if not self.cofinsst_value:
            xsd_fields.remove("nfe40_COFINSST")

        if not self.cfop_id.is_import and "nfe40_II" in xsd_fields:
            xsd_fields.remove("nfe40_II")

        if self.document_id.document_type == "65":
            xsd_fields.remove("nfe40_IPI")

    ##################################################
    # NF-e tag: ICMS
    # Grupo N01. ICMS Normal e ST
    # Grupo N02. Grupo Tributação do ICMS= 00
    # Grupo N03. Grupo Tributação do ICMS= 10
    # Grupo N04. Grupo Tributação do ICMS= 20
    # Grupo N05. Grupo Tributação do ICMS= 30
    # Grupo N06. Grupo Tributação do ICMS= 40, 41, 50
    # Grupo N07. Grupo Tributação do ICMS= 51
    # Grupo N08. Grupo Tributação do ICMS= 60
    # Grupo N09. Grupo Tributação do ICMS= 70
    # Grupo N10. Grupo Tributação do ICMS= 90
    #################################################

    nfe40_choice_icms = fields.Selection(
        selection=ICMS_SELECTION,
        string="Tipo de ICMS",
        compute="_compute_choice_icms",
        store=True,
    )

    nfe40_orig = fields.Selection(related="icms_origin")

    nfe40_modBC = fields.Selection(related="icms_base_type")

    nfe40_pICMS = fields.Float(related="icms_percent", string="pICMS")

    nfe40_vICMS = fields.Monetary(related="icms_value")

    # ICMS ST
    nfe40_vBCST = fields.Monetary(related="icmsst_base")

    nfe40_modBCST = fields.Selection(related="icmsst_base_type")

    nfe40_vICMSST = fields.Monetary(related="icmsst_value")

    # ICMS FCP ST
    nfe40_vFCPST = fields.Monetary(related="icmsfcpst_value")

    # COLOCAR NA ORDEM
    nfe40_pICMSST = fields.Float(related="icmsst_percent", string="pICMSST")
    nfe40_pMVAST = fields.Float(related="icmsst_mva_percent", string="pMVAST")
    nfe40_pRedBCST = fields.Float(related="icmsst_reduction", string="pRedBCST")

    # Todo: Calcular
    nfe40_vFCPSTRet = fields.Monetary(
        string="Valor do ICMS relativo ao Fundo de Combate à Pobreza Retido por ST",
    )
    nfe40_vCredICMSSN = fields.Monetary(
        string="ICMS SN Crédito", related="icmssn_credit_value"
    )

    ##########################
    # NF-e tag: ICMS
    # Compute Methods
    ##########################

    @api.depends("icms_cst_id")
    def _compute_choice_icms(self):
        for record in self:
            icms_choice = ""
            if record.icms_cst_id.code in ICMS_CST:
                if record.icms_cst_id.code in ["40", "41", "50"]:
                    icms_choice = "nfe40_ICMS40"
                else:
                    icms_choice = "{}{}".format("nfe40_ICMS", record.icms_cst_id.code)
            if record.icms_cst_id.code in ICMSSN_CST_CODES_USE_102:
                icms_choice = "nfe40_ICMSSN102"
            elif record.icms_cst_id.code in ICMSSN_CST_CODES_USE_202:
                icms_choice = "nfe40_ICMSSN202"
            elif record.icms_cst_id.code in ICMS_SN_CST:
                icms_choice = "{}{}".format("nfe40_ICMSSN", record.icms_cst_id.code)

            record.nfe40_choice_icms = icms_choice

    ##########################
    # NF-e tag: ICMS
    # Inverse Methods
    ##########################

    def _export_fields_icms(self):
        icms = {
            # ICMS
            "orig": self.nfe40_orig,
            "CST": self.icms_cst_id.code,
            "modBC": self.icms_base_type,
            "vBC": str("%.02f" % self.icms_base),
            "pRedBC": str("%.04f" % self.icms_reduction),
            "pICMS": str("%.04f" % self.icms_percent),
            "vICMS": str("%.02f" % self.icms_value),
            "vICMSSubstituto": str("%.02f" % self.icms_substitute),
            # ICMS SUBSTITUIÇÃO TRIBUTÁRIA
            "modBCST": self.icmsst_base_type,
            "pMVAST": str("%.04f" % self.icmsst_mva_percent),
            "pRedBCST": str("%.04f" % self.icmsst_reduction),
            "vBCST": str("%.02f" % self.icmsst_base),
            "pICMSST": str("%.04f" % self.icmsst_percent),
            "vICMSST": str("%.02f" % self.icmsst_value),
            "UFST": self.partner_id.state_id.code,
            # ICMS COBRADO ANTERIORMENTE POR SUBSTITUIÇÃO TRIBUTÁRIA
            "vBCSTRet": str("%.02f" % self.icmsst_wh_base),
            "pST": str("%.04f" % (self.icmsst_wh_percent + self.icmsfcp_wh_percent)),
            "vICMSSTRet": str("%.02f" % self.icmsst_wh_value),
            "pRedBCEfet": str("%.04f" % self.icms_effective_reduction),
            "vBCEfet": str("%.02f" % self.icms_effective_base),
            "pICMSEfet": str("%.04f" % self.icms_effective_percent),
            "vICMSEfet": str("%.02f" % self.icms_effective_value),
            # ICMS SIMPLES NACIONAL
            "CSOSN": self.icms_cst_id.code,
            "pCredSN": str("%.04f" % self.icmssn_percent),
            "vCredICMSSN": str("%.02f" % self.icmssn_credit_value),
        }
        if self.icmsfcp_wh_percent:
            icms.update(
                {
                    # FUNDO DE COMBATE À POBREZA RETIDO
                    "vBCFCPSTRet": str("%.02f" % self.icmsfcp_base_wh),
                    "pFCPSTRet": str("%.04f" % self.icmsfcp_wh_percent),
                    "vFCPSTRet": str("%.02f" % self.icmsfcp_value_wh),
                }
            )
        if (
            self.icmsfcp_percent
            and self.ind_final == FINAL_CUSTOMER_NO
            and self.cfop_destination != CFOP_DESTINATION_EXTERNAL
        ):
            icms.update(
                {
                    # FUNDO DE COMBATE À POBREZA
                    "vBCFCP": str("%.02f" % self.icmsfcp_base),
                    "pFCP": str("%.04f" % self.icmsfcp_percent),
                    "vFCP": str("%.02f" % self.icmsfcp_value),
                }
            )
        if self.icmsfcpst_percent:
            icms.update(
                {
                    # FUNDO DE COMBATE À POBREZA - COM ST
                    "vBCFCPST": str("%.02f" % self.icmsfcpst_base),
                    "pFCPST": str("%.04f" % self.icmsfcpst_percent),
                    "vFCPST": str("%.02f" % self.icmsfcpst_value),
                }
            )
        if self.icms_relief_id:
            icms.update(
                {
                    # DESONERAÇÃO DO IMCS
                    "vICMSDeson": str("%.02f" % self.icms_relief_value),
                    "motDesICMS": self.icms_relief_id.code,
                }
            )
        return icms

    def _export_fields_nfe_40_icms(self, xsd_fields, class_obj, export_dict):
        # TODO Not Implemented
        if "nfe40_ICMSPart" in xsd_fields:
            xsd_fields.remove("nfe40_ICMSPart")

        # TODO Not Implemented
        if "nfe40_ICMSST" in xsd_fields:
            xsd_fields.remove("nfe40_ICMSST")

        xsd_fields = [self.nfe40_choice_icms]
        icms_tag = (
            self.nfe40_choice_icms.replace("nfe40_", "")
            .replace("ICMS", "Icms")
            .replace("IcmsSN", "Icmssn")
        )
        binding_module = sys.modules[self._get_spec_property("binding_module")]
        # Tnfe.InfNfe.Det.Imposto.Icms.Icms00
        # see https://stackoverflow.com/questions/31174295/
        # getattr-and-setattr-on-nested-subobjects-chained-properties
        tnfe = binding_module.Tnfe
        infnfe = tnfe.InfNfe
        det = infnfe.Det
        imposto = det.Imposto
        icms = imposto.Icms
        icms_binding = getattr(icms, icms_tag)
        icms_dict = self._export_fields_icms()
        sliced_icms_dict = {
            key: icms_dict.get(key)
            for key in icms_binding.__dataclass_fields__.keys()
            if icms_dict.get(key)
        }
        export_dict[icms_tag.upper()] = icms_binding(**sliced_icms_dict)

    #######################################
    # NF-e tag: ICMSPart
    # Grupo N10a. Grupo de Partilha do ICMS
    #######################################

    # TODO

    #########################################
    # NF-e tag: ICMSST
    # Grupo N10b. Grupo de Repasse do ICMS ST
    #########################################

    # TODO

    #####################################
    # NF-e tag: ICMSUFDest
    # Grupo NA. ICMS para a UF de destino
    #####################################

    nfe40_vBCUFDest = fields.Monetary(related="icms_destination_base")

    nfe40_vBCFCPUFDest = fields.Monetary(related="icmsfcp_base")
    nfe40_vFCPUFDest = fields.Monetary(related="icmsfcp_value")
    nfe40_pFCPUFDest = fields.Float(related="icmsfcp_percent")

    nfe40_pICMSUFDest = fields.Monetary(compute="_compute_nfe40_ICMSUFDest")
    nfe40_pICMSInter = fields.Selection(compute="_compute_nfe40_ICMSUFDest")
    nfe40_pICMSInterPart = fields.Monetary(compute="_compute_nfe40_ICMSUFDest")

    def _compute_nfe40_ICMSUFDest(self):
        for record in self:
            if record.icms_origin_percent:
                record.nfe40_pICMSInter = str("%.02f" % record.icms_origin_percent)
            else:
                record.nfe40_pICMSInter = False

            record.nfe40_pICMSUFDest = record.icms_destination_percent
            record.nfe40_pICMSInterPart = record.icms_sharing_percent

    nfe40_vICMSUFDest = fields.Monetary(related="icms_destination_value")
    nfe40_vICMSUFRemet = fields.Monetary(related="icms_origin_value")

    ##################################################
    # NF-e tag: IPI
    # Grupo O. Imposto sobre Produtos Industrializados
    ##################################################

    nfe40_choice_tipi = fields.Selection(
        selection=[("nfe40_IPITrib", "IPITrib"), ("nfe40_IPINT", "IPINT")],
        string="IPITrib ou IPINT",
        compute="_compute_choice_tipi",
        store=True,
    )

    nfe40_choice_ipitrib = fields.Selection(
        selection=[
            ("nfe40_vBC", "vBC"),
            ("nfe40_pIPI", "pIPI"),
            ("nfe40_qUnid", "qUnid"),
            ("nfe40_vUnid", "vUnid"),
        ],
        string="Base vBC/pIPI/qUnid/vUnid",
        compute="_compute_nfe40_choice_ipitrib",
        store=True,
    )

    # CNPJProd TODO

    # cSelo TODO

    # qSelo TODO

    nfe40_cEnq = fields.Char(related="ipi_guideline_id.code")

    nfe40_pIPI = fields.Float(related="ipi_percent", string="pIPI")

    nfe40_vIPI = fields.Monetary(related="ipi_value")

    ##########################
    # NF-e tag: IPI
    # Compute Methods
    ##########################

    @api.depends("ipi_cst_id")
    def _compute_choice_tipi(self):
        for record in self:
            if record.ipi_cst_id.code in ["00", "49", "50", "99"]:
                record.nfe40_choice_tipi = "nfe40_IPITrib"
            else:
                record.nfe40_choice_tipi = "nfe40_IPINT"

    @api.depends("ipi_base_type")
    def _compute_nfe40_choice_ipitrib(self):
        for record in self:
            if record.ipi_base_type == "percent":
                record.nfe40_choice_ipitrib = "nfe40_pIPI"
            else:
                record.nfe40_choice_ipitrib = "nfe40_vUnid"

    ##########################
    # NF-e tag: IPI
    # Inverse Methods
    ##########################

    def _export_fields_nfe_40_tipi(self, xsd_fields, class_obj, export_dict):
        if self.ipi_cst_id.code not in ["00", "49", "50", "99"]:
            xsd_fields.remove("nfe40_IPITrib")
        else:
            xsd_fields.remove("nfe40_IPINT")

    def _export_fields_ipi(self, xsd_fields, class_obj, export_dict):
        export_dict["CST"] = self.ipi_cst_id.code
        export_dict["vBC"] = self.ipi_base

    def _export_fields_nfe_40_ipitrib(self, xsd_fields, class_obj, export_dict):
        self._export_fields_ipi(xsd_fields, class_obj, export_dict)

        if self.nfe40_choice_ipitrib == "nfe40_pIPI":
            xsd_fields.remove("nfe40_qUnid")
            xsd_fields.remove("nfe40_vUnid")
        else:
            xsd_fields.remove("nfe40_vBC")
            xsd_fields.remove("nfe40_pIPI")

    def _export_fields_nfe_40_ipint(self, xsd_fields, class_obj, export_dict):
        self._export_fields_ipi(xsd_fields, class_obj, export_dict)

    ################################
    # NF-e tag: II
    # Grupo P. Imposto de Importação
    ################################

    # vBC TODO

    nfe40_vDespAdu = fields.Monetary(related="ii_customhouse_charges")

    nfe40_vII = fields.Monetary(related="ii_value")

    nfe40_vIOF = fields.Monetary(related="ii_iof_value")

    ###############
    # NF-e tag: PIS
    # Grupo Q. PIS
    ###############

    nfe40_choice_pis = fields.Selection(
        selection=PIS_SELECTION,
        string="PISAliq/PISQtde/PISNT/PISOutr",
        compute="_compute_choice_pis",
        store=True,
    )

    nfe40_choice_pisoutr = fields.Selection(
        [
            ("nfe40_vBC", "vBC"),
            ("nfe40_pPIS", "pPIS"),
            ("nfe40_qBCProd", "qBCProd"),
            ("nfe40_vAliqProd", "vAliqProd"),
        ],
        compute="_compute_nfe40_choice_pisoutr",
        store=True,
        string="Tipo de Tributação do PIS",
    )

    nfe40_PISAliq = fields.Many2one(
        comodel_name="nfe.40.pisaliq",
        string="Código de Situação Tributária do PIS (Alíquota)",
        help="Código de Situação Tributária do PIS."
        "\n01 – Operação Tributável - Base de Cálculo = Valor da Operação"
        "\nAlíquota Normal (Cumulativo/Não Cumulativo);"
        "\n02 - Operação Tributável - Base de Calculo = Valor da Operação"
        "\n(Alíquota Diferenciada);",
    )

    nfe40_vPIS = fields.Monetary(
        string="Valor do PIS (NFe)",
        related="pis_value",
    )

    ##########################
    # NF-e tag: PIS
    # Compute Methods
    ##########################

    @api.depends("pis_cst_id")
    def _compute_choice_pis(self):
        for record in self:
            if record.pis_cst_id.code in ["01", "02"]:
                record.nfe40_choice_pis = "nfe40_PISAliq"
            elif record.pis_cst_id.code == "03":
                record.nfe40_choice_pis = "nfe40_PISQtde"
            elif record.pis_cst_id.code in ["04", "06", "07", "08", "09"]:
                record.nfe40_choice_pis = "nfe40_PISNT"
            else:
                record.nfe40_choice_pis = "nfe40_PISOutr"

    @api.depends("pis_base_type")
    def _compute_nfe40_choice_pisoutr(self):
        for record in self:
            if record.pis_base_type == "percent":
                record.nfe40_choice_pisoutr = "nfe40_pPIS"
            else:
                record.nfe40_choice_pisoutr = "nfe40_vAliqProd"

    ##########################
    # NF-e tag: PIS
    # Inverse Methods
    ##########################

    nfe40_pPIS = fields.Float(related="pis_percent", string="nfe40_pPIS")

    def _export_fields_nfe_40_pis(self, xsd_fields, class_obj, export_dict):
        remove_tags = {
            "nfe40_PISAliq": ["nfe40_PISQtde", "nfe40_PISNT", "nfe40_PISOutr"],
            "nfe40_PISQtde": ["nfe40_PISAliq", "nfe40_PISNT", "nfe40_PISOutr"],
            "nfe40_PISNT": ["nfe40_PISAliq", "nfe40_PISQtde", "nfe40_PISOutr"],
            "nfe40_PISOutr": ["nfe40_PISAliq", "nfe40_PISQtde", "nfe40_PISNT"],
        }

        for tag_to_remove in remove_tags.get(self.nfe40_choice_pis, []):
            if tag_to_remove in xsd_fields:
                xsd_fields.remove(tag_to_remove)

    def _export_fields_pis(self, xsd_fields, class_obj, export_dict):
        export_dict["CST"] = self.pis_cst_id.code
        export_dict["vBC"] = self.pis_base

    def _export_fields_nfe_40_pisaliq(self, xsd_fields, class_obj, export_dict):
        self._export_fields_pis(xsd_fields, class_obj, export_dict)

    def _export_fields_nfe_40_pisqtde(self, xsd_fields, class_obj, export_dict):
        self._export_fields_pis(xsd_fields, class_obj, export_dict)

    def _export_fields_nfe_40_pisoutr(self, xsd_fields, class_obj, export_dict):
        self._export_fields_pis(xsd_fields, class_obj, export_dict)

        if self.nfe40_choice_pisoutr == "nfe40_pPIS":
            xsd_fields.remove("nfe40_qBCProd")
            xsd_fields.remove("nfe40_vAliqProd")

        if self.nfe40_choice_pisoutr == "nfe40_vAliqProd":
            xsd_fields.remove("nfe40_vBC")
            xsd_fields.remove("nfe40_pPIS")

    def _export_fields_nfe_40_pisnt(self, xsd_fields, class_obj, export_dict):
        self._export_fields_pis(xsd_fields, class_obj, export_dict)

    #################
    # NF-e tag: PISST
    # Grupo R. PIS ST
    #################

    # TODO

    ##################
    # NF-e tag: COFINS
    # Grupo S. COFINS
    ##################

    nfe40_choice_cofins = fields.Selection(
        selection=COFINS_SELECTION,
        string="COFINSAliq/COFINSQtde/COFINSNT/COFINSOutr",
        compute="_compute_choice_cofins",
        store=True,
    )

    nfe40_choice_cofinsoutr = fields.Selection(
        selection=[
            ("nfe40_vBC", "vBC"),
            ("nfe40_pCOFINS", "pCOFINS"),
            ("nfe40_qBCProd", "qBCProd"),
            ("nfe40_vAliqProd", "vAliqProd"),
        ],
        compute="_compute_nfe40_choice_cofinsoutr",
        store=True,
        string="Tipo de Tributação do COFINS",
    )

    nfe40_pCOFINS = fields.Float(related="cofins_percent", string="nfe40_pCOFINS")

    nfe40_vCOFINS = fields.Monetary(
        string="Valor do COFINS (NFe)",
        related="cofins_value",
    )

    nfe40_COFINSAliq = fields.Many2one(
        comodel_name="nfe.40.cofinsaliq",
        string="Código de Situação Tributária do COFINS (Alíquota)",
        help="Código de Situação Tributária do COFINS."
        "\n01 – Operação Tributável - Base de Cálculo = Valor da Operação"
        "\nAlíquota Normal (Cumulativo/Não Cumulativo);"
        "\n02 - Operação Tributável - Base de Calculo = Valor da Operação"
        "\n(Alíquota Diferenciada);",
    )

    ##########################
    # NF-e tag: COFINS
    # Compute Methods
    ##########################

    @api.depends("cofins_cst_id")
    def _compute_choice_cofins(self):
        for record in self:
            if record.cofins_cst_id.code in ["01", "02"]:
                record.nfe40_choice_cofins = "nfe40_COFINSAliq"
            elif record.cofins_cst_id.code == "03":
                record.nfe40_choice_cofins = "nfe40_COFINSQtde"
            elif record.cofins_cst_id.code in ["04", "06", "07", "08", "09"]:
                record.nfe40_choice_cofins = "nfe40_COFINSNT"
            else:
                record.nfe40_choice_cofins = "nfe40_COFINSOutr"

    @api.depends("cofins_base_type")
    def _compute_nfe40_choice_cofinsoutr(self):
        for record in self:
            if record.cofins_base_type == "percent":
                record.nfe40_choice_cofinsoutr = "nfe40_pCOFINS"
            else:
                record.nfe40_choice_cofinsoutr = "nfe40_vAliqProd"

    ##########################
    # NF-e tag: COFINS
    # Inverse Methods
    ##########################

    # TODO

    def _export_fields_nfe_40_cofins(self, xsd_fields, class_obj, export_dict):
        remove_tags = {
            "nfe40_COFINSAliq": [
                "nfe40_COFINSQtde",
                "nfe40_COFINSNT",
                "nfe40_COFINSOutr",
            ],
            "nfe40_COFINSQtde": [
                "nfe40_COFINSAliq",
                "nfe40_COFINSNT",
                "nfe40_COFINSOutr",
            ],
            "nfe40_COFINSNT": [
                "nfe40_COFINSAliq",
                "nfe40_COFINSQtde",
                "nfe40_COFINSOutr",
            ],
            "nfe40_COFINSOutr": [
                "nfe40_COFINSAliq",
                "nfe40_COFINSQtde",
                "nfe40_COFINSNT",
            ],
        }

        for tag_to_remove in remove_tags.get(self.nfe40_choice_cofins, []):
            if tag_to_remove in xsd_fields:
                xsd_fields.remove(tag_to_remove)

    def _export_fields_cofins(self, xsd_fields, class_obj, export_dict):
        export_dict["CST"] = self.cofins_cst_id.code
        export_dict["vBC"] = self.cofins_base
        export_dict["vCOFINS"] = self.cofins_value

    def _export_fields_nfe_40_cofinsaliq(self, xsd_fields, class_obj, export_dict):
        self._export_fields_cofins(xsd_fields, class_obj, export_dict)

    def _export_fields_nfe_40_cofinsqtde(self, xsd_fields, class_obj, export_dict):
        self._export_fields_cofins(xsd_fields, class_obj, export_dict)

    def _export_fields_nfe_40_cofinsoutr(self, xsd_fields, class_obj, export_dict):
        self._export_fields_cofins(xsd_fields, class_obj, export_dict)

        if self.nfe40_choice_cofinsoutr == "nfe40_pCOFINS":
            xsd_fields.remove("nfe40_qBCProd")
            xsd_fields.remove("nfe40_vAliqProd")

        if self.nfe40_choice_cofinsoutr == "nfe40_vAliqProd":
            xsd_fields.remove("nfe40_vBC")
            xsd_fields.remove("nfe40_pCOFINS")

    def _export_fields_nfe_40_cofinsnt(self, xsd_fields, class_obj, export_dict):
        self._export_fields_cofins(xsd_fields, class_obj, export_dict)

    ####################
    # NF-e tag: COFINSST
    # Grupo T. COFINS ST
    ####################

    # TODO

    #################
    # NF-e tag: ISSQN
    # Grupo U. ISSQN
    #################

    nfe40_vISSQN = fields.Monetary(related="issqn_value")

    nfe40_cMunFG = fields.Char(related="issqn_fg_city_id.ibge_code")

    nfe40_cListServ = fields.Char(related="service_type_id.code")

    nfe40_vDeducao = fields.Monetary(related="issqn_deduction_amount")

    nfe40_vDescIncond = fields.Monetary(related="issqn_desc_incond_amount")

    nfe40_vDescCond = fields.Monetary(related="issqn_desc_cond_amount")

    nfe40_vISSRet = fields.Monetary(related="issqn_wh_value")

    nfe40_indISS = fields.Selection(related="issqn_eligibility")

    # nfe40_cServico TODO

    nfe40_cMun = fields.Char(related="issqn_fg_city_id.ibge_code")

    nfe40_cPais = fields.Char(
        related="issqn_fg_city_id.state_id.country_id.bc_code",
    )

    # nfe40_nProcesso TODO

    nfe40_indIncentivo = fields.Selection(related="issqn_incentive")

    #####################################################
    # NF-e tag: impostoDevol
    # Grupo UA. Tributos Devolvidos (para o item da NF-e)
    #####################################################

    nfe40_impostoDevol = fields.Many2one(
        comodel_name="nfe.40.impostodevol",
        string="impostoDevol",
        compute="_compute_nfe40_impostoDevol",
        store=True,
    )

    ##########################
    # NF-e tag: impostoDevol
    # Compute Methods
    ##########################

    @api.depends("p_devol", "ipi_devol_value")
    def _compute_nfe40_impostoDevol(self):
        for record in self:
            if record.nfe40_impostoDevol:
                if record.nfe40_impostoDevol.nfe40_IPI:
                    record.nfe40_impostoDevol.nfe40_IPI.unlink()
                record.nfe40_impostoDevol.unlink()
            if (
                record.document_id.edoc_purpose
                in (
                    EDOC_PURPOSE_DEVOLUCAO,
                    EDOC_PURPOSE_COMPLEMENTAR,
                )
                and record.p_devol
                and record.ipi_devol_value
            ):
                ipi_devol = self.env["nfe.40.ipi"].create(
                    {"nfe40_vIPIDevol": record.ipi_devol_value}
                )
                impostoDevol = record.nfe40_impostoDevol.create(
                    {
                        "nfe40_pDevol": record.p_devol,
                        "nfe40_IPI": ipi_devol.id,
                    }
                )
                record.nfe40_impostoDevol = impostoDevol

    ########################
    # NF-e tag: total
    # Grupo W. Total da NF-e
    ########################

    nfe40_choice_imposto = fields.Selection(
        selection=[
            ("nfe40_ICMS", "ICMS"),
            #            ("nfe40_II", "II"),
            #            ("nfe40_IPI", "IPI"),
            ("nfe40_ISSQN", "ISSQN"),
        ],
        string="ICMS/II/IPI ou ISSQN",
        compute="_compute_nfe40_choice_imposto",
        store=True,
    )

    ##########################
    # NF-e tag: total
    # Compute Methods
    ##########################

    @api.depends("tax_icms_or_issqn")
    def _compute_nfe40_choice_imposto(self):
        for record in self:
            if record.tax_icms_or_issqn == "issqn":
                record.nfe40_choice_imposto = "nfe40_ISSQN"
            else:
                record.nfe40_choice_imposto = "nfe40_ICMS"

    #######################################################
    # NF-e tag: infAdProd
    # Grupo V. Informações adicionais (para o item da NF-e)
    #######################################################

    nfe40_infAdProd = fields.Char(compute="_compute_nfe40_infAdProd")

    ##########################
    # NF-e tag: infAdProd
    # Compute Methods
    ##########################

    @api.depends("additional_data")
    def _compute_nfe40_infAdProd(self):
        for record in self:
            if record.additional_data:
                record.nfe40_infAdProd = remove_non_ascii_characters(
                    record.additional_data
                )
            else:
                record.nfe40_infAdProd = False

    @api.model
    def _prepare_import_dict(
        self, values, model=None, parent_dict=None, defaults_model=None
    ):
        values = super()._prepare_import_dict(
            values, model, parent_dict, defaults_model
        )
        if not values.get("name"):
            values["name"] = values.get("nfe40_xProd")
            if values.get("product_id"):
                values["ncm_id"] = (
                    self.env["product.product"].browse(values["product_id"]).ncm_id.id
                )
        return values

    def _build_attr(self, node, fields, vals, path, attr):
        key = "nfe40_%s" % (attr[0])
        value = getattr(node, attr[0])
        if key in ["nfe40_CST", "nfe40_modBC", "nfe40_CSOSN"]:
            return  # (dealt with in _build_many2one)

        if key.startswith("nfe40_ICMS") and key not in [
            "nfe40_ICMS",
            "nfe40_ICMSTot",
            "nfe40_ICMSUFDest",
        ]:
            vals["nfe40_choice_icms"] = key

        if key == "nfe40_vUnCom":
            vals["price_unit"] = float(value)
        if key == "nfe40_NCM":
            vals["ncm_id"] = (
                self.env["l10n_br_fiscal.ncm"]
                .search([("code_unmasked", "=", value)], limit=1)
                .id
            )
        if key == "nfe40_CEST" and value:
            vals["cest_id"] = (
                self.env["l10n_br_fiscal.cest"]
                .search([("code_unmasked", "=", value)], limit=1)
                .id
            )
        if key == "nfe40_qCom":
            vals["quantity"] = float(value)
        if key == "nfe40_qTrib":
            vals["fiscal_quantity"] = float(value)
        if key == "nfe40_cEnq":
            vals["ipi_guideline_id"] = (
                self.env["l10n_br_fiscal.tax.ipi.guideline"]
                .search([("code_unmasked", "=", value)], limit=1)
                .id
            )

        return super()._build_attr(node, fields, vals, path, attr)

    def _build_many2one(self, comodel, vals, new_value, key, value, path):
        """
        Map the tax values from the "imposto" XML bindings into the Odoo
        Fiscal Document line tax attributes.
        """
        if key == "nfe40_ISSQN":
            self._import_tax_attrs(
                key,
                value,
                new_value,
            )

        elif key == "nfe40_ICMS":
            self._import_tax_attrs(
                key,
                value,
                new_value,
                sub_tags=ICMS_SUB_TAGS,
            )

        elif key == "nfe40_IPI":
            self._import_tax_attrs(
                key,
                value,
                new_value,
                sub_tags=[
                    "IPITrib",
                    "IPINT",
                ],
            )

        elif key == "nfe40_II":
            self._import_tax_attrs(
                key,
                value,
                new_value,
            )

        elif key == "nfe40_PIS":
            self._import_tax_attrs(
                key,
                value,
                new_value,
                sub_tags=PIS_SUB_TAGS,
            )

        elif key == "nfe40_PISST":
            self._import_tax_attrs(
                key,
                value,
                new_value,
            )

        elif key == "nfe40_COFINS":
            self._import_tax_attrs(
                key,
                value,
                new_value,
                sub_tags=COFINS_SUB_TAGS,
            )

        elif key == "nfe40_COFINSST":
            self._import_tax_attrs(
                key,
                value,
                new_value,
            )

        elif key == "nfe40_ICMSUFDest":
            self._import_tax_attrs(
                key,
                value,
                new_value,
            )

        if (
            self._name == "account.invoice.line"
            and comodel._name == "l10n_br_fiscal.document.line"
        ):
            # TODO do not hardcode!!
            # stacked m2o
            vals.update(new_value)
        else:
            return super()._build_many2one(comodel, vals, new_value, key, value, path)

    # flake8: noqa: C901
    def _import_tax_attrs(self, key, value, odoo_attrs, sub_tags=None):
        """
        Import tax attributes. First the common
        like CST, vBC, pICMS, pIPI, vICMS, vIPI...
        common for ICMS, IPI, PIS, COFINS...
        and finally the specific ones.
        """
        tax_binding = value
        kind = key.split("_")[1].lower()
        if sub_tags:
            for tag in sub_tags:
                if getattr(value, tag) is not None:
                    tax_binding = getattr(value, tag)

        def map_binding_attr(attr, odoo_attr=None):
            """
            Map binding tax attributes.
            Cast Enum and Float values.
            """
            if hasattr(tax_binding, attr) and getattr(tax_binding, attr) is not None:
                value = getattr(tax_binding, attr)
                if isinstance(value, Enum):
                    casted_value = value.value
                else:
                    casted_value = float(value)
                if odoo_attr:
                    odoo_attrs[odoo_attr] = casted_value
                return casted_value

        # common attributes CST, VBC, p*, v*:
        cst = map_binding_attr("CST")
        if cst:
            cst_id = self.env.ref(f"l10n_br_fiscal.cst_{kind}_{cst}").id
            odoo_attrs[f"{kind}_cst_id"] = cst_id
        else:
            cst_id = None

        map_binding_attr("vBC", f"{kind}_base")

        percent = map_binding_attr(
            f"p{kind.upper().replace('ST', '')}", f"{kind}_percent"
        )
        if kind in ("icms", "icmsufdest"):
            map_binding_attr("modBC", "icms_base_type")
            icms_percent_red = map_binding_attr("pRedBC", "icms_reduction")
        else:
            map_binding_attr("modBC", f"{kind}_base_type")
            icms_percent_red = None

        if "ICMSSN" in key:
            tax_group_kind = "icmssn"
        elif "ICMSST" in key:
            tax_group_kind = "icmsst"
        elif "ICMSUFDest" in key:
            tax_group_kind = "icms"
        else:
            tax_group_kind = kind
        tax_group_id = self.env.ref(f"l10n_br_fiscal.tax_group_{tax_group_kind}").id
        tax_domain = [("tax_group_id", "=", tax_group_id)]
        if percent:
            tax_domain.append(("percent_amount", "=", percent))
        tax_domain_with_cst = None
        if cst_id:
            cst_kind = "cst_{}_id".format(self.env.context.get("edoc_type", "in"))
            tax_domain_with_cst = tax_domain + [(cst_kind, "=", cst_id)]

        fiscal_tax_id = None
        if icms_percent_red:
            # first we try to match a tax with the proper pRed
            tax_domain_base = tax_domain_with_cst or tax_domain
            tax_domain_with_red = tax_domain_base + [
                ("percent_reduction", "=", icms_percent_red)
            ]
            fiscal_tax_id = self.env["l10n_br_fiscal.tax"].search(
                tax_domain_with_red,
                limit=1,
            )

        if not fiscal_tax_id:
            if tax_domain_with_cst:
                fiscal_tax_id = self.env["l10n_br_fiscal.tax"].search(
                    tax_domain_with_cst,
                    limit=1,
                )
            if not fiscal_tax_id:
                fiscal_tax_id = self.env["l10n_br_fiscal.tax"].search(
                    tax_domain,
                    limit=1,
                )

        if fiscal_tax_id:
            odoo_attrs[f"{kind}_tax_id"] = fiscal_tax_id.id
            if not odoo_attrs.get("fiscal_tax_ids"):
                odoo_attrs["fiscal_tax_ids"] = []
            odoo_attrs["fiscal_tax_ids"].append(fiscal_tax_id.id)
        elif not odoo_attrs.get(f"{kind}_tax_id"):
            nt_tax_ref = f"l10n_br_fiscal.tax_{kind}_nt"
            nt_tax = self.env.ref(nt_tax_ref, raise_if_not_found=False)
            if nt_tax:  # NOTE, can it be isento or something else?
                odoo_attrs[f"{kind}_tax_id"] = nt_tax.id

        map_binding_attr(f"v{kind.upper()}", f"{kind}_value")

        if kind in ("icms", "icmsufdest"):
            map_binding_attr("orig", "icms_origin")
            mot_des_icms = map_binding_attr("motDesICMS")
            if mot_des_icms:
                odoo_attrs["icms_relief_id"] = self.env.ref(
                    f"l10n_br_fiscal.icms_relief_{mot_des_icms}"
                ).id
            map_binding_attr("vICMSDeson", "icms_relief_value")
            map_binding_attr("vICMSSubstituto", "icms_substitute")

            # ICMS ST fields
            map_binding_attr("modBCST", "icmsst_base_type")
            map_binding_attr("pMVAST", "icmsst_mva_percent")
            map_binding_attr("pRedBCST", "icmsst_reduction")
            map_binding_attr("vBCST", "icsmst_base")
            map_binding_attr("pICMSST", "icmsst_percent")
            map_binding_attr("vICMSST", "icmsst_value")
            map_binding_attr("vBCSTRet", "icmsst_wh_base")
            map_binding_attr("vICMSSTRet", "icmsst_wh_value")

            # ICMS FCP Fields
            map_binding_attr("pFCPUFDest", "icmsfcp_percent")
            map_binding_attr("vfCPUFDest", "icmsfcp_value")
            map_binding_attr("vBCFCP", "icmsfcp_base")

            # ICMS FCP ST Fields
            map_binding_attr("vBCFCPST", "icmsfcpst_base")
            map_binding_attr("pFCPST", "icmsfcpst_percent")
            map_binding_attr("vFCPST", "icmsfcpst_value")

            # ICMS FCP ST Fields
            map_binding_attr("vBCFCPST", "icmsfcpst_base")
            map_binding_attr("pFCPST", "icmsfcpst_percent")
            map_binding_attr("vFCPST", "icmsfcpst_value")

            # ICMS DIFAL Fields
            map_binding_attr("vBCUFDest", "icms_destination_base")
            map_binding_attr("pICMSUFDest", "icms_origin_percent")
            map_binding_attr("vICMSUFDest", "icms_destination_value")
            map_binding_attr("pICMSInter", "icms_destination_percent")

            map_binding_attr("pICMSInterPart", "icms_sharing_percent")
            map_binding_attr("pICMSInterPart", "icms_sharing_percent")
            map_binding_attr("vICMSUFRemet", "icms_origin_value")
            map_binding_attr("vICMSUFDest", "icms_destination_value")

            # ICMS Simples Nacional Fields
            # TODO map icmssn_tax_id using CSOSN
            csosn = map_binding_attr("CSOSN")
            if csosn:
                odoo_attrs["icms_cst_id"] = self.env.ref(
                    f"l10n_br_fiscal.cst_icmssn_{csosn}"
                ).id
            map_binding_attr("pCredSN", "icmssn_percent")
            map_binding_attr("vCredICMSSN", "icmssn_credit_value")

            # ICMS Retido Anteriormente
            map_binding_attr("vBCSTRet", "icmsst_wh_base")
            map_binding_attr("vICMSSTRet", "icmsst_wh_value")
            map_binding_attr("vBCFCPSTRet", "icmsfcp_base_wh")
            map_binding_attr("vFCPSTRet", "icmsfcp_value_wh")
            map_binding_attr("vFCPST", "icmsfcpst_value")
            map_binding_attr("vBCEfet", "effective_base_value")
            map_binding_attr("vICMSEfet", "icms_effective_value")

        # elif kind == "pis":  # (will also apply to pisst)
        #     pass
        #     # TODO  qBCProd, vAliqProd
        #
        # elif kind == "cofins":  # (will also apply to cofinsst)
        #     pass
        #     # TODO  qBCProd, vAliqProd

    def _verify_related_many2ones(self, related_many2ones):
        if (
            related_many2ones.get("product_id", {}).get("barcode")
            and related_many2ones["product_id"]["barcode"] == "SEM GTIN"
        ):
            del related_many2ones["product_id"]["barcode"]
        return super()._verify_related_many2ones(related_many2ones)

    def _get_aditional_keys(self, model, rec_dict, keys):
        keys = super()._get_aditional_keys(model, rec_dict, keys)
        if model._name == "product.product" and rec_dict.get("barcode"):
            return ["barcode"] + keys
        return keys
