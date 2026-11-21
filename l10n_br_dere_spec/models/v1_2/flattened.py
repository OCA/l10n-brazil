# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields, models

PERCENT_DIGITS = (9, 6)


class Dere12DetBC(models.AbstractModel):
    """D-9199 assessed tax base.

    The XSD repeats ``vDedBCN`` in gBCIBS and gBCCBS and ``vSaldoFinal`` in
    gBCNIBS and gBCNCBS. xsdata-odoo 1.2.2 keeps those groups as separate
    models, so this abstract still flattens the row stored by
    ``l10n_br_dere.tax.assessment.line``.
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
    """D-9199 tax totals.

    The generator emits one total class per regime group. This abstract keeps
    the single row of totals used beside the flattened tax base.
    """

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
