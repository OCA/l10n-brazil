# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:42 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmprPJ(spec_models.AbstractSpecMixin):
    "Informações do Empregador PJ"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.temprpj'
    _generateds_type = 'TEmprPJ'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveFopag(spec_models.AbstractSpecMixin):
    "Identificação do evento periódico"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.tideevefopag'
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


class TItemRemunRPPS(spec_models.AbstractSpecMixin):
    "Informações dos itens da remuneração"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.titemremunrpps'
    _generateds_type = 'TItemRemunRPPS'
    _concrete_rec_name = 'esoc_codRubr'

    esoc02_itensRemun_remunPerAnt_id = fields.Many2one(
        "esoc.02.evtrmnrppsl.remunperant")
    esoc02_itensRemun_remunPerApur_id = fields.Many2one(
        "esoc.02.evtrmnrppsl.remunperapur")
    esoc02_codRubr = fields.Char(
        string="codRubr", xsd_required=True)
    esoc02_ideTabRubr = fields.Char(
        string="ideTabRubr", xsd_required=True)
    esoc02_qtdRubr = fields.Monetary(
        string="qtdRubr")
    esoc02_fatorRubr = fields.Monetary(
        string="fatorRubr")
    esoc02_vrUnit = fields.Monetary(
        string="vrUnit")
    esoc02_vrRubr = fields.Monetary(
        string="vrRubr", xsd_required=True)


class TSaudeCol(spec_models.AbstractSpecMixin):
    "Planos de saúde coletivo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.tsaudecol'
    _generateds_type = 'TSaudeCol'
    _concrete_rec_name = 'esoc_detOper'

    esoc02_detOper = fields.One2many(
        "esoc.02.evtrmnrppsl.detoper",
        "esoc02_detOper_TSaudeCol_id",
        string="detOper", xsd_required=True,
        help="Detalhamento dos valores pagos a Operadoras de Planos de"
        "\nSaúde"
    )


class DetOper(spec_models.AbstractSpecMixin):
    "Detalhamento dos valores pagos a Operadoras de Planos de Saúde"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.detoper'
    _generateds_type = 'detOperType'
    _concrete_rec_name = 'esoc_cnpjOper'

    esoc02_detOper_TSaudeCol_id = fields.Many2one(
        "esoc.02.evtrmnrppsl.tsaudecol")
    esoc02_cnpjOper = fields.Char(
        string="cnpjOper", xsd_required=True)
    esoc02_regANS = fields.Char(
        string="regANS", xsd_required=True)
    esoc02_vrPgTit = fields.Monetary(
        string="vrPgTit", xsd_required=True)
    esoc02_detPlano = fields.One2many(
        "esoc.02.evtrmnrppsl.detplano",
        "esoc02_detPlano_detOper_id",
        string="Informações do dependente do plano privado de saúde"
    )


class DetPlano(spec_models.AbstractSpecMixin):
    "Informações do dependente do plano privado de saúde"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.detplano'
    _generateds_type = 'detPlanoType'
    _concrete_rec_name = 'esoc_tpDep'

    esoc02_detPlano_detOper_id = fields.Many2one(
        "esoc.02.evtrmnrppsl.detoper")
    esoc02_tpDep = fields.Char(
        string="tpDep", xsd_required=True)
    esoc02_cpfDep = fields.Char(
        string="cpfDep")
    esoc02_nmDep = fields.Char(
        string="nmDep", xsd_required=True)
    esoc02_dtNascto = fields.Date(
        string="dtNascto", xsd_required=True)
    esoc02_vlrPgDep = fields.Monetary(
        string="vlrPgDep", xsd_required=True)


class DmDev(spec_models.AbstractSpecMixin):
    "Demonstrativos de valores devidos ao trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.dmdev'
    _generateds_type = 'dmDevType'
    _concrete_rec_name = 'esoc_ideDmDev'

    esoc02_dmDev_evtRmnRPPS_id = fields.Many2one(
        "esoc.02.evtrmnrppsl.evtrmnrpps")
    esoc02_ideDmDev = fields.Char(
        string="ideDmDev", xsd_required=True)
    esoc02_infoPerApur = fields.Many2one(
        "esoc.02.evtrmnrppsl.infoperapur",
        string="Informações relativas ao período de apuração")
    esoc02_infoPerAnt = fields.Many2one(
        "esoc.02.evtrmnrppsl.infoperant",
        string="Remuneração relativa a Períodos Anteriores")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtrmnrppsl.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtRmnRPPS'

    esoc02_evtRmnRPPS = fields.Many2one(
        "esoc.02.evtrmnrppsl.evtrmnrpps",
        string="evtRmnRPPS", xsd_required=True)


class EvtRmnRPPS(spec_models.AbstractSpecMixin):
    "Remuneração de trabalhador não vinculado ao RGPS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.evtrmnrpps'
    _generateds_type = 'evtRmnRPPSType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtrmnrppsl.tideevefopag",
        string="Informações de identificação do evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtrmnrppsl.temprpj",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideTrabalhador = fields.Many2one(
        "esoc.02.evtrmnrppsl.idetrabalhador",
        string="Identificação do Trabalhador",
        xsd_required=True)
    esoc02_dmDev = fields.One2many(
        "esoc.02.evtrmnrppsl.dmdev",
        "esoc02_dmDev_evtRmnRPPS_id",
        string="Demonstrativos de valores devidos ao trabalhador",
        xsd_required=True
    )


class IdeADC(spec_models.AbstractSpecMixin):
    "Identificação da lei que determinou reajuste retroativo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.ideadc'
    _generateds_type = 'ideADCType'
    _concrete_rec_name = 'esoc_dtLei'

    esoc02_ideADC_infoPerAnt_id = fields.Many2one(
        "esoc.02.evtrmnrppsl.infoperant")
    esoc02_dtLei = fields.Date(
        string="dtLei", xsd_required=True)
    esoc02_nrLei = fields.Char(
        string="nrLei", xsd_required=True)
    esoc02_dtEf = fields.Date(
        string="dtEf")
    esoc02_idePeriodo = fields.One2many(
        "esoc.02.evtrmnrppsl.ideperiodo",
        "esoc02_idePeriodo_ideADC_id",
        string="Identificação do período de referência da remuneração",
        xsd_required=True
    )


class IdeEstab(spec_models.AbstractSpecMixin):
    "Identificação da unidade do órgão público"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.ideestab'
    _generateds_type = 'ideEstabType'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_ideEstab_infoPerApur_id = fields.Many2one(
        "esoc.02.evtrmnrppsl.infoperapur")
    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_remunPerApur = fields.One2many(
        "esoc.02.evtrmnrppsl.remunperapur",
        "esoc02_remunPerApur_ideEstab_id",
        string="Remuneração do Trabalhador no Período de Apuração",
        xsd_required=True
    )


class IdeEstab1(spec_models.AbstractSpecMixin):
    "Registro que identifica a unidade do órgão público"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.ideestab1'
    _generateds_type = 'ideEstabType1'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_ideEstab_idePeriodo_id = fields.Many2one(
        "esoc.02.evtrmnrppsl.ideperiodo")
    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_remunPerAnt = fields.One2many(
        "esoc.02.evtrmnrppsl.remunperant",
        "esoc02_remunPerAnt_ideEstab1_id",
        string="Remuneração do Trabalhador",
        xsd_required=True
    )


class IdePeriodo(spec_models.AbstractSpecMixin):
    "Identificação do período de referência da remuneração"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.ideperiodo'
    _generateds_type = 'idePeriodoType'
    _concrete_rec_name = 'esoc_perRef'

    esoc02_idePeriodo_ideADC_id = fields.Many2one(
        "esoc.02.evtrmnrppsl.ideadc")
    esoc02_perRef = fields.Char(
        string="perRef", xsd_required=True)
    esoc02_ideEstab = fields.One2many(
        "esoc.02.evtrmnrppsl.ideestab1",
        "esoc02_ideEstab_idePeriodo_id",
        string="Registro que identifica a unidade do órgão público",
        xsd_required=True
    )


class IdeTrabalhador(spec_models.AbstractSpecMixin):
    "Identificação do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.idetrabalhador'
    _generateds_type = 'ideTrabalhadorType'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab")
    esoc02_qtdDepFP = fields.Boolean(
        string="qtdDepFP")
    esoc02_procJudTrab = fields.One2many(
        "esoc.02.evtrmnrppsl.procjudtrab",
        "esoc02_procJudTrab_ideTrabalhador_id",
        string="procJudTrab",
        help="Informações sobre a existência de processos judiciais do"
        "\ntrabalhador"
    )


class InfoPerAnt(spec_models.AbstractSpecMixin):
    "Remuneração relativa a Períodos Anteriores"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.infoperant'
    _generateds_type = 'infoPerAntType'
    _concrete_rec_name = 'esoc_ideADC'

    esoc02_ideADC = fields.One2many(
        "esoc.02.evtrmnrppsl.ideadc",
        "esoc02_ideADC_infoPerAnt_id",
        string="Identificação da lei que determinou reajuste retroativo",
        xsd_required=True
    )


class InfoPerApur(spec_models.AbstractSpecMixin):
    "Informações relativas ao período de apuração"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.infoperapur'
    _generateds_type = 'infoPerApurType'
    _concrete_rec_name = 'esoc_ideEstab'

    esoc02_ideEstab = fields.One2many(
        "esoc.02.evtrmnrppsl.ideestab",
        "esoc02_ideEstab_infoPerApur_id",
        string="Identificação da unidade do órgão público",
        xsd_required=True
    )


class ProcJudTrab(spec_models.AbstractSpecMixin):
    """Informações sobre a existência de processos judiciais do trabalhador"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.procjudtrab'
    _generateds_type = 'procJudTrabType'
    _concrete_rec_name = 'esoc_tpTrib'

    esoc02_procJudTrab_ideTrabalhador_id = fields.Many2one(
        "esoc.02.evtrmnrppsl.idetrabalhador")
    esoc02_tpTrib = fields.Boolean(
        string="tpTrib", xsd_required=True)
    esoc02_nrProcJud = fields.Char(
        string="nrProcJud", xsd_required=True)
    esoc02_codSusp = fields.Integer(
        string="codSusp")


class RemunPerAnt(spec_models.AbstractSpecMixin):
    "Remuneração do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.remunperant'
    _generateds_type = 'remunPerAntType'
    _concrete_rec_name = 'esoc_matricula'

    esoc02_remunPerAnt_ideEstab1_id = fields.Many2one(
        "esoc.02.evtrmnrppsl.ideestab1")
    esoc02_matricula = fields.Char(
        string="matricula")
    esoc02_codCateg = fields.Integer(
        string="codCateg", xsd_required=True)
    esoc02_itensRemun = fields.One2many(
        "esoc.02.evtrmnrppsl.titemremunrpps",
        "esoc02_itensRemun_remunPerAnt_id",
        string="Itens da Remuneração do Trabalhador",
        xsd_required=True
    )


class RemunPerApur(spec_models.AbstractSpecMixin):
    "Remuneração do Trabalhador no Período de Apuração"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtrmnrppsl.remunperapur'
    _generateds_type = 'remunPerApurType'
    _concrete_rec_name = 'esoc_matricula'

    esoc02_remunPerApur_ideEstab_id = fields.Many2one(
        "esoc.02.evtrmnrppsl.ideestab")
    esoc02_matricula = fields.Char(
        string="matricula")
    esoc02_codCateg = fields.Integer(
        string="codCateg", xsd_required=True)
    esoc02_itensRemun = fields.One2many(
        "esoc.02.evtrmnrppsl.titemremunrpps",
        "esoc02_itensRemun_remunPerApur_id",
        string="Itens da Remuneração do Trabalhador",
        xsd_required=True
    )
    esoc02_infoSaudeColet = fields.Many2one(
        "esoc.02.evtrmnrppsl.tsaudecol",
        string="infoSaudeColet",
        help="Informações de plano privado coletivo empresarial de"
        "\nassistência à saúde")
