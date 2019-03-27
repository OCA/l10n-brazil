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
    _name = 'esoc.02.evtbasesfgt.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class BasePerAntE(spec_models.AbstractSpecMixin):
    "Bases de cálculo quando {tpAcConv} = [E]"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasesfgt.baseperante'
    _generateds_type = 'basePerAntEType'
    _concrete_rec_name = 'esoc_tpValorE'

    esoc02_basePerAntE_infoBasePerAntE_id = fields.Many2one(
        "esoc.02.evtbasesfgt.infobaseperante")
    esoc02_tpValorE = fields.Boolean(
        string="tpValorE", xsd_required=True)
    esoc02_remFGTSE = fields.Monetary(
        string="remFGTSE", xsd_required=True)


class BasePerApur(spec_models.AbstractSpecMixin):
    "Bases de cálculo, exceto se {tpAcConv} = [E]"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasesfgt.baseperapur'
    _generateds_type = 'basePerApurType'
    _concrete_rec_name = 'esoc_tpValor'

    esoc02_basePerApur_infoBaseFGTS_id = fields.Many2one(
        "esoc.02.evtbasesfgt.infobasefgts")
    esoc02_tpValor = fields.Boolean(
        string="tpValor", xsd_required=True)
    esoc02_remFGTS = fields.Monetary(
        string="remFGTS", xsd_required=True)


class DpsPerAntE(spec_models.AbstractSpecMixin):
    "Valores de FGTS quando {tpAcConv} = [E]"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasesfgt.dpsperante'
    _generateds_type = 'dpsPerAntEType'
    _concrete_rec_name = 'esoc_tpDpsE'

    esoc02_dpsPerAntE_infoDpsPerAntE_id = fields.Many2one(
        "esoc.02.evtbasesfgt.infodpsperante")
    esoc02_tpDpsE = fields.Boolean(
        string="tpDpsE", xsd_required=True)
    esoc02_dpsFGTSE = fields.Monetary(
        string="dpsFGTSE", xsd_required=True)


class DpsPerApur(spec_models.AbstractSpecMixin):
    "Valor do FGTS, exceto se {tpAcConv} = [E]"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasesfgt.dpsperapur'
    _generateds_type = 'dpsPerApurType'
    _concrete_rec_name = 'esoc_tpDps'

    esoc02_dpsPerApur_infoTrabDps_id = fields.Many2one(
        "esoc.02.evtbasesfgt.infotrabdps")
    esoc02_tpDps = fields.Boolean(
        string="tpDps", xsd_required=True)
    esoc02_dpsFGTS = fields.Monetary(
        string="dpsFGTS", xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtbasesfgt.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtBasesFGTS'

    esoc02_evtBasesFGTS = fields.Many2one(
        "esoc.02.evtbasesfgt.evtbasesfgts",
        string="evtBasesFGTS",
        xsd_required=True)


class EvtBasesFGTS(spec_models.AbstractSpecMixin):
    "Evento Bases FGTS por Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasesfgt.evtbasesfgts'
    _generateds_type = 'evtBasesFGTSType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtbasesfgt.ideevento",
        string="Identificação do evento de retorno",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtbasesfgt.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideTrabalhador = fields.Many2one(
        "esoc.02.evtbasesfgt.idetrabalhador",
        string="Identificação do Trabalhador",
        xsd_required=True)
    esoc02_infoFGTS = fields.Many2one(
        "esoc.02.evtbasesfgt.infofgts",
        string="Informações relativas ao FGTS")


class IdeEstabLot(spec_models.AbstractSpecMixin):
    "Identificação do estabelecimento e lotação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasesfgt.ideestablot'
    _generateds_type = 'ideEstabLotType'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_ideEstabLot_infoFGTS_id = fields.Many2one(
        "esoc.02.evtbasesfgt.infofgts")
    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_codLotacao = fields.Char(
        string="codLotacao", xsd_required=True)
    esoc02_infoTrabFGTS = fields.One2many(
        "esoc.02.evtbasesfgt.infotrabfgts",
        "esoc02_infoTrabFGTS_ideEstabLot_id",
        string="Informações relativas à matrícula",
        xsd_required=True,
        help="Informações relativas à matrícula, categoria e incidências"
    )


class IdeEvento(spec_models.AbstractSpecMixin):
    "Identificação do evento de retorno"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasesfgt.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'esoc_nrRecArqBase'

    esoc02_nrRecArqBase = fields.Char(
        string="nrRecArqBase",
        xsd_required=True)
    esoc02_perApur = fields.Char(
        string="perApur", xsd_required=True)


class IdeTrabalhador(spec_models.AbstractSpecMixin):
    "Identificação do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasesfgt.idetrabalhador'
    _generateds_type = 'ideTrabalhadorType'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab")


class InfoBaseFGTS(spec_models.AbstractSpecMixin):
    "Bases de cálculo do FGTS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasesfgt.infobasefgts'
    _generateds_type = 'infoBaseFGTSType'
    _concrete_rec_name = 'esoc_basePerApur'

    esoc02_basePerApur = fields.One2many(
        "esoc.02.evtbasesfgt.baseperapur",
        "esoc02_basePerApur_infoBaseFGTS_id",
        string="Bases de cálculo",
        help="Bases de cálculo, exceto se {tpAcConv} = [E]"
    )
    esoc02_infoBasePerAntE = fields.One2many(
        "esoc.02.evtbasesfgt.infobaseperante",
        "esoc02_infoBasePerAntE_infoBaseFGTS_id",
        string="Informações sobre bases do FGTS quando {tpAcConv} = [E]"
    )


class InfoBasePerAntE(spec_models.AbstractSpecMixin):
    "Informações sobre bases do FGTS quando {tpAcConv} = [E]"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasesfgt.infobaseperante'
    _generateds_type = 'infoBasePerAntEType'
    _concrete_rec_name = 'esoc_perRef'

    esoc02_infoBasePerAntE_infoBaseFGTS_id = fields.Many2one(
        "esoc.02.evtbasesfgt.infobasefgts")
    esoc02_perRef = fields.Char(
        string="perRef", xsd_required=True)
    esoc02_basePerAntE = fields.One2many(
        "esoc.02.evtbasesfgt.baseperante",
        "esoc02_basePerAntE_infoBasePerAntE_id",
        string="Bases de cálculo quando {tpAcConv} = [E]",
        xsd_required=True
    )


class InfoDpsFGTS(spec_models.AbstractSpecMixin):
    "Informações sobre valores de FGTS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasesfgt.infodpsfgts'
    _generateds_type = 'infoDpsFGTSType'
    _concrete_rec_name = 'esoc_infoTrabDps'

    esoc02_infoTrabDps = fields.One2many(
        "esoc.02.evtbasesfgt.infotrabdps",
        "esoc02_infoTrabDps_infoDpsFGTS_id",
        string="Matrícula e categoria do trabalhador",
        xsd_required=True
    )


class InfoDpsPerAntE(spec_models.AbstractSpecMixin):
    "Informações sobre FGTS quando {tpAcConv} = [E]"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasesfgt.infodpsperante'
    _generateds_type = 'infoDpsPerAntEType'
    _concrete_rec_name = 'esoc_perRef'

    esoc02_infoDpsPerAntE_infoTrabDps_id = fields.Many2one(
        "esoc.02.evtbasesfgt.infotrabdps")
    esoc02_perRef = fields.Char(
        string="perRef", xsd_required=True)
    esoc02_dpsPerAntE = fields.One2many(
        "esoc.02.evtbasesfgt.dpsperante",
        "esoc02_dpsPerAntE_infoDpsPerAntE_id",
        string="Valores de FGTS quando {tpAcConv} = [E]",
        xsd_required=True
    )


class InfoFGTS(spec_models.AbstractSpecMixin):
    "Informações relativas ao FGTS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasesfgt.infofgts'
    _generateds_type = 'infoFGTSType'
    _concrete_rec_name = 'esoc_dtVenc'

    esoc02_dtVenc = fields.Date(
        string="dtVenc")
    esoc02_ideEstabLot = fields.One2many(
        "esoc.02.evtbasesfgt.ideestablot",
        "esoc02_ideEstabLot_infoFGTS_id",
        string="Identificação do estabelecimento e lotação",
        xsd_required=True
    )
    esoc02_infoDpsFGTS = fields.Many2one(
        "esoc.02.evtbasesfgt.infodpsfgts",
        string="Informações sobre valores de FGTS")


class InfoTrabDps(spec_models.AbstractSpecMixin):
    "Matrícula e categoria do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasesfgt.infotrabdps'
    _generateds_type = 'infoTrabDpsType'
    _concrete_rec_name = 'esoc_matricula'

    esoc02_infoTrabDps_infoDpsFGTS_id = fields.Many2one(
        "esoc.02.evtbasesfgt.infodpsfgts")
    esoc02_matricula = fields.Char(
        string="matricula")
    esoc02_codCateg = fields.Integer(
        string="codCateg", xsd_required=True)
    esoc02_dpsPerApur = fields.One2many(
        "esoc.02.evtbasesfgt.dpsperapur",
        "esoc02_dpsPerApur_infoTrabDps_id",
        string="Valor do FGTS",
        help="Valor do FGTS, exceto se {tpAcConv} = [E]"
    )
    esoc02_infoDpsPerAntE = fields.One2many(
        "esoc.02.evtbasesfgt.infodpsperante",
        "esoc02_infoDpsPerAntE_infoTrabDps_id",
        string="Informações sobre FGTS quando {tpAcConv} = [E]"
    )


class InfoTrabFGTS(spec_models.AbstractSpecMixin):
    "Informações relativas à matrícula, categoria e incidências"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasesfgt.infotrabfgts'
    _generateds_type = 'infoTrabFGTSType'
    _concrete_rec_name = 'esoc_matricula'

    esoc02_infoTrabFGTS_ideEstabLot_id = fields.Many2one(
        "esoc.02.evtbasesfgt.ideestablot")
    esoc02_matricula = fields.Char(
        string="matricula")
    esoc02_codCateg = fields.Integer(
        string="codCateg", xsd_required=True)
    esoc02_dtAdm = fields.Date(
        string="dtAdm")
    esoc02_dtDeslig = fields.Date(
        string="dtDeslig")
    esoc02_dtInicio = fields.Date(
        string="dtInicio")
    esoc02_mtvDeslig = fields.Char(
        string="mtvDeslig")
    esoc02_dtTerm = fields.Date(
        string="dtTerm")
    esoc02_mtvDesligTSV = fields.Char(
        string="mtvDesligTSV")
    esoc02_infoBaseFGTS = fields.Many2one(
        "esoc.02.evtbasesfgt.infobasefgts",
        string="Bases de cálculo do FGTS")
