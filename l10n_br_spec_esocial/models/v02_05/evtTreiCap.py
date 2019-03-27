# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:53 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evttreicapl.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttreicapl.tideevetrab'
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


class TIdeVinculoEstag(spec_models.AbstractSpecMixin):
    "Informacoes do Vínculo trabalhista e estagiário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttreicapl.tidevinculoestag'
    _generateds_type = 'TIdeVinculoEstag'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab")
    esoc02_matricula = fields.Char(
        string="matricula")
    esoc02_codCateg = fields.Integer(
        string="codCateg")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttreicapl.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtTreiCap'

    esoc02_evtTreiCap = fields.Many2one(
        "esoc.02.evttreicapl.evttreicap",
        string="evtTreiCap", xsd_required=True)


class EvtTreiCap(spec_models.AbstractSpecMixin):
    """Evento Treinamentos, Capacitações, Exercícios Simulados e Outras
    Anotações"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttreicapl.evttreicap'
    _generateds_type = 'evtTreiCapType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttreicapl.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttreicapl.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideVinculo = fields.Many2one(
        "esoc.02.evttreicapl.tidevinculoestag",
        string="Informações de Identificação do Trabalhador e do Vínculo",
        xsd_required=True)
    esoc02_treiCap = fields.Many2one(
        "esoc.02.evttreicapl.treicap",
        string="Treinamentos", xsd_required=True,
        help="Treinamentos, capacitações e exercícios simulados")


class IdeProfResp(spec_models.AbstractSpecMixin):
    "Informações relativas ao profissional responsável"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttreicapl.ideprofresp'
    _generateds_type = 'ideProfRespType'
    _concrete_rec_name = 'esoc_cpfProf'

    esoc02_ideProfResp_infoComplem_id = fields.Many2one(
        "esoc.02.evttreicapl.infocomplem")
    esoc02_cpfProf = fields.Char(
        string="cpfProf")
    esoc02_nmProf = fields.Char(
        string="nmProf", xsd_required=True)
    esoc02_tpProf = fields.Boolean(
        string="tpProf", xsd_required=True)
    esoc02_formProf = fields.Char(
        string="formProf", xsd_required=True)
    esoc02_codCBO = fields.Char(
        string="codCBO", xsd_required=True)
    esoc02_nacProf = fields.Boolean(
        string="nacProf", xsd_required=True)


class InfoComplem(spec_models.AbstractSpecMixin):
    _description = 'infocomplem'
    _name = 'esoc.02.evttreicapl.infocomplem'
    _generateds_type = 'infoComplemType'
    _concrete_rec_name = 'esoc_dtTreiCap'

    esoc02_dtTreiCap = fields.Date(
        string="dtTreiCap", xsd_required=True)
    esoc02_durTreiCap = fields.Monetary(
        string="durTreiCap", xsd_required=True)
    esoc02_modTreiCap = fields.Boolean(
        string="modTreiCap", xsd_required=True)
    esoc02_tpTreiCap = fields.Boolean(
        string="tpTreiCap", xsd_required=True)
    esoc02_ideProfResp = fields.One2many(
        "esoc.02.evttreicapl.ideprofresp",
        "esoc02_ideProfResp_infoComplem_id",
        string="Informações relativas ao profissional responsável",
        xsd_required=True
    )


class TreiCap(spec_models.AbstractSpecMixin):
    "Treinamentos, capacitações e exercícios simulados"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttreicapl.treicap'
    _generateds_type = 'treiCapType'
    _concrete_rec_name = 'esoc_codTreiCap'

    esoc02_codTreiCap = fields.Integer(
        string="codTreiCap", xsd_required=True)
    esoc02_obsTreiCap = fields.Char(
        string="obsTreiCap")
    esoc02_infoComplem = fields.Many2one(
        "esoc.02.evttreicapl.infocomplem",
        string="infoComplem")
