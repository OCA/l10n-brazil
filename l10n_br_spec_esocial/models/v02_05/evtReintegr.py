# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:41 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtreintegr.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtreintegr.tideevetrab'
    _generateds_type = 'TIdeEveTrab'
    _concrete_rec_name = 'esoc_indRetif'

    esoc02_indRetif = fields.Boolean(
        string="indRetif", xsd_required=True)
    esoc02_nrRecibo = fields.Char(
        string="nrRecibo")
    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class TIdeVinculoNisObrig(spec_models.AbstractSpecMixin):
    "Informações do Vínculo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtreintegr.tidevinculonisobrig'
    _generateds_type = 'TIdeVinculoNisObrig'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab", xsd_required=True)
    esoc02_matricula = fields.Char(
        string="matricula", xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtreintegr.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtReintegr'

    esoc02_evtReintegr = fields.Many2one(
        "esoc.02.evtreintegr.evtreintegr",
        string="evtReintegr", xsd_required=True)


class EvtReintegr(spec_models.AbstractSpecMixin):
    _description = 'evtreintegr'
    _name = 'esoc.02.evtreintegr.evtreintegr'
    _generateds_type = 'evtReintegrType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtreintegr.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtreintegr.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideVinculo = fields.Many2one(
        "esoc.02.evtreintegr.tidevinculonisobrig",
        string="Informações de Identificação do Trabalhador e do Vínculo",
        xsd_required=True)
    esoc02_infoReintegr = fields.Many2one(
        "esoc.02.evtreintegr.inforeintegr",
        string="infoReintegr",
        xsd_required=True)


class InfoReintegr(spec_models.AbstractSpecMixin):
    _description = 'inforeintegr'
    _name = 'esoc.02.evtreintegr.inforeintegr'
    _generateds_type = 'infoReintegrType'
    _concrete_rec_name = 'esoc_tpReint'

    esoc02_tpReint = fields.Boolean(
        string="tpReint", xsd_required=True)
    esoc02_nrProcJud = fields.Char(
        string="nrProcJud")
    esoc02_nrLeiAnistia = fields.Char(
        string="nrLeiAnistia")
    esoc02_dtEfetRetorno = fields.Date(
        string="dtEfetRetorno",
        xsd_required=True)
    esoc02_dtEfeito = fields.Date(
        string="dtEfeito", xsd_required=True)
    esoc02_indPagtoJuizo = fields.Char(
        string="indPagtoJuizo",
        xsd_required=True)
