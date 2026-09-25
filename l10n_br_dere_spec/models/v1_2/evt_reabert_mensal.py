# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Mapped from evtReabertMensal-v0_0_1.xsd (DeRE layout 1.2.0 / D-1198)

from odoo import fields, models

from .types import APLIC_EMI, TP_AMB, TP_OPER_CLOSE


class Dere12EvtReabertMensal(models.AbstractModel):
    _name = "dere.12.evtreabertmensal"
    _description = "D-1198 period reopening"
    _inherit = "spec.mixin.dere"

    dere12_id = fields.Char(
        string="Event id", size=42, xsd_required=True, xsd_type="ID42"
    )
    dere12_tpOper = fields.Selection(
        TP_OPER_CLOSE, string="Operation type", xsd_required=True
    )
    dere12_tpAmb = fields.Selection(TP_AMB, string="Environment", xsd_required=True)
    dere12_aplicEmi = fields.Selection(
        APLIC_EMI, string="Issuer application", xsd_required=True
    )
    dere12_verAplic = fields.Char(
        string="Application version", size=20, xsd_required=True
    )
    dere12_nrInsc = fields.Char(string="CNPJ root", size=8, xsd_required=True)
    dere12_perApur = fields.Char(string="Assessment period", size=7, xsd_required=True)
    dere12_nrReciboReab = fields.Char(
        string="Closing receipt", size=31, xsd_required=True
    )
