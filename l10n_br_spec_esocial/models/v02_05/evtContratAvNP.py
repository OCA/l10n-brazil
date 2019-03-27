# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:29 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtcontrata.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveFopagMensal(spec_models.AbstractSpecMixin):
    "Identificação do Evento Periódico"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcontrata.tideevefopagmensal'
    _generateds_type = 'TIdeEveFopagMensal'
    _concrete_rec_name = 'esoc_indRetif'

    esoc02_indRetif = fields.Boolean(
        string="indRetif", xsd_required=True)
    esoc02_nrRecibo = fields.Char(
        string="nrRecibo")
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


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtcontrata.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtContratAvNP'

    esoc02_evtContratAvNP = fields.Many2one(
        "esoc.02.evtcontrata.evtcontratavnp",
        string="evtContratAvNP",
        xsd_required=True)


class EvtContratAvNP(spec_models.AbstractSpecMixin):
    "Remuneração de Trab. Avulsos Não Portuários"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcontrata.evtcontratavnp'
    _generateds_type = 'evtContratAvNPType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtcontrata.tideevefopagmensal",
        string="Informações de identificação do evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtcontrata.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_remunAvNP = fields.One2many(
        "esoc.02.evtcontrata.remunavnp",
        "esoc02_remunAvNP_evtContratAvNP_id",
        string="Remuneração dos trabalhadores avulsos não portuários",
        xsd_required=True
    )


class RemunAvNP(spec_models.AbstractSpecMixin):
    "Remuneração dos trabalhadores avulsos não portuários"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcontrata.remunavnp'
    _generateds_type = 'remunAvNPType'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_remunAvNP_evtContratAvNP_id = fields.Many2one(
        "esoc.02.evtcontrata.evtcontratavnp")
    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_codLotacao = fields.Char(
        string="codLotacao", xsd_required=True)
    esoc02_vrBcCp00 = fields.Monetary(
        string="vrBcCp00", xsd_required=True)
    esoc02_vrBcCp15 = fields.Monetary(
        string="vrBcCp15", xsd_required=True)
    esoc02_vrBcCp20 = fields.Monetary(
        string="vrBcCp20", xsd_required=True)
    esoc02_vrBcCp25 = fields.Monetary(
        string="vrBcCp25", xsd_required=True)
    esoc02_vrBcCp13 = fields.Monetary(
        string="vrBcCp13", xsd_required=True)
    esoc02_vrBcFgts = fields.Monetary(
        string="vrBcFgts", xsd_required=True)
    esoc02_vrDescCP = fields.Monetary(
        string="vrDescCP", xsd_required=True)
