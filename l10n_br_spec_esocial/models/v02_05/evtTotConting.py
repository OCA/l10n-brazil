# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:51 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evttotconti.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttotconti.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtTotConting'

    esoc02_evtTotConting = fields.Many2one(
        "esoc.02.evttotconti.evttotconting",
        string="evtTotConting",
        xsd_required=True)


class EvtTotConting(spec_models.AbstractSpecMixin):
    """Solicitação contingencial de totalização de bases de
    cálculo/contribuições"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttotconti.evttotconting'
    _generateds_type = 'evtTotContingType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttotconti.ideevento",
        string="Informações de identificação do evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttotconti.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideRespInf = fields.Many2one(
        "esoc.02.evttotconti.iderespinf",
        string="Responsável pelas informações")


class IdeEvento(spec_models.AbstractSpecMixin):
    "Informações de identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttotconti.ideevento'
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


class IdeRespInf(spec_models.AbstractSpecMixin):
    "Responsável pelas informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttotconti.iderespinf'
    _generateds_type = 'ideRespInfType'
    _concrete_rec_name = 'esoc_nmResp'

    esoc02_nmResp = fields.Char(
        string="nmResp", xsd_required=True)
    esoc02_cpfResp = fields.Char(
        string="cpfResp", xsd_required=True)
    esoc02_telefone = fields.Char(
        string="telefone", xsd_required=True)
    esoc02_email = fields.Char(
        string="email")
