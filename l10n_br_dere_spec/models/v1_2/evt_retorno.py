# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Mapped from evtRetornoTabela-v1_0_1.xsd and related return events.

from odoo import fields, models

from .types import CD_RETORNO, TIPO_OCORRENCIA


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
