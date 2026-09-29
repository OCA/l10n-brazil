# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Mapped from evtFechMensal-v0_0_2.xsd (DeRE layout 1.2.0 / D-1199)

from odoo import fields, models

from .types import APLIC_EMI, METODO_APROVEIT, TP_AMB, TP_OPER_CLOSE, USAR_BCN


class Dere12EvtFechMensal(models.AbstractModel):
    _name = "dere.12.evtfechmensal"
    _description = "D-1199 monthly closing"
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
    dere12_indInexistDedu = fields.Selection(
        [("1", "No deductions to report in this period")],
        string="No deductions indicator",
    )


class Dere12InfoBCN(models.AbstractModel):
    _name = "dere.12.infobcn"
    _description = "D-1199 negative tax base"
    _inherit = ["spec.mixin.dere", "spec.mixin.dere.currency"]

    dere12_codBCNRaiz = fields.Char(
        string="Negative base code", size=5, xsd_required=True
    )
    dere12_usarBCNAcum = fields.Selection(
        USAR_BCN, string="Use accumulated base", xsd_required=True
    )
    dere12_metodoAproveit = fields.Selection(METODO_APROVEIT, string="Recovery method")
    dere12_codBCN = fields.Char(string="Detailed negative base code", size=13)
    dere12_vUsarBCN = fields.Monetary(
        string="Amount to recover", currency_field="brl_currency_id"
    )
