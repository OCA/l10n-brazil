# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Mapped from evtInfoContrib-v1_0_1.xsd (DeRE layout 1.2.0 / D-1001)

from odoo import fields, models

from .types import (
    APLIC_EMI,
    IND_NAT_TRIB,
    MOT_EXCL,
    REG_TRIB_PRINC,
    TP_AMB,
    TP_OPER,
)


class Dere12EvtInfoContrib(models.AbstractModel):
    _name = "dere.12.evtinfocontrib"
    _description = "D-1001 taxpayer information"
    _inherit = "spec.mixin.dere"

    dere12_id = fields.Char(
        string="Event id", size=42, xsd_required=True, xsd_type="ID42"
    )
    dere12_tpOper = fields.Selection(
        TP_OPER, string="Operation type", xsd_required=True
    )
    dere12_motExcl = fields.Selection(MOT_EXCL, string="Exclusion reason")
    dere12_nrProc = fields.Char(string="Lawsuit / process number", size=21)
    dere12_tpAmb = fields.Selection(TP_AMB, string="Environment", xsd_required=True)
    dere12_aplicEmi = fields.Selection(
        APLIC_EMI, string="Issuer application", xsd_required=True
    )
    dere12_verAplic = fields.Char(
        string="Application version", size=20, xsd_required=True
    )
    dere12_nrInsc = fields.Char(string="CNPJ root", size=8, xsd_required=True)
    dere12_iniValid = fields.Date(string="Validity start", xsd_required=True)
    dere12_fimValid = fields.Date(string="Validity end")
    dere12_novaIniValid = fields.Date(string="New validity start")
    dere12_novaFimValid = fields.Date(string="New validity end")
    dere12_regTribPrinc = fields.Selection(
        REG_TRIB_PRINC, string="Main tax regime", xsd_required=True
    )
    dere12_regTribSecund = fields.Char(
        string="Secondary tax regimes",
        help="Up to three values from 1, 2 or 3, comma-separated.",
    )
    dere12_indNatTrib = fields.Selection(
        IND_NAT_TRIB, string="Tax nature", xsd_required=True
    )
    dere12_tpAtividadeFinanc = fields.Char(
        string="Financial activity codes",
        help="Table 21 codes (NNC), comma-separated.",
    )
    dere12_tpAtividadeSaude = fields.Char(
        string="Health-plan activity codes",
        help="Table 31 codes (NNC), comma-separated.",
    )
    dere12_tpAtividadeProg = fields.Char(
        string="Prize-contest activity codes",
        help="Table 41 codes (NNC), comma-separated.",
    )
    dere12_UFCredenc = fields.Char(
        string="Licensed UFs",
        help="Table 13 UF codes, comma-separated.",
    )
