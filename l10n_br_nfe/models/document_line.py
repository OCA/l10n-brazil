# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import sys
from unicodedata import normalize

from odoo import api, fields

from odoo.addons.l10n_br_fiscal.constants.icms import ICMS_CST, ICMS_SN_CST
from odoo.addons.spec_driven_model.models import spec_models

ICMSSN_CST_CODES_USE_102 = ("102", "103", "300", "400")
ICMSSN_CST_CODES_USE_202 = ("202", "203")
ICMS_ST_CST_CODES = ["60", "10"]


class NFeLine(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.line"
    _inherit = ["l10n_br_fiscal.document.line", "nfe.40.det"]
    _stacked = "nfe.40.det"
    _field_prefix = "nfe40_"
    _schema_name = "nfe"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_nfe"
    _spec_module = "odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe"
    _spec_tab_name = "NFe"
    _stack_skip = "nfe40_det_infNFe_id"
    _stacking_points = {}
    # all m2o below this level will be stacked even if not required:
    _force_stack_paths = ("det.imposto",)

    # The generateDS prod mixin (prod XML tag) cannot be inject in
    # the product.product object because the tag embeded values from the
    # fiscal document line. So the mapping is done:
    # from Odoo -> XML by using related fields/_compute
    # from XML -> Odoo by overriding the product create method
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
        compute="_compute_choice11",
        store=True,
    )

    nfe40_choice12 = fields.Selection(
        compute="_compute_choice12",
        store=True,
    )

    nfe40_choice15 = fields.Selection(
        compute="_compute_choice15",
        store=True,
    )

    nfe40_choice3 = fields.Selection(
        compute="_compute_choice3",
        store=True,
    )

    nfe40_choice20 = fields.Selection(
        compute="_compute_nfe40_choice20",
        store=True,
    )

    nfe40_choice13 = fields.Selection(
        compute="_compute_nfe40_choice13",
        store=True,
        string="Tipo de Tributação do PIS",
    )

    nfe40_choice16 = fields.Selection(
        compute="_compute_nfe40_choice16",
        store=True,
        string="Tipo de Tributação do COFINS",
    )

    nfe40_choice10 = fields.Selection(
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
    def _prepare_import_dict(self, values, model=None):
        values = super()._prepare_import_dict(values, model)
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
            "vBCFCPSTRet": str("%.02f" % self.icmsfcp_base_wh),
            "pFCPSTRet": str("%.04f" % self.icmsfcp_wh_percent),
            "vFCPSTRet": str("%.02f" % self.icmsfcp_value_wh),
            "pRedBCEfet": str("%.04f" % self.icms_effective_reduction),
            "vBCEfet": str("%.02f" % self.icms_effective_base),
            "pICMSEfet": str("%.04f" % self.icms_effective_percent),
            "vICMSEfet": str("%.02f" % self.icms_effective_value),
            # ICMS SIMPLES NACIONAL
            "CSOSN": self.icms_cst_id.code,
            "pCredSN": str("%.04f" % self.icmssn_percent),
            "vCredICMSSN": str("%.02f" % self.icmssn_credit_value),
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
            icms_tag = self.nfe40_choice11.replace("nfe40_", "")  # FIXME
            binding_module = sys.modules[self._binding_module]
            icms_binding = getattr(binding_module, icms_tag + "Type")
            icms_dict = self._export_fields_icms()
            export_dict[icms_tag] = icms_binding(**icms_dict)
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
    def _export_field(self, xsd_field, class_obj, member_spec):
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
                member_spec,
                class_obj,
                class_obj._fields[xsd_field].xsd_required,
            )
        elif xsd_field in (
            "nfe40_vBCSTRet",
            "nfe40_pST",
            "nfe40_vICMSSubstituto",
            "nfe40_vICMSSTRet",
        ):
            if self.icms_cst_id.code in ICMS_ST_CST_CODES:
                return self._export_float_monetary(
                    xsd_field, member_spec, class_obj, True
                )
        else:
            return super()._export_field(xsd_field, class_obj, member_spec)

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

    def _export_float_monetary(self, field_name, member_spec, class_obj, xsd_required):
        if not self[field_name] and not xsd_required:
            if not (
                class_obj._name == "nfe.40.imposto" and field_name == "nfe40_vTotTrib"
            ) and not (class_obj._name == "nfe.40.fat"):
                self[field_name] = False
                return False
        return super()._export_float_monetary(
            field_name, member_spec, class_obj, xsd_required
        )

    def _build_attr(self, node, fields, vals, path, attr):
        key = "nfe40_%s" % (attr.get_name(),)  # TODO schema wise
        value = getattr(node, attr.get_name())

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
            super()._build_string_not_simple_type(key, vals, value, node)
            # TODO avoid collision with cls prefix
        elif key == "nfe40_CST":
            if node.original_tagname_.startswith("ICMS"):
                vals["icms_cst_id"] = (
                    self.env["l10n_br_fiscal.cst"]
                    .search([("code", "=", value), ("tax_domain", "=", "icms")])[0]
                    .id
                )
            if node.original_tagname_.startswith("IPI"):
                vals["ipi_cst_id"] = (
                    self.env["l10n_br_fiscal.cst"]
                    .search([("code", "=", value), ("tax_domain", "=", "ipi")])[0]
                    .id
                )
            if node.original_tagname_.startswith("PIS"):
                vals["pis_cst_id"] = (
                    self.env["l10n_br_fiscal.cst"]
                    .search([("code", "=", value), ("tax_domain", "=", "pis")])[0]
                    .id
                )
            if node.original_tagname_.startswith("COFINS"):
                vals["cofins_cst_id"] = (
                    self.env["l10n_br_fiscal.cst"]
                    .search([("code", "=", value), ("tax_domain", "=", "cofins")])[0]
                    .id
                )
        elif key == "nfe40_modBC":
            vals["icms_base_type"] = value
        elif key == "nfe40_vBC":
            if node.original_tagname_.startswith("ICMS"):
                vals["icms_base"] = value
            elif node.original_tagname_.startswith("IPI"):
                vals["ipi_base"] = value
            elif node.original_tagname_.startswith("PIS"):
                vals["pis_base"] = value
            elif node.original_tagname_.startswith("COFINS"):
                vals["cofins_base"] = value

    # flake8: noqa: C901
    def _build_many2one(self, comodel, vals, new_value, key, value, path):
        ICMS_TAGS = [
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
            "ICMSSN500",
            "ICMSSN900",
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
                    if hasattr(icms, "CST") and icms.CST is not None:
                        icms_vals["icms_cst_id"] = self.env.ref(
                            "l10n_br_fiscal.cst_icms_%s" % (icms.CST,)
                        ).id
                        # TODO search + log if not found
                    if hasattr(icms, "modBC") and icms.modBC is not None:
                        icms_vals["icms_base_type"] = float(icms.modBC)
                    if hasattr(icms, "orig"):
                        icms_vals["icms_origin"] = icms.orig
                    if hasattr(icms, "vBC") and icms.vBC is not None:
                        icms_vals["icms_base"] = float(icms.vBC)
                    if hasattr(icms, "pICMS") and icms.pICMS is not None:
                        icms_vals["icms_percent"] = float(icms.pICMS)
                    if hasattr(icms, "vICMS") and icms.vICMS is not None:
                        icms_vals["icms_value"] = float(icms.vICMS)
                    if hasattr(icms, "pRedBC") and icms.pRedBC is not None:
                        icms_vals["icms_reduction"] = float(icms.pRedBC)
                    if hasattr(icms, "motDesICMS") and icms.motDesICMS is not None:
                        icms_vals["icms_relief_id"] = self.env.ref(
                            "l10n_br_fiscal.icms_relief_%s" % (icms.motDesICMS,)
                        ).id
                    if hasattr(icms, "vICMSDeson") and icms.vICMSDeson is not None:
                        icms_vals["icms_relief_value"] = float(icms.vICMSDeson)
                    if (
                        hasattr(icms, "vICMSSubstituto")
                        and icms.vICMSSubstituto is not None
                    ):
                        icms_vals["icms_substitute"] = float(icms.vICMSSubstituto)

                    # ICMS ST fields
                    # TODO map icmsst_tax_id
                    if hasattr(icms, "modBCST") and icms.modBCST is not None:
                        icms_vals["icmsst_base_type"] = float(icms.modBCST)
                    if hasattr(icms, "pMVAST") and icms.pMVAST is not None:
                        icms_vals["icmsst_mva_percent"] = float(icms.pMVAST)
                    if hasattr(icms, "pRedBCST") and icms.pRedBCST is not None:
                        icms_vals["icmsst_reduction"] = float(icms.pRedBCST)
                    if hasattr(icms, "vBCST") and icms.vBCST is not None:
                        icms_vals["icmsst_base"] = float(icms.vBCST)
                    if hasattr(icms, "pICMSST") and icms.pICMSST is not None:
                        icms_vals["icmsst_percent"] = float(icms.pICMSST)
                    if hasattr(icms, "vICMSST") and icms.vICMSST is not None:
                        icms_vals["icmsst_value"] = float(icms.vICMSST)
                    if hasattr(icms, "vBCSTRet") and icms.vBCSTRet is not None:
                        icms_vals["icmsst_wh_base"] = float(icms.vBCSTRet)
                    if hasattr(icms, "vICMSSTRet") and icms.vICMSSTRet is not None:
                        icms_vals["icmsst_wh_value"] = float(icms.vICMSSTRet)

                    # ICMS FCP Fields
                    # TODO map icmsfcp_tax_id
                    if hasattr(icms, "pFCPUFDest") and icms.pFCPUFDest is not None:
                        icms_vals["icmsfcp_percent"] = float(icms.pFCPUFDest)
                    if hasattr(icms, "vFCPUFDest") and icms.vFCPUFDest is not None:
                        icms_vals["icmsfcp_value"] = float(icms.vFCPUFDest)
                    if hasattr(icms, "vBCFCPST") and icms.vBCFCPST is not None:
                        icms_vals["icmsfcp_base"] = float(icms.vBCFCPST)

                    # ICMS DIFAL Fields
                    if hasattr(icms, "vBCUFDest") and icms.vBCUFDest is not None:
                        icms_vals["icms_destination_base"] = float(icms.vBCUFDest)
                    if hasattr(icms, "pICMSUFDest") and icms.pICMSUFDest is not None:
                        icms_vals["icms_origin_percent"] = float(icms.pICMSUFDest)
                    if hasattr(icms, "pICMSInter") and icms.pICMSInter is not None:
                        icms_vals["icms_destination_percent"] = float(icms.pICMSInter)

                    if (
                        hasattr(icms, "pICMSInterPart")
                        and icms.pICMSInterPart is not None
                    ):
                        icms_vals["icms_sharing_percent"] = float(icms.pICMSInterPart)
                    if hasattr(icms, "vICMSUFRemet") and icms.vICMSUFRemet is not None:
                        icms_vals["icms_origin_value"] = float(icms.vICMSUFRemet)
                    if hasattr(icms, "vICMSUFDest"):
                        icms_vals["icms_destination_value"] = float(icms.vICMSUFDest)

                    # ICMS Simples Nacional Fields
                    # TODO map icmssn_tax_id using CSOSN
                    if hasattr(icms, "CSOSN") and icms.CSOSN is not None:
                        icms_vals["icms_cst_id"] = self.env.ref(
                            "l10n_br_fiscal.cst_icmssn_%s" % (icms.CSOSN,)
                        ).id
                    if hasattr(icms, "pCredSN") and icms.pCredSN is not None:
                        icms_vals["icmssn_percent"] = float(icms.pCredSN)
                    if hasattr(icms, "vCredICMSSN") and icms.vCredICMSSN is not None:
                        icms_vals["icmssn_credit_value"] = float(icms.vCredICMSSN)

                    # ICMS Retido Anteriormente
                    if hasattr(icms, "vBCSTRet") and icms.vBCSTRet is not None:
                        icms_vals["icmsst_wh_base"] = float(icms.vBCSTRet)
                    if hasattr(icms, "vICMSSTRet") and icms.vICMSSTRet is not None:
                        icms_vals["icmsst_wh_value"] = float(icms.vICMSSTRet)
                    if hasattr(icms, "vBCFCPSTRet") and icms.vBCFCPSTRet is not None:
                        icms_vals["icmsfcp_base_wh"] = float(icms.vBCFCPSTRet)
                    if hasattr(icms, "vFCPSTRet") and icms.vFCPSTRet is not None:
                        icms_vals["icmsfcp_value_wh"] = float(icms.vFCPSTRet)
                    if hasattr(icms, "vFCPST") and icms.vFCPST is not None:
                        icms_vals["icmsfcpst_value"] = float(icms.vFCPST)
                    if hasattr(icms, "vBCEfet") and icms.vBCEfet is not None:
                        icms_vals["effective_base_value"] = float(icms.vBCEfet)
                    if hasattr(icms, "vICMSEfet") and icms.vICMSEfet is not None:
                        icms_vals["icms_effective_value"] = float(icms.vICMSEfet)
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
            super()._build_many2one(comodel, vals, new_value, key, value, path)

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
