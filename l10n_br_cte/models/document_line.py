# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import sys

from odoo import api, fields

from odoo.addons.l10n_br_fiscal.constants.icms import ICMS_CST, ICMS_SN_CST
from odoo.addons.spec_driven_model.models import spec_models


class CTeLine(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.line"
    _inherit = ["l10n_br_fiscal.document.line", "cte.40.tcte_imp"]
    _stacked = "cte.40.tcte_imp"
    _field_prefix = "cte40_"
    _schema_name = "cte"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_cte"
    _spec_module = "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    _spec_tab_name = "CTe"
    _stacking_points = {}
    _force_stack_paths = "tcte_imp.timp"

    ##########################
    # CT-e tag: vPrest
    ##########################

    cte40_vTPrest = fields.Monetary(string="vTPrest", related="amount_total")

    cte40_vRec = fields.Monetary(
        related="price_gross",
        string="vRec",
    )

    ##################################################
    # CT-e tag: ICMS
    # Grupo N01. Grupo Tributação do ICMS= 00
    # Grupo N02. Grupo Tributação do ICMS= 20
    # Grupo N03. Grupo Tributação do ICMS= 45 (40, 41 e 51)
    # Grupo N04. Grupo Tributação do ICMS= 60
    # Grupo N05. Grupo Tributação do ICMS= 90 - ICMS outros
    # Grupo N06. Grupo Tributação do ICMS= 90 - ICMS Outra UF
    # Grupo N06. Grupo Tributação do ICMS= 01 - ISSN
    #################################################

    cte40_ICMS = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.line", compute="_compute_icms", store=True
    )

    def _compute_icms(self):
        for doc in self:
            doc.cte40_ICMS = doc

    # def _export_fields_cte_40_tcte_imp(self, xsd_fields, class_obj, export_dict):
    #     if self.cte40_choice_icms == "cte40_ICMS00":
    #         xsd_fields.remove("cte40_ICMS20")
    #         xsd_fields.remove("cte40_ICMS45")
    #         xsd_fields.remove("cte40_ICMS60")
    #         xsd_fields.remove("cte40_ICMS90")
    #         xsd_fields.remove("cte40_ICMSOutraUF")
    #         xsd_fields.remove("cte40_ICMSSN")
    #     elif self.cte40_choice_icms == "cte40_ICMS20":
    #         xsd_fields.remove("cte40_ICMS00")
    #         xsd_fields.remove("cte40_ICMS45")
    #         xsd_fields.remove("cte40_ICMS60")
    #         xsd_fields.remove("cte40_ICMS90")
    #         xsd_fields.remove("cte40_ICMSOutraUF")
    #         xsd_fields.remove("cte40_ICMSSN")
    #     elif self.cte40_choice_icms == "cte40_ICMS45":
    #         xsd_fields.remove("cte40_ICMS00")
    #         xsd_fields.remove("cte40_ICMS20")
    #         xsd_fields.remove("cte40_ICMS60")
    #         xsd_fields.remove("cte40_ICMS90")
    #         xsd_fields.remove("cte40_ICMSOutraUF")
    #         xsd_fields.remove("cte40_ICMSSN")
    #     elif self.cte40_choice_icms == "cte40_ICMS60":
    #         xsd_fields.remove("cte40_ICMS00")
    #         xsd_fields.remove("cte40_ICMS20")
    #         xsd_fields.remove("cte40_ICMS45")
    #         xsd_fields.remove("cte40_ICMS90")
    #         xsd_fields.remove("cte40_ICMSOutraUF")
    #         xsd_fields.remove("cte40_ICMSSN")
    #     elif self.cte40_choice_icms == "cte40_ICMS90":
    #         xsd_fields.remove("cte40_ICMS00")
    #         xsd_fields.remove("cte40_ICMS20")
    #         xsd_fields.remove("cte40_ICMS45")
    #         xsd_fields.remove("cte40_ICMS60")
    #         xsd_fields.remove("cte40_ICMSOutraUF")
    #         xsd_fields.remove("cte40_ICMSSN")
    #     elif self.cte40_choice_icms == "cte40_ICMSOutraUF":
    #         xsd_fields.remove("cte40_ICMS00")
    #         xsd_fields.remove("cte40_ICMS20")
    #         xsd_fields.remove("cte40_ICMS45")
    #         xsd_fields.remove("cte40_ICMS60")
    #         xsd_fields.remove("cte40_ICM90")
    #         xsd_fields.remove("cte40_ICMSSN")
    #     elif self.cte40_choice_icms == "cte40_ICMSSN":
    #         xsd_fields.remove("cte40_ICMS00")
    #         xsd_fields.remove("cte40_ICMS20")
    #         xsd_fields.remove("cte40_ICMS45")
    #         xsd_fields.remove("cte40_ICMS60")
    #         xsd_fields.remove("cte40_ICMS90")
    #         xsd_fields.remove("cte40_ICMSOutraUF")

    cte40_choice_icms = fields.Selection(
        selection=[
            ("cte40_ICMS00", "ICMS00"),
            ("cte40_ICMS20", "ICMS20"),
            ("cte40_ICMS45", "ICMS45"),
            ("cte40_ICMS60", "ICMS60"),
            ("cte40_ICMS90", "ICMS90"),
            ("cte40_ICMSOutraUF", "ICMSOutraUF"),
            ("cte40_ICMSSN", "ICMSSN"),
        ],
        string="Tipo de ICMS",
        compute="_compute_choice_icms",
        store=True,
    )

    cte40_CST = fields.Selection(
        selection=[
            ("00", "00 - Tributação normal ICMS"),
            ("20", "20 - Tributação com BC reduzida do ICMS"),
            ("45", "45 - ICMS Isento, não Tributado ou diferido"),
            ("60", "60 - ICMS cobrado por substituição tributária"),
            ("90", "90 - ICMS outros"),
            ("90", "90 - ICMS Outra UF"),
            ("01", "01 - Simples Nacional"),
        ],
        string="Classificação Tributária do Serviço",
        compute="_compute_choice_icms",
        store=True,
    )

    cte40_vTotTrib = fields.Monetary(related="estimate_tax")

    cte40_pICMS = fields.Float(related="icms_percent", string="pICMS")

    cte40_vICMS = fields.Monetary(related="icms_value")

    # ICMS20 - ICMS90
    cte40_pRedBC = fields.Float(
        related="icms_reduction",
    )

    cte40_vBC = fields.Monetary(related="icms_base")

    # ICMS60
    cte40_vBCSTRet = fields.Monetary(related="icmsst_wh_base")

    cte40_vICMSSTRet = fields.Monetary(related="icmsst_wh_value")

    # TODO cte40_pICMSTRet = fields.Monetary(related="")

    # ICMSSN
    cte40_indSN = fields.Selection(related="indSN")

    # ICMS NF
    cte40_vBCST = fields.Monetary(related="icmsst_base")

    # ICMSOutraUF
    # TODO

    ##########################
    # CT-e tag: ICMS
    # Compute Methods
    ##########################

    @api.depends("icms_cst_id")
    def _compute_choice_icms(self):
        for record in self:
            record.cte40_choice_icms = None
            record.cte40_CST = None
            if record.icms_cst_id.code in ICMS_CST:
                if record.icms_cst_id.code in ["40", "41", "50"]:
                    record.cte40_choice_icms = "cte40_ICMS45"
                elif (
                    record.icms_cst_id.code == "90"
                    and self.partner_id.state_id != self.company_id.state_id
                ):
                    record.cte40_choice_icms = "cte40_ICMSOutraUF"
                else:
                    record.cte40_choice_icms = "{}{}".format(
                        "cte40_ICMS", record.icms_cst_id.code
                    )
            elif record.icms_cst_id.code in ICMS_SN_CST:
                record.cte40_choice_icms = "cte40_ICMSSN"
                record.cte40_CST = "01"
            if record.cte40_CST != "01":
                record.cte40_CST = record.icms_cst_id.code

    indSN = fields.Selection(
        selection=[
            ("0", "Não é simples nacional"),
            ("1", "É simples nacional"),
        ],
        default="0",
    )

    def _export_fields_icms(self):
        icms = {
            "CST": self.icms_cst_id.code,
            "vBC": str("%.02f" % self.icms_base),
            "pRedBC": str("%.04f" % self.icms_reduction),
            "pICMS": str("%.04f" % self.icms_percent),
            "vICMS": str("%.02f" % self.icms_value),
            "vICMSSubstituto": str("%.02f" % self.icms_substitute),
            "indSN": self.cte40_indSN,
            "vBCSTRet": str("%.02f" % self.icmsst_wh_base),
            "vICMSSTRet": str("%.02f" % self.icmsst_wh_value),
        }
        return icms

    def _export_fields_cte_40_timp(self, xsd_fields, class_obj, export_dict):
        # TODO Not Implemented
        if "cte40_ICMSOutraUF" in xsd_fields:
            xsd_fields.remove("cte40_ICMSOutraUF")

        xsd_fields = [self.cte40_choice_icms]
        icms_tag = self.cte40_choice_icms.replace("cte40_", "").replace(
            "ICMSSN", "Icmssn"
        )
        binding_module = sys.modules[self._binding_module]
        icms = binding_module.Timp
        icms_binding = getattr(icms, icms_tag)
        icms_dict = self._export_fields_icms()
        sliced_icms_dict = {
            key: icms_dict.get(key)
            for key in icms_binding.__dataclass_fields__.keys()
            if icms_dict.get(key)
        }
        export_dict[icms_tag.upper()] = icms_binding(**sliced_icms_dict)

    ##########################
    # CT-e tag: ICMSUFFim
    ##########################

    cte40_vBCUFFim = fields.Monetary(related="icms_destination_base")
    cte40_pFCPUFFim = fields.Monetary(compute="_compute_cte40_ICMSUFFim", store=True)
    cte40_pICMSUFFim = fields.Monetary(compute="_compute_cte40_ICMSUFFim", store=True)
    # cte40_pICMSInter = fields.Selection(
    #    selection=[("0", "Teste")],
    #    compute="_compute_cte40_ICMSUFFim")

    def _compute_cte40_ICMSUFFim(self):
        for record in self:
            #    if record.icms_origin_percent:
            #        record.cte40_pICMSInter = str("%.02f" % record.icms_origin_percent)
            #    else:
            #        record.cte40_pICMSInter = False

            record.cte40_pFCPUFFim = record.icmsfcp_percent
            record.cte40_pICMSUFFim = record.icms_destination_percent

    cte40_vFCPUFfim = fields.Monetary(related="icmsfcp_value")
    cte40_vICMSUFFim = fields.Monetary(related="icms_destination_value")
    cte40_vICMSUFIni = fields.Monetary(related="icms_origin_value")

    ##########################
    # CT-e tag: natCarga
    ##########################

    cte40_xDime = fields.Char(compute="_compute_dime", store=True)

    def _compute_dime(self):
        for record in self:
            for package in record.product_id.packaging_ids:
                record.cte40_xDime = (
                    package.width + "X" + package.packaging_length + "X" + package.width
                )
