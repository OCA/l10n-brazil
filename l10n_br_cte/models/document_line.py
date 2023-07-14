# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.l10n_br_fiscal.constants.icms import ICMS_CST
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

    cte40_choice11 = fields.Selection(
        selection=[
            ("cte40_ICMS00", "ICMS00"),
            ("cte40_ICMS20", "ICMS20"),
            ("cte40_ICMS40", "ICMS45"),
            ("cte40_ICMS60", "ICMS60"),
            ("cte40_ICMS90", "ICMS90"),
            ("cte40_ICMSOutraUF", "ICMSOutraUF"),
            ("cte40_ICMSSN", "ICMSSN"),
        ],
        string="Tipo de ICMS",
        compute="_compute_choice11",
        store=True,
    )

    cte40_vTotTrib = fields.Monetary(related="estimate_tax")

    cte40_pICMS = fields.Float(related="icms_percent", string="pICMS")

    cte40_vICMS = fields.Monetary(related="amount_icms_value")

    # ICMS20 - ICMS90
    cte40_pRedBC = fields.Float(related="icms_reduction")

    cte40_vBC = fields.Monetary(related="icms_base")

    # ICMS60
    cte40_vBCSTRet = fields.Monetary(related="icmsst_wh_base")

    cte40_vICMSSTRet = fields.Monetary(related="icmsst_wh_value")

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
    def _compute_choice11(self):
        for record in self:
            icms_choice = ""
            if record.icms_cst_id.code in ICMS_CST:
                if record.icms_cst_id.code in ["40", "41", "50"]:
                    icms_choice = "cte40_ICMS45"
                elif (
                    record.icms_cst_id.code == "90"
                    and self.partner_id.state_id != self.company_id.state_id
                ):
                    icms_choice = "cte40_ICMSOutraUF"
                else:
                    icms_choice = "{}{}".format("cte40_ICMS", record.icms_cst_id.code)
            record.cte40_choice11 = icms_choice

    indSN = fields.Selection(
        selection=[
            ("0", "Não é simples nacional"),
            ("1", "É simples nacional"),
        ]
    )

    ##########################
    # CT-e tag: ICMSUFFim
    ##########################

    cte40_vBCUFFim = fields.Monetary(related="icms_destination_base")
    cte40_pFCPUFFim = fields.Monetary(compute="_compute_cte40_ICMSUFFim")
    cte40_pICMSUFFim = fields.Monetary(compute="_compute_cte40_ICMSUFFim")
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
            record.cte40_pICMSUFfim = record.icms_destination_percent

    cte40_vFCPUFfim = fields.Monetary(related="icmsfcp_value")
    cte40_vICMSUFfim = fields.Monetary(related="icms_destination_value")
    cte40_vICMSUFIni = fields.Monetary(related="icms_origin_value")
