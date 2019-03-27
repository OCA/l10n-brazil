# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:24 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtavprevio.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtavprevio.tideevetrab'
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
    _name = 'esoc.02.evtavprevio.tidevinculonisobrig'
    _generateds_type = 'TIdeVinculoNisObrig'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab", xsd_required=True)
    esoc02_matricula = fields.Char(
        string="matricula", xsd_required=True)


class CancAvPrevio(spec_models.AbstractSpecMixin):
    "Cancelamento do Aviso Prévio"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtavprevio.cancavprevio'
    _generateds_type = 'cancAvPrevioType'
    _concrete_rec_name = 'esoc_dtCancAvPrv'

    esoc02_dtCancAvPrv = fields.Date(
        string="dtCancAvPrv", xsd_required=True)
    esoc02_observacao = fields.Char(
        string="observacao")
    esoc02_mtvCancAvPrevio = fields.Boolean(
        string="mtvCancAvPrevio",
        xsd_required=True)


class DetAvPrevio(spec_models.AbstractSpecMixin):
    _description = 'detavprevio'
    _name = 'esoc.02.evtavprevio.detavprevio'
    _generateds_type = 'detAvPrevioType'
    _concrete_rec_name = 'esoc_dtAvPrv'

    esoc02_dtAvPrv = fields.Date(
        string="dtAvPrv", xsd_required=True)
    esoc02_dtPrevDeslig = fields.Date(
        string="dtPrevDeslig",
        xsd_required=True)
    esoc02_tpAvPrevio = fields.Boolean(
        string="tpAvPrevio", xsd_required=True)
    esoc02_observacao = fields.Char(
        string="observacao")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtavprevio.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtAvPrevio'

    esoc02_evtAvPrevio = fields.Many2one(
        "esoc.02.evtavprevio.evtavprevio",
        string="evtAvPrevio", xsd_required=True)


class EvtAvPrevio(spec_models.AbstractSpecMixin):
    "Evento Aviso Prévio"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtavprevio.evtavprevio'
    _generateds_type = 'evtAvPrevioType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtavprevio.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtavprevio.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideVinculo = fields.Many2one(
        "esoc.02.evtavprevio.tidevinculonisobrig",
        string="Informações de Identificação do Trabalhador e do Vínculo",
        xsd_required=True)
    esoc02_infoAvPrevio = fields.Many2one(
        "esoc.02.evtavprevio.infoavprevio",
        string="Informações do Aviso Prévio",
        xsd_required=True)


class InfoAvPrevio(spec_models.AbstractSpecMixin):
    "Informações do Aviso Prévio"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtavprevio.infoavprevio'
    _generateds_type = 'infoAvPrevioType'
    _concrete_rec_name = 'esoc_detAvPrevio'

    esoc02_choice1 = fields.Selection([
        ('esoc02_detAvPrevio', 'detAvPrevio'),
        ('esoc02_cancAvPrevio', 'cancAvPrevio')],
        "detAvPrevio/cancAvPrevio",
        default="esoc02_detAvPrevio")
    esoc02_detAvPrevio = fields.Many2one(
        "esoc.02.evtavprevio.detavprevio",
        choice='1',
        string="detAvPrevio", xsd_required=True)
    esoc02_cancAvPrevio = fields.Many2one(
        "esoc.02.evtavprevio.cancavprevio",
        choice='1',
        string="Cancelamento do Aviso Prévio",
        xsd_required=True)
