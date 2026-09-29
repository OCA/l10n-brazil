# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Mapped from evtPGCC-v1_0_3.xsd (DeRE layout 1.2.0 / D-1011)

from odoo import fields, models

from .types import (
    APLIC_EMI,
    COD_NAT,
    FREQ_ENCERR,
    IND_CTA,
    IND_TRIB_ISS,
    MOT_EXCL,
    NAT_CTA,
    PLANO_CTA_REF,
    TP_AMB,
    TP_OPER,
)


class Dere12EvtPGCC(models.AbstractModel):
    _name = "dere.12.evtpgcc"
    _description = "D-1011 commented chart of accounts"
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
    dere12_planoCtaRef = fields.Selection(
        PLANO_CTA_REF, string="Referential chart", xsd_required=True
    )
    dere12_freqEncerr = fields.Selection(
        FREQ_ENCERR, string="Closing frequency", xsd_required=True
    )


class Dere12InfoConta(models.AbstractModel):
    _name = "dere.12.infoconta"
    _description = "D-1011 chart account"
    _inherit = "spec.mixin.dere"

    dere12_cCta = fields.Char(string="Full account code", size=53, xsd_required=True)
    dere12_cCtaInterna = fields.Char(
        string="Internal account code", size=50, xsd_required=True
    )
    dere12_cDbrMista = fields.Char(
        string="Mixed-account split", size=3, xsd_required=True
    )
    dere12_nomeCta = fields.Char(string="Account name", size=100, xsd_required=True)
    dere12_indCta = fields.Selection(
        IND_CTA, string="Account indicator", xsd_required=True
    )
    dere12_descCta = fields.Char(string="Account description", size=600)
    dere12_cCtaSup = fields.Char(string="Parent account code", size=53)
    dere12_cCtaRef = fields.Char(
        string="Referential account code", size=13, xsd_required=True
    )
    dere12_nivelCta = fields.Integer(string="Hierarchy level", xsd_required=True)
    dere12_natCta = fields.Selection(
        NAT_CTA, string="Account nature", xsd_required=True
    )
    dere12_codNat = fields.Selection(COD_NAT, string="Nature code", xsd_required=True)
    dere12_codTrib = fields.Char(string="Taxation code", size=9)
    dere12_indTribISS = fields.Selection(IND_TRIB_ISS, string="ISS indicator")
    dere12_idLeiDisp = fields.Char(string="Legal destination code", size=5)
    dere12_iniVig = fields.Date(string="Account start", xsd_required=True)
    dere12_fimVig = fields.Date(string="Account end")
