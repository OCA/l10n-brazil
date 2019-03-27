# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:38 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtirrflib.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtirrflib.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtIrrf'

    esoc02_evtIrrf = fields.Many2one(
        "esoc.02.evtirrflib.evtirrf",
        string="evtIrrf", xsd_required=True)


class EvtIrrf(spec_models.AbstractSpecMixin):
    _description = 'evtirrf'
    _name = 'esoc.02.evtirrflib.evtirrf'
    _generateds_type = 'evtIrrfType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtirrflib.ideevento",
        string="Identificação do evento de retorno",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtirrflib.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoIRRF = fields.Many2one(
        "esoc.02.evtirrflib.infoirrf",
        string="Informações relativas ao IRRF",
        xsd_required=True)


class IdeEvento(spec_models.AbstractSpecMixin):
    "Identificação do evento de retorno"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtirrflib.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'esoc_perApur'

    esoc02_perApur = fields.Char(
        string="perApur", xsd_required=True)


class InfoCRContrib(spec_models.AbstractSpecMixin):
    "Totalizador do IRRF por CR"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtirrflib.infocrcontrib'
    _generateds_type = 'infoCRContribType'
    _concrete_rec_name = 'esoc_tpCR'

    esoc02_infoCRContrib_infoIRRF_id = fields.Many2one(
        "esoc.02.evtirrflib.infoirrf")
    esoc02_tpCR = fields.Integer(
        string="tpCR", xsd_required=True)
    esoc02_vrCR = fields.Monetary(
        string="vrCR", xsd_required=True)


class InfoIRRF(spec_models.AbstractSpecMixin):
    "Informações relativas ao IRRF"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtirrflib.infoirrf'
    _generateds_type = 'infoIRRFType'
    _concrete_rec_name = 'esoc_nrRecArqBase'

    esoc02_nrRecArqBase = fields.Char(
        string="nrRecArqBase",
        xsd_required=True)
    esoc02_indExistInfo = fields.Boolean(
        string="indExistInfo",
        xsd_required=True)
    esoc02_infoCRContrib = fields.One2many(
        "esoc.02.evtirrflib.infocrcontrib",
        "esoc02_infoCRContrib_infoIRRF_id",
        string="Totalizador do IRRF por CR"
    )
