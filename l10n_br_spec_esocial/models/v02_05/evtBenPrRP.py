# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:26 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmprPJ(spec_models.AbstractSpecMixin):
    "Informações do Empregador PJ"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbenprrpl.temprpj'
    _generateds_type = 'TEmprPJ'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveFopag(spec_models.AbstractSpecMixin):
    "Identificação do evento periódico"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbenprrpl.tideevefopag'
    _generateds_type = 'TIdeEveFopag'
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


class DmDev(spec_models.AbstractSpecMixin):
    "Demonstrativos de valores devidos ao beneficiário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbenprrpl.dmdev'
    _generateds_type = 'dmDevType'
    _concrete_rec_name = 'esoc_tpBenef'

    esoc02_dmDev_evtBenPrRP_id = fields.Many2one(
        "esoc.02.evtbenprrpl.evtbenprrp")
    esoc02_tpBenef = fields.Boolean(
        string="tpBenef", xsd_required=True)
    esoc02_nrBenefic = fields.Char(
        string="nrBenefic", xsd_required=True)
    esoc02_ideDmDev = fields.Char(
        string="ideDmDev", xsd_required=True)
    esoc02_itens = fields.One2many(
        "esoc.02.evtbenprrpl.itens",
        "esoc02_itens_dmDev_id",
        string="Detalhamento dos valores devidos ao beneficiário",
        xsd_required=True
    )


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtbenprrpl.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtBenPrRP'

    esoc02_evtBenPrRP = fields.Many2one(
        "esoc.02.evtbenprrpl.evtbenprrp",
        string="evtBenPrRP", xsd_required=True)


class EvtBenPrRP(spec_models.AbstractSpecMixin):
    "Remuneração de trabalhadores RPPS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbenprrpl.evtbenprrp'
    _generateds_type = 'evtBenPrRPType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtbenprrpl.tideevefopag",
        string="Informações de identificação do evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtbenprrpl.temprpj",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideBenef = fields.Many2one(
        "esoc.02.evtbenprrpl.idebenef",
        string="Identificação do Trabalhador",
        xsd_required=True)
    esoc02_dmDev = fields.One2many(
        "esoc.02.evtbenprrpl.dmdev",
        "esoc02_dmDev_evtBenPrRP_id",
        string="Demonstrativos de valores devidos ao beneficiário",
        xsd_required=True
    )


class IdeBenef(spec_models.AbstractSpecMixin):
    "Identificação do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbenprrpl.idebenef'
    _generateds_type = 'ideBenefType'
    _concrete_rec_name = 'esoc_cpfBenef'

    esoc02_cpfBenef = fields.Char(
        string="cpfBenef", xsd_required=True)


class Itens(spec_models.AbstractSpecMixin):
    "Detalhamento dos valores devidos ao beneficiário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbenprrpl.itens'
    _generateds_type = 'itensType'
    _concrete_rec_name = 'esoc_codRubr'

    esoc02_itens_dmDev_id = fields.Many2one(
        "esoc.02.evtbenprrpl.dmdev")
    esoc02_codRubr = fields.Char(
        string="codRubr", xsd_required=True)
    esoc02_ideTabRubr = fields.Char(
        string="ideTabRubr", xsd_required=True)
    esoc02_vrRubr = fields.Monetary(
        string="vrRubr", xsd_required=True)
