# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:30 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtcontrsin.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class ContribSind(spec_models.AbstractSpecMixin):
    "Informações da contribuição sindical patronal"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcontrsin.contribsind'
    _generateds_type = 'contribSindType'
    _concrete_rec_name = 'esoc_cnpjSindic'

    esoc02_contribSind_evtContrSindPatr_id = fields.Many2one(
        "esoc.02.evtcontrsin.evtcontrsindpatr")
    esoc02_cnpjSindic = fields.Char(
        string="cnpjSindic", xsd_required=True)
    esoc02_tpContribSind = fields.Boolean(
        string="tpContribSind",
        xsd_required=True)
    esoc02_vlrContribSind = fields.Monetary(
        string="vlrContribSind",
        xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtcontrsin.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtContrSindPatr'

    esoc02_evtContrSindPatr = fields.Many2one(
        "esoc.02.evtcontrsin.evtcontrsindpatr",
        string="evtContrSindPatr",
        xsd_required=True)


class EvtContrSindPatr(spec_models.AbstractSpecMixin):
    "Contribuição sindical patronal"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcontrsin.evtcontrsindpatr'
    _generateds_type = 'evtContrSindPatrType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtcontrsin.ideevento",
        string="Informações de identificação do evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtcontrsin.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_contribSind = fields.One2many(
        "esoc.02.evtcontrsin.contribsind",
        "esoc02_contribSind_evtContrSindPatr_id",
        string="Informações da contribuição sindical patronal",
        xsd_required=True
    )


class IdeEvento(spec_models.AbstractSpecMixin):
    "Informações de identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcontrsin.ideevento'
    _generateds_type = 'ideEventoType'
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
