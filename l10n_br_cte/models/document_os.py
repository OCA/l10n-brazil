# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from nfelib.cte.bindings.v4_0.cte_os_v4_00 import CteOs

import re
import sys

from odoo import api, fields

from odoo.addons.l10n_br_fiscal.constants.icms import ICMS_CST, ICMS_SN_CST
from odoo.addons.spec_driven_model.models import spec_models

from ..constants.cte import CTE_CST

CTEOS_ICMS_SELECTION = [
    (f"cteos40_{tag}", tag)
    for tag in ("ICMS00", "ICMS20", "ICMS45", "ICMS90", "ICMSOutraUF", "ICMSSN")
]


def filter_processador_edoc_cte_os(record):
    return (
        record.processador_edoc == "oca" and record.document_type_id.code == "67"
    )


class CTeOS(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document"
    _inherit = [
        "l10n_br_fiscal.document",
        "cteos.40.tcteos_infcte",
    ]
    _spec_schema = "cteos"
    _spec_version = "40"
    _cteos40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0_os.cte_tipos_basico_v4_00"
    )
    _cteos40_stacking_mixin = "cteos.40.tcteos_infcte"
    _cteos40_stacking_skip_paths = (
        "cteos40_semData",
        "cteos40_noPeriodo",
        "cteos40_comHora",
        "cteos40_noInter",
    )
    # all m2o at this level will be stacked even if not required:
    _cteos40_stacking_force_paths = ("infcte.compl",)

    # --- ide block: mostly related to business fields (mirrors the CT-e stack) ---
    cteos40_versao = fields.Char(related="document_version")
    cteos40_mod = fields.Char(related="document_type_id.code", string="cteos40_mod")
    cteos40_serie = fields.Char(related="document_serie")
    cteos40_nCT = fields.Char(related="document_number")
    cteos40_dhEmi = fields.Datetime(related="document_date")
    cteos40_natOp = fields.Char(related="operation_name")
    cteos40_tpAmb = fields.Selection(related="cte_environment")
    cteos40_modal = fields.Selection(related="transport_modal")

    # --- emit / toma linkage to concrete company / partner ---
    cteos40_emit = fields.Many2one(
        comodel_name="res.company", compute="_compute_cteos40_emit"
    )
    cteos40_toma = fields.Many2one(
        comodel_name="res.partner", compute="_compute_cteos40_toma"
    )

    @api.depends("company_id")
    def _compute_cteos40_emit(self):
        for doc in self:
            doc.cteos40_emit = (
                doc.company_id if filter_processador_edoc_cte_os(doc) else False
            )

    @api.depends("partner_id")
    def _compute_cteos40_toma(self):
        for doc in self:
            doc.cteos40_toma = (
                doc.partner_id if filter_processador_edoc_cte_os(doc) else False
            )

    cteos40_cUF = fields.Char(
        related="company_id.partner_id.state_id.ibge_code"
    )
    cteos40_cCT = fields.Char(compute="_compute_cteos40_cct")
    cteos40_xDescServ = fields.Char(related="operation_name")

    def _compute_cteos40_cct(self):
        for record in self.filtered(filter_processador_edoc_cte_os):
            record.cteos40_cCT = (
                record.document_key[35:43] if record.document_key else False
            )

    # --- vPrest block ---
    cteos40_vTPrest = fields.Monetary(related="fiscal_amount_total")
    cteos40_vRec = fields.Monetary(related="amount_price_gross")

    # --- infCte@Id (access key prefixed with "CTeOS") ---
    cteos40_Id = fields.Char(
        compute="_compute_cteos40_id",
        inverse="_inverse_cteos40_id",
    )

    @api.depends("document_type_id", "document_key")
    def _compute_cteos40_id(self):
        for record in self.filtered(filter_processador_edoc_cte_os):
            record.cteos40_Id = (
                f"CTeOS{record.document_key}" if record.document_key else False
            )

    def _inverse_cteos40_id(self):
        for record in self.filtered(filter_processador_edoc_cte_os):
            if record.cteos40_Id:
                record.document_key = re.findall(r"\d+", str(record.cteos40_Id))[0]

    # --- ICMS block (mirrors the CT-e ICMS mapping for the OS layout) ---
    cteos40_choice_icms = fields.Selection(
        selection=CTEOS_ICMS_SELECTION,
        string="Tipo de ICMS (OS)",
        compute="_compute_cteos40_choice_icms",
        store=True,
    )
    cteos40_CST = fields.Selection(
        selection=CTE_CST,
        string="Classificação Tributária do Serviço (OS)",
        compute="_compute_cteos40_choice_icms",
        store=True,
    )
    cteos40_indSN = fields.Float(default=1)

    @api.depends("fiscal_line_ids", "fiscal_line_ids.icms_cst_id")
    def _compute_cteos40_choice_icms(self):
        for record in self.filtered(filter_processador_edoc_cte_os):
            record.cteos40_choice_icms = None
            record.cteos40_CST = None
            if not record.fiscal_line_ids:
                continue
            cst = record.fiscal_line_ids[0].icms_cst_id.code
            if cst in ICMS_CST:
                if cst in ["40", "41", "50"]:
                    record.cteos40_choice_icms = "cteos40_ICMS45"
                    record.cteos40_CST = "45"
                elif (
                    cst == "90"
                    and record.partner_id.state_id != record.company_id.state_id
                ):
                    record.cteos40_choice_icms = "cteos40_ICMSOutraUF"
                else:
                    record.cteos40_choice_icms = f"cteos40_ICMS{cst}"
                    record.cteos40_CST = cst
            elif cst in ICMS_SN_CST:
                record.cteos40_choice_icms = "cteos40_ICMSSN"
                record.cteos40_CST = "90"

    def _export_fields_cteos40_icms(self):
        if not self.fiscal_line_ids:
            return {}
        first_line = self.fiscal_line_ids[0]
        icms = {
            "CST": self.cteos40_CST,
            "vBC": 0.0,
            "pRedBC": first_line.icms_reduction,
            "pICMS": first_line.icms_percent,
            "vICMS": 0.0,
            "indSN": int(self.cteos40_indSN),
        }
        for line in self.fiscal_line_ids:
            icms["vBC"] += line.icms_base
            icms["vICMS"] += line.icms_value
        icms["vBC"] = f"{icms['vBC']:.02f}"
        icms["vICMS"] = f"{icms['vICMS']:.02f}"
        icms["pRedBC"] = f"{icms['pRedBC']:.04f}"
        icms["pICMS"] = f"{icms['pICMS']:.02f}"
        return icms

    def _export_fields_cteos_40_timpos(self, xsd_fields, class_obj, export_dict):
        for record in self.filtered(filter_processador_edoc_cte_os):
            if not record.cteos40_choice_icms:
                continue
            if "cteos40_ICMSOutraUF" in xsd_fields:
                xsd_fields.remove("cteos40_ICMSOutraUF")
            icms_tag = (
                record.cteos40_choice_icms.replace("cteos40_", "")
                .replace("ICMSSN", "Icmssn")
                .replace("ICMS", "Icms")
            )
            binding_module = sys.modules[record._get_spec_property("binding_module")]
            icms_binding = getattr(binding_module.TimpOs, icms_tag)
            icms_dict = record._export_fields_cteos40_icms()
            sliced_icms_dict = {
                key: icms_dict.get(key)
                for key in icms_binding.__dataclass_fields__.keys()
                if icms_dict.get(key)
            }
            export_dict[icms_tag.upper()] = icms_binding(**sliced_icms_dict)

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_processador_edoc_cte_os):
            inf_cte = record._build_binding("cteos", "40")
            cte_os = CteOs(
                infCte=inf_cte,
                infCTeSupl=None,
                signature=None,
                versao=record.document_version or "4.00",
            )
            edocs.append(cte_os)
        return edocs
