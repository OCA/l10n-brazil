# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:40 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtreabreev.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtreabreev.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtReabreEvPer'

    esoc02_evtReabreEvPer = fields.Many2one(
        "esoc.02.evtreabreev.evtreabreevper",
        string="evtReabreEvPer",
        xsd_required=True)


class EvtReabreEvPer(spec_models.AbstractSpecMixin):
    "Evento de reabertura de eventos periódicos - remuneração"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtreabreev.evtreabreevper'
    _generateds_type = 'evtReabreEvPerType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtreabreev.ideevento",
        string="Informações de identificação do evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtreabreev.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)


class IdeEvento(spec_models.AbstractSpecMixin):
    "Informações de identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtreabreev.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'esoc_indApuracao'

    esoc02_indApuracao = fields.Boolean(
        string="indApuracao", xsd_required=True)
    esoc02_perApur = fields.Char(
        string="perApur", xsd_required=True)
    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)
