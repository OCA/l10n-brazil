# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import sys
from unicodedata import normalize

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal.constants.icms import ICMS_CST, ICMS_SN_CST
from odoo.addons.spec_driven_model.models import spec_models

ICMSSN_CST_CODES_USE_102 = ("102", "103", "300", "400")
ICMSSN_CST_CODES_USE_202 = ("202", "203")
ICMS_ST_CST_CODES = ["60", "10"]


class Tipi(models.AbstractModel):
    _inherit = "nfe.40.tipi"

    # legacy generateds-odoo choice field added manually (not by xsdata-odoo):
    nfe40_choice3 = fields.Selection(
        [("nfe40_IPITrib", "IPITrib"), ("nfe40_IPINT", "IPINT")], "IPITrib/IPINT"
    )


class NFeLine(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.line"
    _inherit = ["l10n_br_fiscal.document.line", "nfe.40.det"]
    _stacked = "nfe.40.det"
    _field_prefix = "nfe40_"
    _schema_name = "nfe"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_nfe"
    _spec_module = "odoo.addons.l10n_br_nfe_spec.models.v4_0.leiaute_nfe_v4_00"
    _spec_tab_name = "NFe"
    _stacking_points = {}
    # all m2o below this level will be stacked even if not required:
    _force_stack_paths = ("det.imposto.",)
    _stack_skip = ("nfe40_det_infNFe_id",)

    # When dynamic stacking is applied, the NFe line has the following structure.
    # NOTE GenerateDS actually has a bug here putting II before IPI
    # we fixed nfelib for NFe with II here https://github.com/akretion/nfelib/pull/47
    # fortunately xsdata doesn't have this bug.
    DET_TREE = """
> <det>
    > <prod>
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
    - <impostoDevol>"""

    # The nfe.40.prod mixin (prod XML tag) cannot be injected in
    # the product.product object because the tag includes attributes from the
    # Odoo fiscal document line and because we may have an Nfe with
    # lines decsriptions instead of full blown products.
    # So a part of the mapping is done
    # in the fiscal document line:
    # from Odoo -> XML by using related fields/_compute
    # from XML -> Odoo by overriding the product default_get method
    nfe40_cProd = fields.Char(
        related="product_id.default_code",
    )

    nfe40_cEAN = fields.Char(
        related="product_id.barcode",
    )

    nfe40_cEANTrib = fields.Char(
        related="product_id.barcode",
    )

    nfe40_uCom = fields.Char(
        related="uom_id.code",
    )

    nfe40_qCom = fields.Float(
        string="nfe40 qCom",
        related="quantity",
    )

    nfe40_vUnCom = fields.Float(
        related="price_unit",
        string="Valor unitário de comercialização",
    )

    nfe40_uTrib = fields.Char(
        related="uot_id.code",
    )

    nfe40_qTrib = fields.Float(
        string="nfe40_qTrib",
        related="fiscal_quantity",
    )

    nfe40_vUnTrib = fields.Float(
        related="fiscal_price",
        string="Valor unitário de tributação",
    )

    nfe40_vProd = fields.Monetary(
        related="price_gross",
    )

    nfe40_choice9 = fields.Selection(
        [
            ("normal", "Produto Normal"),  # overriden to allow normal product
            ("nfe40_veicProd", "Veículo"),
            ("nfe40_med", "Medicamento"),
            ("nfe40_arma", "Arma"),
            ("nfe40_comb", "Combustível"),
            ("nfe40_nRECOPI", "Número do RECOPI"),
        ],
        string="Tipo de Produto",
        default="normal",
    )

    nfe40_choice11 = fields.Selection(
        [
            ("nfe40_ICMS00", "ICMS00"),
            ("nfe40_ICMS10", "ICMS10"),
            ("nfe40_ICMS20", "ICMS20"),
            ("nfe40_ICMS30", "ICMS30"),
            ("nfe40_ICMS40", "ICMS40"),
            ("nfe40_ICMS51", "ICMS51"),
            ("nfe40_ICMS60", "ICMS60"),
            ("nfe40_ICMS70", "ICMS70"),
            ("nfe40_ICMS90", "ICMS90"),
            ("nfe40_ICMSPart", "ICMSPart"),
            ("nfe40_ICMSST", "ICMSST"),
            ("nfe40_ICMSSN101", "ICMSSN101"),
            ("nfe40_ICMSSN102", "ICMSSN102"),
            ("nfe40_ICMSSN201", "ICMSSN201"),
            ("nfe40_ICMSSN202", "ICMSSN202"),
            ("nfe40_ICMSSN500", "ICMSSN500"),
            ("nfe40_ICMSSN900", "ICMSSN900"),
        ],
        "ICMS00/ICMS10/ICMS20/ICMS30/ICMS40/ICMS51/ICMS60/I...",
        compute="_compute_choice11",
        store=True,
    )

    nfe40_choice12 = fields.Selection(
        [
            ("nfe40_PISAliq", "PISAliq"),
            ("nfe40_PISQtde", "PISQtde"),
            ("nfe40_PISNT", "PISNT"),
            ("nfe40_PISOutr", "PISOutr"),
        ],
        "PISAliq/PISQtde/PISNT/PISOutr",
        compute="_compute_choice12",
        store=True,
    )

    nfe40_choice15 = fields.Selection(
        [
            ("nfe40_COFINSAliq", "COFINSAliq"),
            ("nfe40_COFINSQtde", "COFINSQtde"),
            ("nfe40_COFINSNT", "COFINSNT"),
            ("nfe40_COFINSOutr", "COFINSOutr"),
        ],
        "COFINSAliq/COFINSQtde/COFINSNT/COFINSOutr",
        compute="_compute_choice15",
        store=True,
    )

    nfe40_choice3 = fields.Selection(
        [("nfe40_IPITrib", "IPITrib"), ("nfe40_IPINT", "IPINT")],
        "IPITrib/IPINT",
        compute="_compute_choice3",
        store=True,
    )

    nfe40_choice20 = fields.Selection(
        [
            ("nfe40_vBC", "vBC"),
            ("nfe40_pIPI", "pIPI"),
            ("nfe40_qUnid", "qUnid"),
            ("nfe40_vUnid", "vUnid"),
        ],
        "vBC/pIPI/qUnid/vUnid",
        compute="_compute_nfe40_choice20",
        store=True,
    )

    nfe40_choice13 = fields.Selection(
        [
            ("nfe40_vBC", "vBC"),
            ("nfe40_pPIS", "pPIS"),
            ("nfe40_qBCProd", "qBCProd"),
            ("nfe40_vAliqProd", "vAliqProd"),
        ],
        compute="_compute_nfe40_choice13",
        store=True,
        string="Tipo de Tributação do PIS",
    )

    nfe40_choice16 = fields.Selection(
        [
            ("nfe40_vBC", "vBC"),
            ("nfe40_pCOFINS", "pCOFINS"),
            ("nfe40_qBCProd", "qBCProd"),
            ("nfe40_vAliqProd", "vAliqProd"),
        ],
        compute="_compute_nfe40_choice16",
        store=True,
        string="Tipo de Tributação do COFINS",
    )

    nfe40_choice10 = fields.Selection(
        [
            ("nfe40_ICMS", "ICMS"),
            ("nfe40_II", "II"),
            ("nfe40_IPI", "IPI"),
            ("nfe40_ISSQN", "ISSQN"),
        ],
        "ICMS/II/IPI/ISSQN",
        compute="_compute_nfe40_choice10",
        store=True,
    )

    nfe40_orig = fields.Selection(
        related="icms_origin",
    )

    nfe40_modBC = fields.Selection(
        related="icms_base_type",
    )

    nfe40_vICMS = fields.Monetary(
        related="icms_value",
    )

    nfe40_vPIS = fields.Monetary(
        string="Valor do PIS (NFe)",
        related="pis_value",
    )

    nfe40_vCOFINS = fields.Monetary(
        string="Valor do COFINS (NFe)",
        related="cofins_value",
    )

    nfe40_CFOP = fields.Char(
        related="cfop_id.code",
    )

    nfe40_indTot = fields.Selection(
        default="1",
    )

    nfe40_vIPI = fields.Monetary(
        related="ipi_value",
    )

    nfe40_infAdProd = fields.Char(
        compute="_compute_nfe40_infAdProd",
    )

    nfe40_xPed = fields.Char(
        related="partner_order",
    )

    nfe40_nItemPed = fields.Char(
        related="partner_order_line",
    )

    nfe40_vFrete = fields.Monetary(
        related="freight_value",
    )

    nfe40_vSeg = fields.Monetary(
        related="insurance_value",
    )

    nfe40_vOutro = fields.Monetary(
        related="other_value",
    )

    nfe40_vTotTrib = fields.Monetary(
        related="estimate_tax",
    )

    nfe40_PISAliq = fields.Many2one(
        "nfe.40.pisaliq",
        string="Código de Situação Tributária do PIS (Alíquota)",
        help="Código de Situação Tributária do PIS."
        "\n01 – Operação Tributável - Base de Cálculo = Valor da Operação"
        "\nAlíquota Normal (Cumulativo/Não Cumulativo);"
        "\n02 - Operação Tributável - Base de Calculo = Valor da Operação"
        "\n(Alíquota Diferenciada);",
    )

    nfe40_COFINSAliq = fields.Many2one(
        "nfe.40.cofinsaliq",
        string="Código de Situação Tributária do COFINS (Alíquota)",
        help="Código de Situação Tributária do COFINS."
        "\n01 – Operação Tributável - Base de Cálculo = Valor da Operação"
        "\nAlíquota Normal (Cumulativo/Não Cumulativo);"
        "\n02 - Operação Tributável - Base de Calculo = Valor da Operação"
        "\n(Alíquota Diferenciada);",
    )

    # Todo: Calcular
    nfe40_vFCPUFDest = fields.Monetary(
        string="Valor total do ICMS relativo ao Fundo de Combate à Pobreza",
    )

    # Todo: Calcular
    nfe40_vFCPSTRet = fields.Monetary(
        string="Valor do ICMS relativo ao Fundo de Combate à Pobreza Retido por ST",
    )
    nfe40_vCredICMSSN = fields.Monetary(
        string="ICMS SN Crédito", related="icmssn_credit_value"
    )
    nfe40_vDesc = fields.Monetary(related="discount_value")

    # TODO toxic field from several tags, should not even be injected!
    # meanwhile forcing a string on it avoids .pot issues.
    nfe40_vBC = fields.Monetary(string="FIXME Não usar esse campo!")

    nfe40_vBCST = fields.Monetary(related="icmsst_base")
    nfe40_modBCST = fields.Selection(related="icmsst_base_type")
    nfe40_vICMSST = fields.Monetary(related="icmsst_value")

    @api.depends("additional_data")
    def _compute_nfe40_infAdProd(self):
        for record in self:
            if record.additional_data:
                record.nfe40_infAdProd = (
                    normalize("NFKD", record.additional_data)
                    .encode("ASCII", "ignore")
                    .decode("ASCII")
                    .replace("\n", "")
                    .replace("\r", "")
                )
            else:
                record.nfe40_infAdProd = False

    @api.depends("icms_cst_id")
    def _compute_choice11(self):
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

            record.nfe40_choice11 = icms_choice

    @api.depends("pis_cst_id")
    def _compute_choice12(self):
        for record in self:
            if record.pis_cst_id.code in ["01", "02"]:
                record.nfe40_choice12 = "nfe40_PISAliq"
            elif record.pis_cst_id.code == "03":
                record.nfe40_choice12 = "nfe40_PISQtde"
            elif record.pis_cst_id.code in ["04", "06", "07", "08", "09"]:
                record.nfe40_choice12 = "nfe40_PISNT"
            else:
                record.nfe40_choice12 = "nfe40_PISOutr"

    @api.depends("cofins_cst_id")
    def _compute_choice15(self):
        for record in self:
            if record.cofins_cst_id.code in ["01", "02"]:
                record.nfe40_choice15 = "nfe40_COFINSAliq"
            elif record.cofins_cst_id.code == "03":
                record.nfe40_choice15 = "nfe40_COFINSQtde"
            elif record.cofins_cst_id.code in ["04", "06", "07", "08", "09"]:
                record.nfe40_choice15 = "nfe40_COFINSNT"
            else:
                record.nfe40_choice15 = "nfe40_COFINSOutr"

    @api.depends("ipi_cst_id")
    def _compute_choice3(self):
        for record in self:
            if record.ipi_cst_id.code in ["00", "49", "50", "99"]:
                record.nfe40_choice3 = "nfe40_IPITrib"
            else:
                record.nfe40_choice3 = "nfe40_IPINT"

    @api.depends("ipi_base_type")
    def _compute_nfe40_choice20(self):
        for record in self:
            if record.ipi_base_type == "percent":
                record.nfe40_choice20 = "nfe40_pIPI"
            else:
                record.nfe40_choice20 = "nfe40_vUnid"

    @api.depends("pis_base_type")
    def _compute_nfe40_choice13(self):
        for record in self:
            if record.pis_base_type == "percent":
                record.nfe40_choice13 = "nfe40_pPIS"
            else:
                record.nfe40_choice13 = "nfe40_vAliqProd"

    @api.depends("cofins_base_type")
    def _compute_nfe40_choice16(self):
        for record in self:
            if record.cofins_base_type == "percent":
                record.nfe40_choice16 = "nfe40_pCOFINS"
            else:
                record.nfe40_choice16 = "nfe40_vAliqProd"

    @api.depends("tax_icms_or_issqn")
    def _compute_nfe40_choice10(self):
        for record in self:
            if record.tax_icms_or_issqn == "icms":
                record.nfe40_choice10 = "nfe40_ICMS"
            else:
                record.nfe40_choice10 = "nfe40_ISSQN"

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

    def _export_fields_icms(self):
        icms = {
            # ICMS
            "orig": self.nfe40_orig,
            "cst": self.icms_cst_id.code,
            "mod_bc": self.icms_base_type,
            "v_bc": str("%.02f" % self.icms_base),
            "p_red_bc": str("%.04f" % self.icms_reduction),
            "p_icms": str("%.04f" % self.icms_percent),
            "v_icms": str("%.02f" % self.icms_value),
            "v_icmssubstituto": str("%.02f" % self.icms_substitute),
            # ICMS SUBSTITUIÇÃO TRIBUTÁRIA
            "mod_bcst": self.icmsst_base_type,
            "p_mvast": str("%.04f" % self.icmsst_mva_percent),
            "p_red_bcst": str("%.04f" % self.icmsst_reduction),
            "v_bcst": str("%.02f" % self.icmsst_base),
            "p_icmsst": str("%.04f" % self.icmsst_percent),
            "v_icmsst": str("%.02f" % self.icmsst_value),
            "ufst": self.partner_id.state_id.code,
            # ICMS COBRADO ANTERIORMENTE POR SUBSTITUIÇÃO TRIBUTÁRIA
            "v_bcst_ret": str("%.02f" % self.icmsst_wh_base),
            "p_st": str("%.04f" % (self.icmsst_wh_percent + self.icmsfcp_wh_percent)),
            "v_icmsst_ret": str("%.02f" % self.icmsst_wh_value),
            "vBCFCPSTRet": str("%.02f" % self.icmsfcp_base_wh),
            "v_bcfcpstret": str("%.04f" % self.icmsfcp_wh_percent),
            "v_fcpstret": str("%.02f" % self.icmsfcp_value_wh),
            "p_red_bcefet": str("%.04f" % self.icms_effective_reduction),
            "v_bcefet": str("%.02f" % self.icms_effective_base),
            "p_icmsefet": str("%.04f" % self.icms_effective_percent),
            "v_icmsefet": str("%.02f" % self.icms_effective_value),
            # ICMS SIMPLES NACIONAL
            "csosn": self.icms_cst_id.code,
            "p_cred_sn": str("%.04f" % self.icmssn_percent),
            "v_cred_icmssn": str("%.02f" % self.icmssn_credit_value),
        }
        if self.icmsfcp_percent:
            icms.update(
                {
                    # FUNDO DE COMBATE À POBREZA
                    "vBCFCPST": str("%.02f" % self.icmsfcp_base),
                    "pFCPST": str("%.04f" % self.icmsfcp_percent),
                    "vFCPST": str("%.02f" % self.icmsfcpst_value),
                }
            )
        return icms

    def _export_fields(self, xsd_fields, class_obj, export_dict):
        if class_obj._name == "nfe.40.imposto":
            xsd_fields = [i for i in xsd_fields]
            if self.nfe40_choice10 == "nfe40_ICMS":
                xsd_fields.remove("nfe40_ISSQN")
            else:
                xsd_fields.remove("nfe40_ICMS")
                xsd_fields.remove("nfe40_II")
        elif class_obj._name == "nfe.40.icms":
            xsd_fields = [self.nfe40_choice11]
            icms_tag = (
                self.nfe40_choice11.replace("nfe40_", "")
                .replace("ICMS", "Icms")
                .replace("IcmsSN", "Icmssn")
            )  # FIXME
            binding_module = sys.modules[self._binding_module]
            # Tnfe.InfNfe.Det.Imposto.Icms.Icms00
            # see https://stackoverflow.com/questions/31174295/getattr-and-setattr-on-nested-subobjects-chained-properties
            tnfe = getattr(binding_module, "Tnfe")
            infnfe = getattr(tnfe, "InfNfe")
            det = getattr(infnfe, "Det")
            imposto = getattr(det, "Imposto")
            icms = getattr(imposto, "Icms")
            icms_binding = getattr(icms, icms_tag)
            icms_dict = self._export_fields_icms()
            # TODO filter icms_dict with icms_binding fields, see in spec_model
            sliced_icms_dict = {
                key: icms_dict.get(key)
                for key in icms_binding.__dataclass_fields__.keys()
            }
            export_dict[icms_tag.lower()] = icms_binding(**sliced_icms_dict)
        elif class_obj._name == "nfe.40.icmsufdest":
            # DIFAL
            self.nfe40_vBCUFDest = str("%.02f" % self.icms_destination_base)
            self.nfe40_vBCFCPUFDest = str("%.02f" % self.icmsfcp_base)
            self.nfe40_pFCPUFDest = str("%.04f" % self.icmsfcp_percent)
            self.nfe40_pICMSUFDest = str("%.04f" % self.icms_destination_percent)
            self.nfe40_pICMSInter = str(
                "%.02f" % self.icms_origin_percent or self.icms_percent
            )
            self.nfe40_pICMSInterPart = str(
                "%.04f" % self.icms_sharing_percent or 100.0
            )
            self.nfe40_vFCPUFDest = str("%.02f" % self.icmsfcp_value)
            self.nfe40_vICMSUFDest = str("%.02f" % self.icms_destination_value)
            self.nfe40_vICMSUFRemet = str("%.02f" % self.icms_origin_value)
        elif class_obj._name == "nfe.40.tipi":
            xsd_fields = [
                f
                for f in xsd_fields
                if f not in [i[0] for i in class_obj._fields["nfe40_choice3"].selection]
            ]
            xsd_fields += [self.nfe40_choice3]
        elif class_obj._name == "nfe.40.pis":
            xsd_fields = [self.nfe40_choice12]
        elif class_obj._name == "nfe.40.cofins":
            xsd_fields = [self.nfe40_choice15]
        elif class_obj._name == "nfe.40.ipitrib":
            xsd_fields = [i for i in xsd_fields]
            if self.nfe40_choice20 == "nfe40_pIPI":
                xsd_fields.remove("nfe40_qUnid")
                xsd_fields.remove("nfe40_vUnid")
            else:
                xsd_fields.remove("nfe40_vBC")
                xsd_fields.remove("nfe40_pIPI")
        elif class_obj._name == "nfe.40.pisoutr":
            xsd_fields = [i for i in xsd_fields]
            if self.nfe40_choice13 == "nfe40_pPIS":
                xsd_fields.remove("nfe40_qBCProd")
                xsd_fields.remove("nfe40_vAliqProd")
            else:
                xsd_fields.remove("nfe40_vBC")
                xsd_fields.remove("nfe40_pPIS")
        elif class_obj._name == "nfe.40.cofinsoutr":
            xsd_fields = [i for i in xsd_fields]
            if self.nfe40_choice16 == "nfe40_pCOFINS":
                xsd_fields.remove("nfe40_qBCProd")
                xsd_fields.remove("nfe40_vAliqProd")
            else:
                xsd_fields.remove("nfe40_vBC")
                xsd_fields.remove("nfe40_pCOFINS")

        self.nfe40_NCM = self.ncm_id.code_unmasked or False
        self.nfe40_CEST = self.cest_id and self.cest_id.code_unmasked or False
        self.nfe40_pICMS = self.icms_percent
        self.nfe40_pICMSST = self.icmsst_percent
        self.nfe40_pMVAST = self.icmsst_mva_percent
        self.nfe40_pRedBCST = self.icmsst_reduction
        self.nfe40_pIPI = self.ipi_percent
        self.nfe40_pPIS = self.pis_percent
        self.nfe40_pCOFINS = self.cofins_percent
        self.nfe40_cEnq = str(self.ipi_guideline_id.code or "999").zfill(3)
        return super()._export_fields(xsd_fields, class_obj, export_dict)

    # flake8: noqa: C901
    def _export_field(self, xsd_field, class_obj, field_spec, export_value=None):
        xsd_type = field_spec.xsd_type if hasattr(field_spec, "xsd_type") else None
        # ISSQN
        if xsd_field == "nfe40_cMunFG":
            return self.issqn_fg_city_id.ibge_code
        if xsd_field == "nfe40_cListServ":
            return self.service_type_id.code
        if xsd_field == "nfe40_vDeducao":
            return self.issqn_deduction_amount
        if xsd_field == "nfe40_vOutro":
            return self.issqn_other_amount
        if xsd_field == "nfe40_vDescIncond":
            return self.issqn_desc_incond_amount
        if xsd_field == "nfe40_vDescCond":
            return self.issqn_desc_cond_amount
        if xsd_field == "nfe40_vISSRet":
            return self.issqn_wh_value
        if xsd_field == "nfe40_indISS":
            return self.issqn_eligibility
        if xsd_field == "nfe40_cServico":
            return ""  # TODO
        if xsd_field == "nfe40_cMun":
            return self.issqn_fg_city_id.ibge_code  # TODO
        if xsd_field == "nfe40_cPais" and self.issqn_fg_city_id:
            return self.issqn_fg_city_id.state_id.country_id.bc_code[1:]  # TODO
        if xsd_field == "nfe40_nProcesso":
            return ""  # TODO
        if xsd_field == "nfe40_indIncentivo":
            return self.issqn_incentive
        if xsd_field == "nfe40_xProd":
            return self.name[:120].replace("\n", "").strip()
        if xsd_field in ["nfe40_cEAN", "nfe40_cEANTrib"] and not self[xsd_field]:
            return "SEM GTIN"
        elif xsd_field == "nfe40_CST":
            if class_obj._name.startswith("nfe.40.icms"):
                return self.icms_cst_id.code
            elif class_obj._name.startswith("nfe.40.ipi"):
                return self.ipi_cst_id.code
            elif class_obj._name.startswith("nfe.40.pis"):
                return self.pis_cst_id.code
            elif class_obj._name.startswith("nfe.40.cofins"):
                return self.cofins_cst_id.code
        elif xsd_field == "nfe40_CSOSN":
            if self.nfe40_choice11 == "nfe40_ICMSSN101":
                return "101"
        elif xsd_field == "nfe40_vBC":
            field_name = "nfe40_vBC"
            if class_obj._name.startswith("nfe.40.icms"):
                field_name = "icms_base"
            elif class_obj._name.startswith("nfe.40.ipi"):
                field_name = "ipi_base"
            elif class_obj._name.startswith("nfe.40.pis"):
                field_name = "pis_base"
            elif class_obj._name.startswith("nfe.40.cofins"):
                field_name = "cofins_base"
            return self._export_float_monetary(
                field_name,
                xsd_type or "TDec_1302",  # (None for pis/cofins)
                class_obj,
                class_obj._fields[xsd_field].xsd_required
                if hasattr(class_obj._fields[xsd_field], "xsd_required")
                else False,
            )
        elif xsd_field in (
            "nfe40_vBCSTRet",
            "nfe40_pST",
            "nfe40_vICMSSubstituto",
            "nfe40_vICMSSTRet",
        ):
            if self.icms_cst_id.code in ICMS_ST_CST_CODES:
                return self._export_float_monetary(xsd_field, xsd_type, class_obj, True)
        else:
            return super()._export_field(xsd_field, class_obj, field_spec)

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        self.ensure_one()
        if field_name in self._stacking_points.keys():
            if field_name == "nfe40_ISSQN" and not self.service_type_id:
                return False
            elif field_name == "nfe40_ICMS" and self.service_type_id:
                return False
            elif field_name == "nfe40_ICMSUFDest" and (
                not self.icms_value
                or self.partner_id.ind_ie_dest != "9"
                or self.partner_id.state_id == self.company_id.state_id
                or self.partner_id.country_id != self.company_id.country_id
            ):
                return False
            # TODO add condition
            elif field_name in ["nfe40_II", "nfe40_PISST", "nfe40_COFINSST"]:
                return False

            elif (not xsd_required) and field_name not in [
                "nfe40_PIS",
                "nfe40_COFINS",
                "nfe40_IPI",
                "nfe40_ICMSUFDest",
            ]:
                comodel = self.env[self._stacking_points.get(field_name).comodel_name]
                fields = [
                    f for f in comodel._fields if f.startswith(self._field_prefix)
                ]
                sub_tag_read = self.read(fields)[0]
                if not any(
                    v
                    for k, v in sub_tag_read.items()
                    if k.startswith(self._field_prefix)
                ):
                    return False

        return super()._export_many2one(field_name, xsd_required, class_obj)

    def _export_float_monetary(
        self, field_name, xsd_type, class_obj, xsd_required, export_value=None
    ):
        if not self[field_name] and not xsd_required:
            if not (
                class_obj._name == "nfe.40.imposto" and field_name == "nfe40_vTotTrib"
            ) and not (class_obj._name == "nfe.40.fat"):
                self[field_name] = False
                return False
        return super()._export_float_monetary(
            field_name, xsd_type, class_obj, xsd_required
        )

    def _build_attr(self, node, fields, vals, path, attr):
        key = "nfe40_%s" % (attr[0])  # TODO schema wise
        value = getattr(node, attr[0])

        if key.startswith("nfe40_ICMS") and key not in [
            "nfe40_ICMS",
            "nfe40_ICMSTot",
            "nfe40_ICMSUFDest",
        ]:
            vals["nfe40_choice11"] = key

        if key.startswith("nfe40_IPI") and key != "nfe40_IPI":
            vals["nfe40_choice3"] = key

        if key.startswith("nfe40_PIS") and key not in ["nfe40_PIS", "nfe40_PISST"]:
            vals["nfe40_choice12"] = key

        if key.startswith("nfe40_COFINS") and key not in [
            "nfe40_COFINS",
            "nfe40_COFINSST",
        ]:
            vals["nfe40_choice15"] = key

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
        if key == "nfe40_pICMS":
            vals["icms_percent"] = float(value)
        if key == "nfe40_pIPI":
            vals["ipi_percent"] = float(value or 0.00)
        if key == "nfe40_pPIS":
            vals["pis_percent"] = float(value or 0.00)
        if key == "nfe40_pCOFINS":
            vals["cofins_percent"] = float(value or 0.00)
        if key == "nfe40_cEnq":
            vals["ipi_guideline_id"] = (
                self.env["l10n_br_fiscal.tax.ipi.guideline"]
                .search([("code_unmasked", "=", value)], limit=1)
                .id
            )

        return super()._build_attr(node, fields, vals, path, attr)

    def _build_string_not_simple_type(self, key, vals, value, node):
        if key not in ["nfe40_CST", "nfe40_modBC", "nfe40_CSOSN", "nfe40_vBC"]:
            return super()._build_string_not_simple_type(key, vals, value, node)
            # TODO avoid collision with cls prefix
        elif key == "nfe40_CST":
            if str(type(node)).startswith("Tnfe.InfNfe.Det.Imposto.Icms"):
                vals["icms_cst_id"] = (
                    self.env["l10n_br_fiscal.cst"]
                    .search([("code", "=", value), ("tax_domain", "=", "icms")])[0]
                    .id
                )
            elif str(type(node)).startswith("Tnfe.InfNfe.Det.Imposto.Ipi"):
                vals["ipi_cst_id"] = (
                    self.env["l10n_br_fiscal.cst"]
                    .search([("code", "=", value), ("tax_domain", "=", "ipi")])[0]
                    .id
                )
            elif str(type(node)).startswith("Tnfe.InfNfe.Det.Imposto.Pis"):
                vals["pis_cst_id"] = (
                    self.env["l10n_br_fiscal.cst"]
                    .search([("code", "=", value), ("tax_domain", "=", "pis")])[0]
                    .id
                )
            elif str(type(node)).startswith("Tnfe.InfNfe.Det.Imposto.Cofins"):
                vals["cofins_cst_id"] = (
                    self.env["l10n_br_fiscal.cst"]
                    .search([("code", "=", value), ("tax_domain", "=", "cofins")])[0]
                    .id
                )
        elif key == "nfe40_modBC":
            vals["icms_base_type"] = value
        elif key == "nfe40_vBC":
            if str(type(node)).startswith("Tnfe.InfNfe.Det.Imposto.Icms"):
                vals["icms_base"] = value
            elif str(type(node)).startswith("Tnfe.InfNfe.Det.Imposto.Ipi"):
                vals["ipi_base"] = value
            elif str(type(node)).startswith("Tnfe.InfNfe.Det.Imposto.Pis"):
                vals["pis_base"] = value
            elif str(type(node)).startswith("Tnfe.InfNfe.Det.Imposto.Cofins"):
                vals["cofins_base"] = value

    # flake8: noqa: C901
    def _build_many2one(self, comodel, vals, new_value, key, value, path):
        ICMS_TAGS = [
            "icms00",
            "icms10",
            "icms20",
            "icms30",
            "icms40",
            "icms51",
            "icms60",
            "icms70",
            "icms90",
            "icmspart",
            "icmsst",
            "icmssn101",
            "icmssn102",
            "icmssn500",
            "icmssn900",
        ]

        if key == "nfe40_ISSQN":
            pass
            # TODO ISSQN Fields
        elif key == "nfe40_ICMS":
            # TODO extract method
            icms_vals = {}
            for tag in ICMS_TAGS:
                if getattr(value, tag) is not None:
                    icms = getattr(value, tag)

                    # ICMSxx fields
                    # TODO map icms_tax_id
                    if hasattr(icms, "cst") and icms.cst is not None:
                        icms_vals["icms_cst_id"] = self.env.ref(
                            "l10n_br_fiscal.cst_icms_%s" % (icms.cst.value,)
                        ).id
                        # TODO search + log if not found
                    if hasattr(icms, "mod_bc") and icms.mod_bc is not None:
                        icms_vals["icms_base_type"] = icms.mod_bc.value
                    if hasattr(icms, "orig"):
                        icms_vals["icms_origin"] = icms.orig.value
                    if hasattr(icms, "v_bc") and icms.v_bc is not None:
                        icms_vals["icms_base"] = float(icms.v_bc)
                    if hasattr(icms, "p_icms") and icms.p_icms is not None:
                        icms_vals["icms_percent"] = float(icms.p_icms)
                    if hasattr(icms, "v_icms") and icms.v_icms is not None:
                        icms_vals["icms_value"] = float(icms.v_icms)
                    if hasattr(icms, "p_red_bc") and icms.p_red_bc is not None:
                        icms_vals["icms_reduction"] = float(icms.p_red_bc)
                    if hasattr(icms, "mot_des_icms") and icms.mot_des_icms is not None:
                        icms_vals["icms_relief_id"] = self.env.ref(
                            "l10n_br_fiscal.icms_relief_%s" % (icms.mot_des_icms.value,)
                        ).id
                    if hasattr(icms, "v_icms_deson") and icms.v_icms_deson is not None:
                        icms_vals["icms_relief_value"] = float(icms.v_icms_deson)
                    if (
                        hasattr(icms, "v_icms_substituto")
                        and icms.v_icms_substituto is not None
                    ):
                        icms_vals["icms_substitute"] = float(icms.v_icms_substituto)

                    # ICMS ST fields
                    # TODO map icmsst_tax_id
                    if hasattr(icms, "mod_bcst") and icms.mod_bcst is not None:
                        icms_vals["icmsst_base_type"] = icms.mod_bcst.value
                    if hasattr(icms, "p_mvast") and icms.p_mvast is not None:
                        icms_vals["icmsst_mva_percent"] = float(icms.p_mvast)
                    if hasattr(icms, "p_red_bcst") and icms.p_red_bcst is not None:
                        icms_vals["icmsst_reduction"] = float(icms.p_red_bcst)
                    if hasattr(icms, "v_bcst") and icms.v_bcst is not None:
                        icms_vals["icmsst_base"] = float(icms.v_bcst)
                    if hasattr(icms, "p_icmsst") and icms.p_icmsst is not None:
                        icms_vals["icmsst_percent"] = float(icms.p_icmsst)
                    if hasattr(icms, "v_icmsst") and icms.v_icmsst is not None:
                        icms_vals["icmsst_value"] = float(icms.v_icmsst)
                    if hasattr(icms, "v_bcstret") and icms.v_bcstret is not None:
                        icms_vals["icmsst_wh_base"] = float(icms.v_bcstret)
                    if hasattr(icms, "v_icmsstret") and icms.v_icmsstret is not None:
                        icms_vals["icmsst_wh_value"] = float(icms.v_icmsstret)

                    # ICMS FCP Fields
                    # TODO map icmsfcp_tax_id
                    if hasattr(icms, "pFCPUFDest") and icms.pFCPUFDest is not None:
                        icms_vals["icmsfcp_percent"] = float(icms.pFCPUFDest)
                    if hasattr(icms, "vFCPUFDest") and icms.vFCPUFDest is not None:
                        icms_vals["icmsfcp_value"] = float(icms.vFCPUFDest)
                    if hasattr(icms, "vBCFCPST") and icms.vBCFCPST is not None:
                        icms_vals["icmsfcp_base"] = float(icms.vBCFCPST)

                    # ICMS DIFAL Fields
                    if (
                        hasattr(icms, "v_bcfcpufdest")
                        and icms.v_bcfcpufdest is not None
                    ):
                        icms_vals["icms_destination_base"] = float(icms.v_bcfcpufdest)
                    if hasattr(icms, "p_fcpufdest") and icms.p_fcpufdest is not None:
                        icms_vals["icms_origin_percent"] = float(icms.p_fcpufdest)
                    if hasattr(icms, "p_icmsinter") and icms.p_icmsinter is not None:
                        icms_vals["icms_destination_percent"] = float(icms.p_icmsinter)

                    if (
                        hasattr(icms, "p_icmsinter_part")
                        and icms.p_icmsinter_part is not None
                    ):
                        icms_vals["icms_sharing_percent"] = float(icms.p_icmsinter_part)
                    if (
                        hasattr(icms, "v_icmsufremet")
                        and icms.v_icmsufremet is not None
                    ):
                        icms_vals["icms_origin_value"] = float(icms.v_icmsufremet)
                    if hasattr(icms, "v_icmsufdest"):
                        icms_vals["icms_destination_value"] = float(icms.v_icmsufdest)

                    # ICMS Simples Nacional Fields
                    # TODO map icmssn_tax_id using CSOSN
                    if hasattr(icms, "csosn") and icms.csosn is not None:
                        icms_vals["icms_cst_id"] = self.env.ref(
                            "l10n_br_fiscal.cst_icmssn_%s" % (icms.csosn.value,)
                        ).id
                    if hasattr(icms, "p_cred_sn") and icms.p_cred_sn is not None:
                        icms_vals["icmssn_percent"] = float(icms.p_cred_sn)
                    if (
                        hasattr(icms, "v_cred_icmssn")
                        and icms.v_cred_icmssn is not None
                    ):
                        icms_vals["icmssn_credit_value"] = float(icms.v_cred_icmssn)

                    # ICMS Retido Anteriormente
                    if hasattr(icms, "v_bcstret") and icms.v_bcstret is not None:
                        icms_vals["icmsst_wh_base"] = float(icms.v_bcstret)
                    if hasattr(icms, "v_icmsstret") and icms.v_icmsstret is not None:
                        icms_vals["icmsst_wh_value"] = float(icms.v_icmsstret)
                    if hasattr(icms, "v_bcfcpstret") and icms.v_bcfcpstret is not None:
                        icms_vals["icmsfcp_base_wh"] = float(icms.v_bcfcpstret)
                    if hasattr(icms, "v_fcpstret") and icms.v_fcpstret is not None:
                        icms_vals["icmsfcp_value_wh"] = float(icms.v_fcpstret)
                    if hasattr(icms, "v_fcpst") and icms.v_fcpst is not None:
                        icms_vals["icmsfcpst_value"] = float(icms.v_fcpst)
                    if hasattr(icms, "v_bcefet") and icms.v_bcefet is not None:
                        icms_vals["effective_base_value"] = float(icms.v_bcefet)
                    if hasattr(icms, "v_icmsefet") and icms.v_icmsefet is not None:
                        icms_vals["icms_effective_value"] = float(icms.v_icmsefet)
            new_value.update(icms_vals)
        elif key == "nfe40_IPI":
            pass
            # IPI Fields

            # II Fields

            # COFINS

            # COFINS ST

            # PIS

            # PIS ST

            # ICMSPart fields

            # ICMSSN fields

            # TODO
        if (
            self._name == "account.invoice.line"
            and comodel._name == "l10n_br_fiscal.document.line"
        ):
            # TODO do not hardcode!!
            # stacked m2o
            vals.update(new_value)
        else:
            return super()._build_many2one(comodel, vals, new_value, key, value, path)

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
