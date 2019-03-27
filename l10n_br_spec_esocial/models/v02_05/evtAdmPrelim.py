# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:19 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtadmpreli.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeCadastro(spec_models.AbstractSpecMixin):
    "Identificação de evento de cadastro/tabelas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmpreli.tidecadastro'
    _generateds_type = 'TIdeCadastro'
    _concrete_rec_name = 'esoc_tpAmb'

    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtadmpreli.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtAdmPrelim'

    esoc02_evtAdmPrelim = fields.Many2one(
        "esoc.02.evtadmpreli.evtadmprelim",
        string="evtAdmPrelim",
        xsd_required=True)


class EvtAdmPrelim(spec_models.AbstractSpecMixin):
    "Evento Admissão do Trabalhador - Registro Preliminar"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmpreli.evtadmprelim'
    _generateds_type = 'evtAdmPrelimType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtadmpreli.tidecadastro",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtadmpreli.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoRegPrelim = fields.Many2one(
        "esoc.02.evtadmpreli.inforegprelim",
        string="Informações do Registro Preliminar do Trabalhador",
        xsd_required=True)


class InfoRegPrelim(spec_models.AbstractSpecMixin):
    "Informações do Registro Preliminar do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtadmpreli.inforegprelim'
    _generateds_type = 'infoRegPrelimType'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_dtNascto = fields.Date(
        string="dtNascto", xsd_required=True)
    esoc02_dtAdm = fields.Date(
        string="dtAdm", xsd_required=True)
