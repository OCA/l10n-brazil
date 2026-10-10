# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Mapped from evtRetornoTabela-v1_0_1.xsd (D-9001), evtRetornoBalan-v1_0_0.xsd
# (D-9101), evtRetornoAplicFin-v1_0_0.xsd (D-9106) and
# evtRetornoMensal-v0_0_2.xsd (D-9199).

from odoo import fields, models

from .types import CD_RETORNO, IND_AJUSTE_AUTO, IND_TRIB_ISS, TIPO_OCORRENCIA

PERCENT_DIGITS = (9, 6)


class Dere12EvtRetornoTabela(models.AbstractModel):
    _name = "dere.12.evtretornostabela"
    _description = "D-9001 table-event return"
    _inherit = "spec.mixin.dere"

    dere12_nrInsc = fields.Char(string="CNPJ root", size=8, xsd_required=True)
    dere12_cdRetorno = fields.Selection(
        CD_RETORNO, string="Return code", xsd_required=True
    )
    dere12_descRetorno = fields.Char(
        string="Return description", size=7, xsd_required=True
    )
    dere12_nrRecibo = fields.Char(string="Event receipt", size=31)
    dere12_seqEvento = fields.Char(string="Event version sequence", size=2)
    dere12_protocoloLote = fields.Char(string="Batch protocol", size=28)
    dere12_dhRecepcao = fields.Datetime(string="Reception datetime")
    dere12_dhProcess = fields.Datetime(string="Processing datetime")
    dere12_tpEv = fields.Char(string="Event type", size=6)
    dere12_hash = fields.Char(string="File hash", size=44)


class Dere12Ocorrencia(models.AbstractModel):
    _name = "dere.12.ocorrencia"
    _description = "DeRE return occurrence"
    _inherit = "spec.mixin.dere"

    dere12_codigo = fields.Char(string="Occurrence code", size=6, xsd_required=True)
    dere12_descricao = fields.Char(
        string="Occurrence description", size=2048, xsd_required=True
    )
    dere12_tipo = fields.Selection(
        TIPO_OCORRENCIA, string="Occurrence type", xsd_required=True
    )
    dere12_localizacao = fields.Char(string="Field location", size=2048)


class Dere12DetEvento(models.AbstractModel):
    _name = "dere.12.detevento"
    _description = "D-9001 active validity of a table event"
    _inherit = "spec.mixin.dere"

    dere12_nrRecibo = fields.Char(string="Event receipt", size=31, xsd_required=True)
    dere12_iniValid = fields.Date(string="Validity start", xsd_required=True)
    dere12_fimValid = fields.Date(string="Validity end")
    dere12_fimValidEfetiva = fields.Date(string="Effective validity end")
    dere12_indAjusteAuto = fields.Selection(IND_AJUSTE_AUTO, string="Automatic cut")


class Dere12DetLacuna(models.AbstractModel):
    _name = "dere.12.detlacuna"
    _description = "D-9001 period without table coverage"
    _inherit = "spec.mixin.dere"

    dere12_iniLacuna = fields.Date(string="Gap start", xsd_required=True)
    dere12_fimLacuna = fields.Date(string="Gap end")


class Dere12GTotalCodTrib(models.AbstractModel):
    _name = "dere.12.gtotalcodtrib"
    _description = "D-9101 / D-9106 assessed total"
    _inherit = ["spec.mixin.dere", "spec.mixin.dere.currency"]

    dere12_codTrib = fields.Char(string="Taxation code", size=9)
    dere12_indTribISS = fields.Selection(IND_TRIB_ISS, string="ISS indicator")
    dere12_vApurTot = fields.Monetary(
        string="Assessed total", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vTotSaldoInic = fields.Monetary(
        string="Opening balance total", currency_field="brl_currency_id"
    )
    dere12_vTotSaldoFinal = fields.Monetary(
        string="Closing balance total", currency_field="brl_currency_id"
    )


class Dere12DetBC(models.AbstractModel):
    """D-9199 assessed tax base.

    The XSD repeats ``vDedBCN`` in gBCIBS and gBCCBS and ``vSaldoFinal`` in
    gBCNIBS and gBCNCBS, so those fields carry an IBS/CBS suffix here.
    """

    _name = "dere.12.detbc"
    _description = "D-9199 assessed tax base"
    _inherit = ["spec.mixin.dere", "spec.mixin.dere.currency"]

    dere12_codBC = fields.Char(string="Tax base code", size=4, xsd_required=True)
    dere12_xDetBC = fields.Char(
        string="Tax base description", size=1024, xsd_required=True
    )
    dere12_memoriaCalculo = fields.Text(string="Calculation memory", xsd_required=True)
    dere12_vBCIBS = fields.Monetary(
        string="IBS base", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vBCNIBS = fields.Monetary(
        string="IBS negative base", currency_field="brl_currency_id"
    )
    dere12_vDedBCNIBS = fields.Monetary(
        string="IBS negative base used", currency_field="brl_currency_id"
    )
    dere12_vBCApurIBS = fields.Monetary(
        string="IBS assessed base", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_pIBSMun = fields.Float(
        string="Municipal IBS rate", digits=PERCENT_DIGITS, xsd_required=True
    )
    dere12_vIBSMun = fields.Monetary(
        string="Municipal IBS", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_pIBSUF = fields.Float(
        string="State IBS rate", digits=PERCENT_DIGITS, xsd_required=True
    )
    dere12_vIBSUF = fields.Monetary(
        string="State IBS", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_pIBS = fields.Float(
        string="IBS rate", digits=PERCENT_DIGITS, xsd_required=True
    )
    dere12_vIBSTot = fields.Monetary(
        string="Total IBS", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vBCCBS = fields.Monetary(
        string="CBS base", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vBCNCBS = fields.Monetary(
        string="CBS negative base", currency_field="brl_currency_id"
    )
    dere12_vDedBCNCBS = fields.Monetary(
        string="CBS negative base used", currency_field="brl_currency_id"
    )
    dere12_vBCApurCBS = fields.Monetary(
        string="CBS assessed base", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_pCBS = fields.Float(
        string="CBS rate", digits=PERCENT_DIGITS, xsd_required=True
    )
    dere12_vCBS = fields.Monetary(
        string="CBS", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vBCIS = fields.Monetary(string="IS base", currency_field="brl_currency_id")
    dere12_vBCApurIS = fields.Monetary(
        string="IS assessed base", currency_field="brl_currency_id"
    )
    dere12_pIS = fields.Float(string="IS rate", digits=PERCENT_DIGITS)
    dere12_vIS = fields.Monetary(string="IS", currency_field="brl_currency_id")
    dere12_vSaldoFinalBCNIBS = fields.Monetary(
        string="IBS negative base carried forward", currency_field="brl_currency_id"
    )
    dere12_vSaldoFinalBCNCBS = fields.Monetary(
        string="CBS negative base carried forward", currency_field="brl_currency_id"
    )


class Dere12TotalTributos(models.AbstractModel):
    _name = "dere.12.totaltributos"
    _description = "D-9199 tax totals"
    _inherit = ["spec.mixin.dere", "spec.mixin.dere.currency"]

    dere12_vIS = fields.Monetary(string="IS", currency_field="brl_currency_id")
    dere12_vIBSMun = fields.Monetary(
        string="Municipal IBS", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vIBSUF = fields.Monetary(
        string="State IBS", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vIBSTot = fields.Monetary(
        string="Total IBS", currency_field="brl_currency_id", xsd_required=True
    )
    dere12_vCBS = fields.Monetary(
        string="CBS", currency_field="brl_currency_id", xsd_required=True
    )
