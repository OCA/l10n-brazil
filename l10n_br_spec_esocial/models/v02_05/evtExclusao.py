# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:33 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtexclusao.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtexclusao.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtExclusao'

    esoc02_evtExclusao = fields.Many2one(
        "esoc.02.evtexclusao.evtexclusao",
        string="evtExclusao", xsd_required=True)


class EvtExclusao(spec_models.AbstractSpecMixin):
    "Evento de exclusão"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexclusao.evtexclusao'
    _generateds_type = 'evtExclusaoType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtexclusao.ideevento",
        string="Informações de identificação do evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtexclusao.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoExclusao = fields.Many2one(
        "esoc.02.evtexclusao.infoexclusao",
        string="Informação do evento que será excluído",
        xsd_required=True)


class IdeEvento(spec_models.AbstractSpecMixin):
    "Informações de identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexclusao.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'esoc_tpAmb'

    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class IdeFolhaPagto(spec_models.AbstractSpecMixin):
    """Registro que identifica a qual folha de pagamento pertence o evento que
    será excluído"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexclusao.idefolhapagto'
    _generateds_type = 'ideFolhaPagtoType'
    _concrete_rec_name = 'esoc_indApuracao'

    esoc02_indApuracao = fields.Boolean(
        string="indApuracao", xsd_required=True)
    esoc02_perApur = fields.Char(
        string="perApur", xsd_required=True)


class IdeTrabalhador(spec_models.AbstractSpecMixin):
    """Registro que identifica a qual trabalhador refere-se o evento a ser
    excluído"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexclusao.idetrabalhador'
    _generateds_type = 'ideTrabalhadorType'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab")


class InfoExclusao(spec_models.AbstractSpecMixin):
    "Informação do evento que será excluído"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexclusao.infoexclusao'
    _generateds_type = 'infoExclusaoType'
    _concrete_rec_name = 'esoc_tpEvento'

    esoc02_tpEvento = fields.Char(
        string="tpEvento", xsd_required=True)
    esoc02_nrRecEvt = fields.Char(
        string="nrRecEvt", xsd_required=True)
    esoc02_ideTrabalhador = fields.Many2one(
        "esoc.02.evtexclusao.idetrabalhador",
        string="Registro que identifica a qual trabalhador refere",
        help="Registro que identifica a qual trabalhador refere-se o evento"
        "\na ser excluído")
    esoc02_ideFolhaPagto = fields.Many2one(
        "esoc.02.evtexclusao.idefolhapagto",
        string="ideFolhaPagto",
        help="Registro que identifica a qual folha de pagamento pertence o"
        "\nevento que será excluído")
