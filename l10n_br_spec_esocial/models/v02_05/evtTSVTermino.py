# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:57 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evttsvtermi.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.tideevetrab'
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


class TRemunOutrasEmpresas(spec_models.AbstractSpecMixin):
    "Remuneração em outras empresas ou atividades"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.tremunoutrasempresas'
    _generateds_type = 'TRemunOutrasEmpresas'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_remunOutrEmpr_infoMV_id = fields.Many2one(
        "esoc.02.evttsvtermi.infomv")
    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_codCateg = fields.Integer(
        string="codCateg", xsd_required=True)
    esoc02_vlrRemunOE = fields.Monetary(
        string="vlrRemunOE", xsd_required=True)


class TSaudeCol(spec_models.AbstractSpecMixin):
    "Planos de saúde coletivo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.tsaudecol'
    _generateds_type = 'TSaudeCol'
    _concrete_rec_name = 'esoc_detOper'

    esoc02_detOper = fields.One2many(
        "esoc.02.evttsvtermi.detoper",
        "esoc02_detOper_TSaudeCol_id",
        string="detOper", xsd_required=True,
        help="Detalhamento dos valores pagos a Operadoras de Planos de"
        "\nSaúde"
    )


class DetOper(spec_models.AbstractSpecMixin):
    "Detalhamento dos valores pagos a Operadoras de Planos de Saúde"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.detoper'
    _generateds_type = 'detOperType'
    _concrete_rec_name = 'esoc_cnpjOper'

    esoc02_detOper_TSaudeCol_id = fields.Many2one(
        "esoc.02.evttsvtermi.tsaudecol")
    esoc02_cnpjOper = fields.Char(
        string="cnpjOper", xsd_required=True)
    esoc02_regANS = fields.Char(
        string="regANS", xsd_required=True)
    esoc02_vrPgTit = fields.Monetary(
        string="vrPgTit", xsd_required=True)
    esoc02_detPlano = fields.One2many(
        "esoc.02.evttsvtermi.detplano",
        "esoc02_detPlano_detOper_id",
        string="Informações do dependente do plano privado de saúde"
    )


class DetPlano(spec_models.AbstractSpecMixin):
    "Informações do dependente do plano privado de saúde"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.detplano'
    _generateds_type = 'detPlanoType'
    _concrete_rec_name = 'esoc_tpDep'

    esoc02_detPlano_detOper_id = fields.Many2one(
        "esoc.02.evttsvtermi.detoper")
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


class DetVerbas(spec_models.AbstractSpecMixin):
    _description = 'detverbas'
    _name = 'esoc.02.evttsvtermi.detverbas'
    _generateds_type = 'detVerbasType'
    _concrete_rec_name = 'esoc_codRubr'

    esoc02_detVerbas_ideEstabLot_id = fields.Many2one(
        "esoc.02.evttsvtermi.ideestablot")
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


class DmDev(spec_models.AbstractSpecMixin):
    "Identificação dos demonstrativos de pagamentos a serem efetuados"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.dmdev'
    _generateds_type = 'dmDevType'
    _concrete_rec_name = 'esoc_ideDmDev'

    esoc02_dmDev_verbasResc_id = fields.Many2one(
        "esoc.02.evttsvtermi.verbasresc")
    esoc02_ideDmDev = fields.Char(
        string="ideDmDev", xsd_required=True)
    esoc02_ideEstabLot = fields.One2many(
        "esoc.02.evttsvtermi.ideestablot",
        "esoc02_ideEstabLot_dmDev_id",
        string="Identificação do estabelecimento e lotação",
        xsd_required=True
    )


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttsvtermi.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtTSVTermino'

    esoc02_evtTSVTermino = fields.Many2one(
        "esoc.02.evttsvtermi.evttsvtermino",
        string="evtTSVTermino",
        xsd_required=True)


class EvtTSVTermino(spec_models.AbstractSpecMixin):
    "TSVE - Término"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.evttsvtermino'
    _generateds_type = 'evtTSVTerminoType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttsvtermi.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttsvtermi.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideTrabSemVinculo = fields.Many2one(
        "esoc.02.evttsvtermi.idetrabsemvinculo",
        string="Identificação do Trabalhador Sem Vínculo",
        xsd_required=True)
    esoc02_infoTSVTermino = fields.Many2one(
        "esoc.02.evttsvtermi.infotsvtermino",
        string="Trabalhador Sem Vínculo de Emprego",
        xsd_required=True,
        help="Trabalhador Sem Vínculo de Emprego - Término")


class IdeEstabLot(spec_models.AbstractSpecMixin):
    "Identificação do estabelecimento e lotação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.ideestablot'
    _generateds_type = 'ideEstabLotType'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_ideEstabLot_dmDev_id = fields.Many2one(
        "esoc.02.evttsvtermi.dmdev")
    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_codLotacao = fields.Char(
        string="codLotacao", xsd_required=True)
    esoc02_detVerbas = fields.One2many(
        "esoc.02.evttsvtermi.detverbas",
        "esoc02_detVerbas_ideEstabLot_id",
        string="detVerbas", xsd_required=True
    )
    esoc02_infoSaudeColet = fields.Many2one(
        "esoc.02.evttsvtermi.tsaudecol",
        string="infoSaudeColet",
        help="Informações de plano privado coletivo empresarial de"
        "\nassistência à saúde")
    esoc02_infoAgNocivo = fields.Many2one(
        "esoc.02.evttsvtermi.infoagnocivo",
        string="Grau de Exposição a Agentes Nocivos")
    esoc02_infoSimples = fields.Many2one(
        "esoc.02.evttsvtermi.infosimples",
        string="Informação relativa a empresas do Simples")


class IdeTrabSemVinculo(spec_models.AbstractSpecMixin):
    "Identificação do Trabalhador Sem Vínculo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.idetrabsemvinculo'
    _generateds_type = 'ideTrabSemVinculoType'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab")
    esoc02_codCateg = fields.Integer(
        string="codCateg", xsd_required=True)


class InfoAgNocivo(spec_models.AbstractSpecMixin):
    "Grau de Exposição a Agentes Nocivos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.infoagnocivo'
    _generateds_type = 'infoAgNocivoType'
    _concrete_rec_name = 'esoc_grauExp'

    esoc02_grauExp = fields.Boolean(
        string="grauExp", xsd_required=True)


class InfoMV(spec_models.AbstractSpecMixin):
    "Informação de Múltiplos Vínculos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.infomv'
    _generateds_type = 'infoMVType'
    _concrete_rec_name = 'esoc_indMV'

    esoc02_indMV = fields.Boolean(
        string="indMV", xsd_required=True)
    esoc02_remunOutrEmpr = fields.One2many(
        "esoc.02.evttsvtermi.tremunoutrasempresas",
        "esoc02_remunOutrEmpr_infoMV_id",
        string="remunOutrEmpr",
        xsd_required=True,
        help="Remuneração recebida pelo trabalhador em outras empresas ou"
        "\natividades"
    )


class InfoSimples(spec_models.AbstractSpecMixin):
    "Informação relativa a empresas do Simples"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.infosimples'
    _generateds_type = 'infoSimplesType'
    _concrete_rec_name = 'esoc_indSimples'

    esoc02_indSimples = fields.Boolean(
        string="indSimples", xsd_required=True)


class InfoTSVTermino(spec_models.AbstractSpecMixin):
    "Trabalhador Sem Vínculo de Emprego - Término"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.infotsvtermino'
    _generateds_type = 'infoTSVTerminoType'
    _concrete_rec_name = 'esoc_dtTerm'

    esoc02_dtTerm = fields.Date(
        string="dtTerm", xsd_required=True)
    esoc02_mtvDesligTSV = fields.Char(
        string="mtvDesligTSV")
    esoc02_pensAlim = fields.Boolean(
        string="pensAlim")
    esoc02_percAliment = fields.Monetary(
        string="percAliment")
    esoc02_vrAlim = fields.Monetary(
        string="vrAlim")
    esoc02_mudancaCPF = fields.Many2one(
        "esoc.02.evttsvtermi.mudancacpf",
        string="Informação do novo CPF do trabalhador")
    esoc02_verbasResc = fields.Many2one(
        "esoc.02.evttsvtermi.verbasresc",
        string="verbasResc")
    esoc02_quarentena = fields.Many2one(
        "esoc.02.evttsvtermi.quarentena",
        string="quarentena",
        help="Informações sobre a quarentena remunerada de trabalhador"
        "\ndesligado")


class MudancaCPF(spec_models.AbstractSpecMixin):
    "Informação do novo CPF do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.mudancacpf'
    _generateds_type = 'mudancaCPFType'
    _concrete_rec_name = 'esoc_novoCPF'

    esoc02_novoCPF = fields.Char(
        string="novoCPF", xsd_required=True)


class ProcJudTrab(spec_models.AbstractSpecMixin):
    """Informações sobre a existência de processos judiciais do trabalhador"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.procjudtrab'
    _generateds_type = 'procJudTrabType'
    _concrete_rec_name = 'esoc_tpTrib'

    esoc02_procJudTrab_verbasResc_id = fields.Many2one(
        "esoc.02.evttsvtermi.verbasresc")
    esoc02_tpTrib = fields.Boolean(
        string="tpTrib", xsd_required=True)
    esoc02_nrProcJud = fields.Char(
        string="nrProcJud", xsd_required=True)
    esoc02_codSusp = fields.Integer(
        string="codSusp")


class Quarentena(spec_models.AbstractSpecMixin):
    "Informações sobre a quarentena remunerada de trabalhador desligado"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvtermi.quarentena'
    _generateds_type = 'quarentenaType'
    _concrete_rec_name = 'esoc_dtFimQuar'

    esoc02_dtFimQuar = fields.Date(
        string="dtFimQuar", xsd_required=True)


class VerbasResc(spec_models.AbstractSpecMixin):
    _description = 'verbasresc'
    _name = 'esoc.02.evttsvtermi.verbasresc'
    _generateds_type = 'verbasRescType'
    _concrete_rec_name = 'esoc_dmDev'

    esoc02_dmDev = fields.One2many(
        "esoc.02.evttsvtermi.dmdev",
        "esoc02_dmDev_verbasResc_id",
        string="dmDev", xsd_required=True,
        help="Identificação dos demonstrativos de pagamentos a serem"
        "\nefetuados"
    )
    esoc02_procJudTrab = fields.One2many(
        "esoc.02.evttsvtermi.procjudtrab",
        "esoc02_procJudTrab_verbasResc_id",
        string="procJudTrab",
        help="Informações sobre a existência de processos judiciais do"
        "\ntrabalhador"
    )
    esoc02_infoMV = fields.Many2one(
        "esoc.02.evttsvtermi.infomv",
        string="Informação de Múltiplos Vínculos")
