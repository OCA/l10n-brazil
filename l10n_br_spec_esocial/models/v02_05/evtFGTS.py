# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:35 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtfgtslib.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class BasePerAntE(spec_models.AbstractSpecMixin):
    "Bases de cálculo do FGTS, quando {tpAcConv} = [E]"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtfgtslib.baseperante'
    _generateds_type = 'basePerAntEType'
    _concrete_rec_name = 'esoc_tpValorE'

    esoc02_basePerAntE_infoBasePerAntE_id = fields.Many2one(
        "esoc.02.evtfgtslib.infobaseperante")
    esoc02_tpValorE = fields.Boolean(
        string="tpValorE", xsd_required=True)
    esoc02_baseFGTSE = fields.Monetary(
        string="baseFGTSE", xsd_required=True)


class BasePerApur(spec_models.AbstractSpecMixin):
    "Bases de cálculo do FGTS, exceto se {tpAcConv} = [E]"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtfgtslib.baseperapur'
    _generateds_type = 'basePerApurType'
    _concrete_rec_name = 'esoc_tpValor'

    esoc02_basePerApur_infoBaseFGTS_id = fields.Many2one(
        "esoc.02.evtfgtslib.infobasefgts")
    esoc02_tpValor = fields.Boolean(
        string="tpValor", xsd_required=True)
    esoc02_baseFGTS = fields.Monetary(
        string="baseFGTS", xsd_required=True)


class DpsPerAntE(spec_models.AbstractSpecMixin):
    "Valores de FGTS quando {tpAcConv} = [E]"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtfgtslib.dpsperante'
    _generateds_type = 'dpsPerAntEType'
    _concrete_rec_name = 'esoc_tpDpsE'

    esoc02_dpsPerAntE_infoDpsPerAntE_id = fields.Many2one(
        "esoc.02.evtfgtslib.infodpsperante")
    esoc02_tpDpsE = fields.Boolean(
        string="tpDpsE", xsd_required=True)
    esoc02_vrFGTSE = fields.Monetary(
        string="vrFGTSE", xsd_required=True)


class DpsPerApur(spec_models.AbstractSpecMixin):
    "Valores de FGTS, exceto se {tpAcConv} = [E]"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtfgtslib.dpsperapur'
    _generateds_type = 'dpsPerApurType'
    _concrete_rec_name = 'esoc_tpDps'

    esoc02_dpsPerApur_infoDpsFGTS_id = fields.Many2one(
        "esoc.02.evtfgtslib.infodpsfgts")
    esoc02_tpDps = fields.Boolean(
        string="tpDps", xsd_required=True)
    esoc02_vrFGTS = fields.Monetary(
        string="vrFGTS", xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtfgtslib.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtFGTS'

    esoc02_evtFGTS = fields.Many2one(
        "esoc.02.evtfgtslib.evtfgts",
        string="evtFGTS", xsd_required=True)


class EvtFGTS(spec_models.AbstractSpecMixin):
    "Evento FGTS consolidado"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtfgtslib.evtfgts'
    _generateds_type = 'evtFGTSType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtfgtslib.ideevento",
        string="Identificação do evento de retorno",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtfgtslib.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoFGTS = fields.Many2one(
        "esoc.02.evtfgtslib.infofgts",
        string="Informações relativas ao FGTS",
        xsd_required=True)


class IdeEvento(spec_models.AbstractSpecMixin):
    "Identificação do evento de retorno"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtfgtslib.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'esoc_perApur'

    esoc02_perApur = fields.Char(
        string="perApur", xsd_required=True)


class InfoBaseFGTS(spec_models.AbstractSpecMixin):
    "Bases de cálculo do FGTS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtfgtslib.infobasefgts'
    _generateds_type = 'infoBaseFGTSType'
    _concrete_rec_name = 'esoc_basePerApur'

    esoc02_basePerApur = fields.One2many(
        "esoc.02.evtfgtslib.baseperapur",
        "esoc02_basePerApur_infoBaseFGTS_id",
        string="Bases de cálculo do FGTS",
        help="Bases de cálculo do FGTS, exceto se {tpAcConv} = [E]"
    )
    esoc02_infoBasePerAntE = fields.One2many(
        "esoc.02.evtfgtslib.infobaseperante",
        "esoc02_infoBasePerAntE_infoBaseFGTS_id",
        string="Informações sobre bases de cálculo do FGTS",
        help="Informações sobre bases de cálculo do FGTS, quando {tpAcConv}"
        "\n= [E]"
    )


class InfoBasePerAntE(spec_models.AbstractSpecMixin):
    "Informações sobre bases de cálculo do FGTS, quando {tpAcConv} = [E]"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtfgtslib.infobaseperante'
    _generateds_type = 'infoBasePerAntEType'
    _concrete_rec_name = 'esoc_perRef'

    esoc02_infoBasePerAntE_infoBaseFGTS_id = fields.Many2one(
        "esoc.02.evtfgtslib.infobasefgts")
    esoc02_perRef = fields.Char(
        string="perRef", xsd_required=True)
    esoc02_basePerAntE = fields.One2many(
        "esoc.02.evtfgtslib.baseperante",
        "esoc02_basePerAntE_infoBasePerAntE_id",
        string="Bases de cálculo do FGTS",
        xsd_required=True,
        help="Bases de cálculo do FGTS, quando {tpAcConv} = [E]"
    )


class InfoDpsFGTS(spec_models.AbstractSpecMixin):
    "Informações sobre FGTS agrupadas por tipo de depósito"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtfgtslib.infodpsfgts'
    _generateds_type = 'infoDpsFGTSType'
    _concrete_rec_name = 'esoc_dpsPerApur'

    esoc02_dpsPerApur = fields.One2many(
        "esoc.02.evtfgtslib.dpsperapur",
        "esoc02_dpsPerApur_infoDpsFGTS_id",
        string="Valores de FGTS",
        help="Valores de FGTS, exceto se {tpAcConv} = [E]"
    )
    esoc02_infoDpsPerAntE = fields.One2many(
        "esoc.02.evtfgtslib.infodpsperante",
        "esoc02_infoDpsPerAntE_infoDpsFGTS_id",
        string="Informações sobre o FGTS quando {tpAcConv} = [E]"
    )


class InfoDpsPerAntE(spec_models.AbstractSpecMixin):
    "Informações sobre o FGTS quando {tpAcConv} = [E]"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtfgtslib.infodpsperante'
    _generateds_type = 'infoDpsPerAntEType'
    _concrete_rec_name = 'esoc_perRef'

    esoc02_infoDpsPerAntE_infoDpsFGTS_id = fields.Many2one(
        "esoc.02.evtfgtslib.infodpsfgts")
    esoc02_perRef = fields.Char(
        string="perRef", xsd_required=True)
    esoc02_dpsPerAntE = fields.One2many(
        "esoc.02.evtfgtslib.dpsperante",
        "esoc02_dpsPerAntE_infoDpsPerAntE_id",
        string="Valores de FGTS quando {tpAcConv} = [E]",
        xsd_required=True
    )


class InfoFGTS(spec_models.AbstractSpecMixin):
    "Informações relativas ao FGTS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtfgtslib.infofgts'
    _generateds_type = 'infoFGTSType'
    _concrete_rec_name = 'esoc_nrRecArqBase'

    esoc02_nrRecArqBase = fields.Char(
        string="nrRecArqBase",
        xsd_required=True)
    esoc02_indExistInfo = fields.Boolean(
        string="indExistInfo",
        xsd_required=True)
    esoc02_infoBaseFGTS = fields.Many2one(
        "esoc.02.evtfgtslib.infobasefgts",
        string="Bases de cálculo do FGTS")
    esoc02_infoDpsFGTS = fields.Many2one(
        "esoc.02.evtfgtslib.infodpsfgts",
        string="Informações sobre FGTS agrupadas por tipo de depósito")
