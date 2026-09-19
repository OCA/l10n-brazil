# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Mapped from evtAplicResTec-v1_0_0.xsd (DeRE layout 1.2.0 / D-1106)

from odoo import fields, models

from .types import APLIC_EMI, MOT_EXCL, SEM_APLIC, TP_AMB, TP_OPER


class Dere12EvtAplicResTec(models.AbstractModel):
    _name = "dere.12.evtaplicrestec"
    _description = "D-1106 technical-reserve investments"
    _inherit = "spec.mixin.dere"

    dere12_id = fields.Char(
        string="Event id", size=42, xsd_required=True, xsd_type="ID42"
    )
    dere12_tpOper = fields.Selection(
        TP_OPER, string="Operation type", xsd_required=True
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
    dere12_semAplic = fields.Selection(SEM_APLIC, string="No investments indicator")


class Dere12DetAtivo(models.AbstractModel):
    _name = "dere.12.detativo"
    _description = "D-1106 technical-reserve asset"
    _inherit = ["spec.mixin.dere", "spec.mixin.dere.currency"]

    dere12_idAtivo = fields.Char(string="Asset id", size=30, xsd_required=True)
    dere12_descAtivo = fields.Char(
        string="Asset description", size=255, xsd_required=True
    )
    dere12_vSaldoInic = fields.Monetary(
        string="Opening balance", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vRendPerReceb = fields.Monetary(
        string="Period income received", currency_field="brl_currency_id"
    )
    dere12_vVarMensal = fields.Monetary(
        string="Monthly variation", currency_field="brl_currency_id"
    )
    dere12_vPrincLiqResg = fields.Monetary(
        string="Principal redeemed", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vRendLiqResg = fields.Monetary(
        string="Income on redemption", currency_field="brl_currency_id"
    )
    dere12_vSaldoFinal = fields.Monetary(
        string="Closing balance", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vApur = fields.Monetary(
        string="Taxable amount", currency_field="brl_currency_id", xsd_required=True
    )
