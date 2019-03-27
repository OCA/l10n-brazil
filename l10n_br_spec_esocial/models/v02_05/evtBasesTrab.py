# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:25 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtbasestra.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class CalcTerc(spec_models.AbstractSpecMixin):
    """Cálculo das contribuições sociais devidas a Outras Entidades e Fundos"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasestra.calcterc'
    _generateds_type = 'calcTercType'
    _concrete_rec_name = 'esoc_tpCR'

    esoc02_calcTerc_infoCategIncid_id = fields.Many2one(
        "esoc.02.evtbasestra.infocategincid")
    esoc02_tpCR = fields.Integer(
        string="tpCR", xsd_required=True)
    esoc02_vrCsSegTerc = fields.Monetary(
        string="vrCsSegTerc", xsd_required=True)
    esoc02_vrDescTerc = fields.Monetary(
        string="vrDescTerc", xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtbasestra.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtBasesTrab'

    esoc02_evtBasesTrab = fields.Many2one(
        "esoc.02.evtbasestra.evtbasestrab",
        string="evtBasesTrab",
        xsd_required=True)


class EvtBasesTrab(spec_models.AbstractSpecMixin):
    "Evento Bases por Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasestra.evtbasestrab'
    _generateds_type = 'evtBasesTrabType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtbasestra.ideevento",
        string="Identificação do evento de retorno",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtbasestra.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideTrabalhador = fields.Many2one(
        "esoc.02.evtbasestra.idetrabalhador",
        string="Identificação do Trabalhador",
        xsd_required=True)
    esoc02_infoCpCalc = fields.One2many(
        "esoc.02.evtbasestra.infocpcalc",
        "esoc02_infoCpCalc_evtBasesTrab_id",
        string="Cálculo da contribuição previdenciária do segurado"
    )
    esoc02_infoCp = fields.Many2one(
        "esoc.02.evtbasestra.infocp",
        string="infoCp",
        help="Informações sobre bases e valores das contribuições sociais")


class IdeEstabLot(spec_models.AbstractSpecMixin):
    "Identificação do estabelecimento ou obra e da lotação tributária"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasestra.ideestablot'
    _generateds_type = 'ideEstabLotType'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_ideEstabLot_infoCp_id = fields.Many2one(
        "esoc.02.evtbasestra.infocp")
    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_codLotacao = fields.Char(
        string="codLotacao", xsd_required=True)
    esoc02_infoCategIncid = fields.One2many(
        "esoc.02.evtbasestra.infocategincid",
        "esoc02_infoCategIncid_ideEstabLot_id",
        string="infoCategIncid",
        xsd_required=True,
        help="Informações relativas à matrícula e categoria do trabalhador"
        "\ne tipos de incidências"
    )


class IdeEvento(spec_models.AbstractSpecMixin):
    "Identificação do evento de retorno"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasestra.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'esoc_nrRecArqBase'

    esoc02_nrRecArqBase = fields.Char(
        string="nrRecArqBase",
        xsd_required=True)
    esoc02_indApuracao = fields.Boolean(
        string="indApuracao", xsd_required=True)
    esoc02_perApur = fields.Char(
        string="perApur", xsd_required=True)


class IdeTrabalhador(spec_models.AbstractSpecMixin):
    "Identificação do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasestra.idetrabalhador'
    _generateds_type = 'ideTrabalhadorType'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_procJudTrab = fields.One2many(
        "esoc.02.evtbasestra.procjudtrab",
        "esoc02_procJudTrab_ideTrabalhador_id",
        string="Processos judiciais do trabalhador"
    )


class InfoBaseCS(spec_models.AbstractSpecMixin):
    "Informações sobre bases de cálculo, descontos e deduções de CS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasestra.infobasecs'
    _generateds_type = 'infoBaseCSType'
    _concrete_rec_name = 'esoc_ind13'

    esoc02_infoBaseCS_infoCategIncid_id = fields.Many2one(
        "esoc.02.evtbasestra.infocategincid")
    esoc02_ind13 = fields.Boolean(
        string="ind13", xsd_required=True)
    esoc02_tpValor = fields.Boolean(
        string="tpValor", xsd_required=True)
    esoc02_valor = fields.Monetary(
        string="valor", xsd_required=True)


class InfoCategIncid(spec_models.AbstractSpecMixin):
    """Informações relativas à matrícula e categoria do trabalhador e tipos de
    incidências"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasestra.infocategincid'
    _generateds_type = 'infoCategIncidType'
    _concrete_rec_name = 'esoc_matricula'

    esoc02_infoCategIncid_ideEstabLot_id = fields.Many2one(
        "esoc.02.evtbasestra.ideestablot")
    esoc02_matricula = fields.Char(
        string="matricula")
    esoc02_codCateg = fields.Integer(
        string="codCateg", xsd_required=True)
    esoc02_indSimples = fields.Boolean(
        string="indSimples")
    esoc02_infoBaseCS = fields.One2many(
        "esoc.02.evtbasestra.infobasecs",
        "esoc02_infoBaseCS_infoCategIncid_id",
        string="Informações sobre bases de cálculo",
        help="Informações sobre bases de cálculo, descontos e deduções de"
        "\nCS"
    )
    esoc02_calcTerc = fields.One2many(
        "esoc.02.evtbasestra.calcterc",
        "esoc02_calcTerc_infoCategIncid_id",
        string="calcTerc",
        help="Cálculo das contribuições sociais devidas a Outras Entidades"
        "\ne Fundos"
    )


class InfoCpCalc(spec_models.AbstractSpecMixin):
    "Cálculo da contribuição previdenciária do segurado"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasestra.infocpcalc'
    _generateds_type = 'infoCpCalcType'
    _concrete_rec_name = 'esoc_tpCR'

    esoc02_infoCpCalc_evtBasesTrab_id = fields.Many2one(
        "esoc.02.evtbasestra.evtbasestrab")
    esoc02_tpCR = fields.Integer(
        string="tpCR", xsd_required=True)
    esoc02_vrCpSeg = fields.Monetary(
        string="vrCpSeg", xsd_required=True)
    esoc02_vrDescSeg = fields.Monetary(
        string="vrDescSeg", xsd_required=True)


class InfoCp(spec_models.AbstractSpecMixin):
    "Informações sobre bases e valores das contribuições sociais"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasestra.infocp'
    _generateds_type = 'infoCpType'
    _concrete_rec_name = 'esoc_ideEstabLot'

    esoc02_ideEstabLot = fields.One2many(
        "esoc.02.evtbasestra.ideestablot",
        "esoc02_ideEstabLot_infoCp_id",
        string="ideEstabLot", xsd_required=True,
        help="Identificação do estabelecimento ou obra e da lotação"
        "\ntributária"
    )


class ProcJudTrab(spec_models.AbstractSpecMixin):
    "Processos judiciais do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtbasestra.procjudtrab'
    _generateds_type = 'procJudTrabType'
    _concrete_rec_name = 'esoc_nrProcJud'

    esoc02_procJudTrab_ideTrabalhador_id = fields.Many2one(
        "esoc.02.evtbasestra.idetrabalhador")
    esoc02_nrProcJud = fields.Char(
        string="nrProcJud", xsd_required=True)
    esoc02_codSusp = fields.Integer(
        string="codSusp", xsd_required=True)
