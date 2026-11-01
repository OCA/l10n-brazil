# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Mapped from evtBalancete-v1_0_1.xsd (DeRE layout 1.2.0 / D-1101)

from odoo import fields, models

from .types import APLIC_EMI, MOT_EXCL, NAT_SALDO, TP_AMB, TP_OPER


class Dere12EvtBalancete(models.AbstractModel):
    _name = "dere.12.evtbalancete"
    _description = "D-1101 monthly trial balance"
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


class Dere12BalanceteConta(models.AbstractModel):
    _name = "dere.12.balanceteconta"
    _description = "D-1101 trial-balance account"
    _inherit = ["spec.mixin.dere", "spec.mixin.dere.currency"]

    dere12_cCta = fields.Char(
        string="Analytic account code", size=53, xsd_required=True
    )
    dere12_natSaldoInic = fields.Selection(
        NAT_SALDO, string="Opening balance nature", xsd_required=True
    )
    dere12_vSaldoInic = fields.Monetary(
        string="Opening balance", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vMovDebt = fields.Monetary(
        string="Debit movement", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vAjusteDebt = fields.Monetary(
        string="Debit adjustment", currency_field="brl_currency_id"
    )
    dere12_vMovCred = fields.Monetary(
        string="Credit movement", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vAjusteCred = fields.Monetary(
        string="Credit adjustment", currency_field="brl_currency_id"
    )
    dere12_natSaldoFinal = fields.Selection(
        NAT_SALDO, string="Closing balance nature", xsd_required=True
    )
    dere12_vSaldoFinal = fields.Monetary(
        string="Closing balance", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_natVApur = fields.Selection(NAT_SALDO, string="Assessment nature")
    dere12_vApur = fields.Monetary(
        string="Taxable amount", currency_field="brl_currency_id", xsd_required=True
    )
