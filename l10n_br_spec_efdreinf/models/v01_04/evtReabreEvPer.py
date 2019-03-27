# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 03:42:51 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class Reinf(spec_models.AbstractSpecMixin):
    _description = 'reinf'
    _name = 'efdreinf.01.reinf'
    _generateds_type = 'Reinf'
    _concrete_rec_name = 'efdreinf_evtReabreEvPer'

    efdreinf01_evtReabreEvPer = fields.Many2one(
        "efdreinf.01.evtreabreevper",
        string="evtReabreEvPer",
        xsd_required=True)


class EvtReabreEvPer(spec_models.AbstractSpecMixin):
    "Evento de reabertura de eventos periódicosIdentificador do Evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.evtreabreevper'
    _generateds_type = 'evtReabreEvPerType'
    _concrete_rec_name = 'efdreinf_id'

    efdreinf01_id = fields.Char(
        string="id", xsd_required=True)
    efdreinf01_ideEvento = fields.Many2one(
        "efdreinf.01.ideevento",
        string="Informações de identificação do evento",
        xsd_required=True)
    efdreinf01_ideContri = fields.Many2one(
        "efdreinf.01.idecontri",
        string="ideContri", xsd_required=True)


class IdeContri(spec_models.AbstractSpecMixin):
    _description = 'idecontri'
    _name = 'efdreinf.01.idecontri'
    _generateds_type = 'ideContriType'
    _concrete_rec_name = 'efdreinf_tpInsc'

    efdreinf01_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True,
        help="Número de inscrição do contribuinte de acordo com o tipo de"
        "\ninscrição indicado.")


class IdeEvento(spec_models.AbstractSpecMixin):
    "Informações de identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'efdreinf_perApur'

    efdreinf01_perApur = fields.Char(
        string="perApur", xsd_required=True)
    efdreinf01_tpAmb = fields.Integer(
        string="tpAmb", xsd_required=True)
    efdreinf01_procEmi = fields.Integer(
        string="procEmi", xsd_required=True)
    efdreinf01_verProc = fields.Char(
        string="verProc", xsd_required=True)
