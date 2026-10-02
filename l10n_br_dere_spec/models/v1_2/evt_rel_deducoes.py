# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Mapped from evtRelDeducoes-v0_0_1.xsd (DeRE layout 1.2.0 / D-1121)

from odoo import fields, models

from .types import (
    APLIC_EMI,
    FIN_EVT,
    MOT_EXCL,
    TP_AMB,
    TP_ATIV,
    TP_DFE,
    TP_OPER_DEDUCAO,
)


class Dere12EvtRelDeducoes(models.AbstractModel):
    _name = "dere.12.evtreldeducoes"
    _description = "D-1121 deductions"
    _inherit = "spec.mixin.dere"

    dere12_id = fields.Char(
        string="Event id", size=42, xsd_required=True, xsd_type="ID42"
    )
    dere12_tpOper = fields.Selection(
        TP_OPER_DEDUCAO, string="Operation type", xsd_required=True
    )
    dere12_motExcl = fields.Selection(MOT_EXCL, string="Exclusion reason")
    dere12_nrProc = fields.Char(string="Lawsuit / process number", size=21)
    dere12_nrRecibo = fields.Char(string="Previous receipt", size=31)
    dere12_tpAmb = fields.Selection(TP_AMB, string="Environment", xsd_required=True)
    dere12_aplicEmi = fields.Selection(
        APLIC_EMI, string="Issuer application", xsd_required=True
    )
    dere12_verAplic = fields.Char(
        string="Application version", size=20, xsd_required=True
    )
    dere12_nrInsc = fields.Char(string="CNPJ root", size=8, xsd_required=True)
    dere12_perApur = fields.Char(string="Assessment period", size=7, xsd_required=True)
    dere12_finEvt = fields.Selection(FIN_EVT, string="Event purpose")


class Dere12InfoDeducao(models.AbstractModel):
    _name = "dere.12.infodeducao"
    _description = "D-1121 deduction"
    _inherit = ["spec.mixin.dere", "spec.mixin.dere.currency"]

    dere12_tpDFe = fields.Selection(TP_DFE, string="Fiscal document type")
    dere12_chDFe = fields.Char(string="Access key", size=53)
    dere12_dtEmi = fields.Date(string="Issue date", xsd_required=True)
    dere12_chDFeRetif = fields.Char(string="Rectified access key", size=53)
    dere12_tpAtiv = fields.Selection(TP_ATIV, string="Activity type", xsd_required=True)
    dere12_vOper = fields.Monetary(
        string="Operation amount", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vDedTotal = fields.Monetary(
        string="Total deductible", currency_field="brl_currency_id"
    )
    dere12_vDed = fields.Monetary(
        string="Deduction this period",
        currency_field="brl_currency_id",
        xsd_required=True,
    )


class Dere12ItemDFe(models.AbstractModel):
    _name = "dere.12.itemdfe"
    _description = "D-1121 deduction item"
    _inherit = ["spec.mixin.dere", "spec.mixin.dere.currency"]

    dere12_nItem = fields.Char(string="Item number", size=3, xsd_required=True)
    dere12_vItem = fields.Monetary(
        string="Item amount", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vItemDedTotal = fields.Monetary(
        string="Item deductible total", currency_field="brl_currency_id"
    )
    dere12_vItemDed = fields.Monetary(
        string="Item deduction this period",
        currency_field="brl_currency_id",
        xsd_required=True,
    )
