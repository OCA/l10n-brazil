# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:42 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtremunlib.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TItemRemuneracao(spec_models.AbstractSpecMixin):
    "Informações dos Itens da remuneração"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.titemremuneracao'
    _generateds_type = 'TItemRemuneracao'
    _concrete_rec_name = 'esoc_codRubr'

    esoc02_itensRemun_remunPerAnt_id = fields.Many2one(
        "esoc.02.evtremunlib.remunperant")
    esoc02_itensRemun_remunPerApur_id = fields.Many2one(
        "esoc.02.evtremunlib.remunperapur")
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


class TRemunOutrasEmpresas(spec_models.AbstractSpecMixin):
    "Remuneração em outras empresas ou atividades"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.tremunoutrasempresas'
    _generateds_type = 'TRemunOutrasEmpresas'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_remunOutrEmpr_infoMV_id = fields.Many2one(
        "esoc.02.evtremunlib.infomv")
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
    _name = 'esoc.02.evtremunlib.tsaudecol'
    _generateds_type = 'TSaudeCol'
    _concrete_rec_name = 'esoc_detOper'

    esoc02_detOper = fields.One2many(
        "esoc.02.evtremunlib.detoper",
        "esoc02_detOper_TSaudeCol_id",
        string="detOper", xsd_required=True,
        help="Detalhamento dos valores pagos a Operadoras de Planos de"
        "\nSaúde"
    )


class DetOper(spec_models.AbstractSpecMixin):
    "Detalhamento dos valores pagos a Operadoras de Planos de Saúde"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.detoper'
    _generateds_type = 'detOperType'
    _concrete_rec_name = 'esoc_cnpjOper'

    esoc02_detOper_TSaudeCol_id = fields.Many2one(
        "esoc.02.evtremunlib.tsaudecol")
    esoc02_cnpjOper = fields.Char(
        string="cnpjOper", xsd_required=True)
    esoc02_regANS = fields.Char(
        string="regANS", xsd_required=True)
    esoc02_vrPgTit = fields.Monetary(
        string="vrPgTit", xsd_required=True)
    esoc02_detPlano = fields.One2many(
        "esoc.02.evtremunlib.detplano",
        "esoc02_detPlano_detOper_id",
        string="Informações do dependente do plano privado de saúde"
    )


class DetPlano(spec_models.AbstractSpecMixin):
    "Informações do dependente do plano privado de saúde"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.detplano'
    _generateds_type = 'detPlanoType'
    _concrete_rec_name = 'esoc_tpDep'

    esoc02_detPlano_detOper_id = fields.Many2one(
        "esoc.02.evtremunlib.detoper")
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
    _name = 'esoc.02.evtremunlib.dmdev'
    _generateds_type = 'dmDevType'
    _concrete_rec_name = 'esoc_ideDmDev'

    esoc02_dmDev_evtRemun_id = fields.Many2one(
        "esoc.02.evtremunlib.evtremun")
    esoc02_ideDmDev = fields.Char(
        string="ideDmDev", xsd_required=True)
    esoc02_codCateg = fields.Integer(
        string="codCateg", xsd_required=True)
    esoc02_infoPerApur = fields.Many2one(
        "esoc.02.evtremunlib.infoperapur",
        string="Remuneração no período de apuração")
    esoc02_infoPerAnt = fields.Many2one(
        "esoc.02.evtremunlib.infoperant",
        string="Remuneração relativa a diferenças salariais")
    esoc02_infoComplCont = fields.Many2one(
        "esoc.02.evtremunlib.infocomplcont",
        string="Informações complementares contratuais do trabalhador")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtremunlib.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtRemun'

    esoc02_evtRemun = fields.Many2one(
        "esoc.02.evtremunlib.evtremun",
        string="evtRemun", xsd_required=True)


class EvtRemun(spec_models.AbstractSpecMixin):
    "Remuneração de trabalhador vinculado ao RGPS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.evtremun'
    _generateds_type = 'evtRemunType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtremunlib.ideevento",
        string="Informações de identificação do evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtremunlib.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideTrabalhador = fields.Many2one(
        "esoc.02.evtremunlib.idetrabalhador",
        string="Identificação do Trabalhador",
        xsd_required=True)
    esoc02_dmDev = fields.One2many(
        "esoc.02.evtremunlib.dmdev",
        "esoc02_dmDev_evtRemun_id",
        string="Demonstrativos de valores devidos ao trabalhador",
        xsd_required=True
    )


class IdeADC(spec_models.AbstractSpecMixin):
    """Instrumento ou situação ensejadora da remuneração em Períodos
    Anteriores"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.ideadc'
    _generateds_type = 'ideADCType'
    _concrete_rec_name = 'esoc_dtAcConv'

    esoc02_ideADC_infoPerAnt_id = fields.Many2one(
        "esoc.02.evtremunlib.infoperant")
    esoc02_dtAcConv = fields.Date(
        string="dtAcConv")
    esoc02_tpAcConv = fields.Char(
        string="tpAcConv", xsd_required=True)
    esoc02_compAcConv = fields.Char(
        string="compAcConv")
    esoc02_dtEfAcConv = fields.Date(
        string="dtEfAcConv")
    esoc02_dsc = fields.Char(
        string="dsc", xsd_required=True)
    esoc02_remunSuc = fields.Char(
        string="remunSuc", xsd_required=True)
    esoc02_idePeriodo = fields.One2many(
        "esoc.02.evtremunlib.ideperiodo",
        "esoc02_idePeriodo_ideADC_id",
        string="Identificação do período de referência da remuneração",
        xsd_required=True
    )


class IdeEstabLot(spec_models.AbstractSpecMixin):
    "Identificação do estabelecimento e lotação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.ideestablot'
    _generateds_type = 'ideEstabLotType'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_ideEstabLot_infoPerApur_id = fields.Many2one(
        "esoc.02.evtremunlib.infoperapur")
    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_codLotacao = fields.Char(
        string="codLotacao", xsd_required=True)
    esoc02_qtdDiasAv = fields.Boolean(
        string="qtdDiasAv")
    esoc02_remunPerApur = fields.One2many(
        "esoc.02.evtremunlib.remunperapur",
        "esoc02_remunPerApur_ideEstabLot_id",
        string="Remuneração do Trabalhador",
        xsd_required=True
    )


class IdeEstabLot1(spec_models.AbstractSpecMixin):
    "Identificação do estabelecimento e lotação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.ideestablot1'
    _generateds_type = 'ideEstabLotType1'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_ideEstabLot_idePeriodo_id = fields.Many2one(
        "esoc.02.evtremunlib.ideperiodo")
    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_codLotacao = fields.Char(
        string="codLotacao", xsd_required=True)
    esoc02_remunPerAnt = fields.One2many(
        "esoc.02.evtremunlib.remunperant",
        "esoc02_remunPerAnt_ideEstabLot1_id",
        string="Remuneração do Trabalhador",
        xsd_required=True
    )


class IdeEvento(spec_models.AbstractSpecMixin):
    "Informações de identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.ideevento'
    _generateds_type = 'ideEventoType'
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


class IdePeriodo(spec_models.AbstractSpecMixin):
    "Identificação do período de referência da remuneração"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.ideperiodo'
    _generateds_type = 'idePeriodoType'
    _concrete_rec_name = 'esoc_perRef'

    esoc02_idePeriodo_ideADC_id = fields.Many2one(
        "esoc.02.evtremunlib.ideadc")
    esoc02_perRef = fields.Char(
        string="perRef", xsd_required=True)
    esoc02_ideEstabLot = fields.One2many(
        "esoc.02.evtremunlib.ideestablot1",
        "esoc02_ideEstabLot_idePeriodo_id",
        string="Identificação do estabelecimento e lotação",
        xsd_required=True
    )


class IdeTrabalhador(spec_models.AbstractSpecMixin):
    "Identificação do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.idetrabalhador'
    _generateds_type = 'ideTrabalhadorType'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab")
    esoc02_infoMV = fields.Many2one(
        "esoc.02.evtremunlib.infomv",
        string="Informação de Múltiplos Vínculos")
    esoc02_infoComplem = fields.Many2one(
        "esoc.02.evtremunlib.infocomplem",
        string="Informações complementares de identificação do trabalhador")
    esoc02_procJudTrab = fields.One2many(
        "esoc.02.evtremunlib.procjudtrab",
        "esoc02_procJudTrab_ideTrabalhador_id",
        string="procJudTrab",
        help="Informações sobre a existência de processos judiciais do"
        "\ntrabalhador"
    )
    esoc02_infoInterm = fields.Many2one(
        "esoc.02.evtremunlib.infointerm",
        string="Informações relativas ao trabalho intermitente")


class InfoAgNocivo(spec_models.AbstractSpecMixin):
    "Grau de Exposição a Agentes Nocivos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.infoagnocivo'
    _generateds_type = 'infoAgNocivoType'
    _concrete_rec_name = 'esoc_grauExp'

    esoc02_grauExp = fields.Boolean(
        string="grauExp", xsd_required=True)


class InfoAgNocivo7(spec_models.AbstractSpecMixin):
    "Grau de Exposição a Agentes Nocivos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.infoagnocivo7'
    _generateds_type = 'infoAgNocivoType7'
    _concrete_rec_name = 'esoc_grauExp'

    esoc02_grauExp = fields.Boolean(
        string="grauExp", xsd_required=True)


class InfoComplCont(spec_models.AbstractSpecMixin):
    "Informações complementares contratuais do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.infocomplcont'
    _generateds_type = 'infoComplContType'
    _concrete_rec_name = 'esoc_codCBO'

    esoc02_codCBO = fields.Char(
        string="codCBO", xsd_required=True)
    esoc02_natAtividade = fields.Boolean(
        string="natAtividade")
    esoc02_qtdDiasTrab = fields.Boolean(
        string="qtdDiasTrab")


class InfoComplem(spec_models.AbstractSpecMixin):
    "Informações complementares de identificação do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.infocomplem'
    _generateds_type = 'infoComplemType'
    _concrete_rec_name = 'esoc_nmTrab'

    esoc02_nmTrab = fields.Char(
        string="nmTrab", xsd_required=True)
    esoc02_dtNascto = fields.Date(
        string="dtNascto", xsd_required=True)
    esoc02_sucessaoVinc = fields.Many2one(
        "esoc.02.evtremunlib.sucessaovinc",
        string="Grupo de informações da sucessão de vínculo trabalhista")


class InfoInterm(spec_models.AbstractSpecMixin):
    "Informações relativas ao trabalho intermitente"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.infointerm'
    _generateds_type = 'infoIntermType'
    _concrete_rec_name = 'esoc_qtdDiasInterm'

    esoc02_qtdDiasInterm = fields.Boolean(
        string="qtdDiasInterm",
        xsd_required=True)


class InfoMV(spec_models.AbstractSpecMixin):
    "Informação de Múltiplos Vínculos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.infomv'
    _generateds_type = 'infoMVType'
    _concrete_rec_name = 'esoc_indMV'

    esoc02_indMV = fields.Boolean(
        string="indMV", xsd_required=True)
    esoc02_remunOutrEmpr = fields.One2many(
        "esoc.02.evtremunlib.tremunoutrasempresas",
        "esoc02_remunOutrEmpr_infoMV_id",
        string="remunOutrEmpr",
        xsd_required=True,
        help="Remuneração recebida pelo trabalhador em outras empresas ou"
        "\natividades"
    )


class InfoPerAnt(spec_models.AbstractSpecMixin):
    "Remuneração relativa a diferenças salariais"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.infoperant'
    _generateds_type = 'infoPerAntType'
    _concrete_rec_name = 'esoc_ideADC'

    esoc02_ideADC = fields.One2many(
        "esoc.02.evtremunlib.ideadc",
        "esoc02_ideADC_infoPerAnt_id",
        string="ideADC", xsd_required=True,
        help="Instrumento ou situação ensejadora da remuneração em Períodos"
        "\nAnteriores"
    )


class InfoPerApur(spec_models.AbstractSpecMixin):
    "Remuneração no período de apuração"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.infoperapur'
    _generateds_type = 'infoPerApurType'
    _concrete_rec_name = 'esoc_ideEstabLot'

    esoc02_ideEstabLot = fields.One2many(
        "esoc.02.evtremunlib.ideestablot",
        "esoc02_ideEstabLot_infoPerApur_id",
        string="Identificação do estabelecimento e lotação",
        xsd_required=True
    )


class InfoTrabInterm(spec_models.AbstractSpecMixin):
    "Informações da(s) convocação(ões) de trabalho intermitente"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.infotrabinterm'
    _generateds_type = 'infoTrabIntermType'
    _concrete_rec_name = 'esoc_codConv'

    esoc02_infoTrabInterm_remunPerApur_id = fields.Many2one(
        "esoc.02.evtremunlib.remunperapur")
    esoc02_codConv = fields.Char(
        string="codConv", xsd_required=True)


class InfoTrabInterm9(spec_models.AbstractSpecMixin):
    "Informações da(s) convocação(ões) de trabalho intermitente"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.infotrabinterm9'
    _generateds_type = 'infoTrabIntermType9'
    _concrete_rec_name = 'esoc_codConv'

    esoc02_infoTrabInterm_remunPerAnt_id = fields.Many2one(
        "esoc.02.evtremunlib.remunperant")
    esoc02_codConv = fields.Char(
        string="codConv", xsd_required=True)


class ProcJudTrab(spec_models.AbstractSpecMixin):
    """Informações sobre a existência de processos judiciais do trabalhador"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.procjudtrab'
    _generateds_type = 'procJudTrabType'
    _concrete_rec_name = 'esoc_tpTrib'

    esoc02_procJudTrab_ideTrabalhador_id = fields.Many2one(
        "esoc.02.evtremunlib.idetrabalhador")
    esoc02_tpTrib = fields.Boolean(
        string="tpTrib", xsd_required=True)
    esoc02_nrProcJud = fields.Char(
        string="nrProcJud", xsd_required=True)
    esoc02_codSusp = fields.Integer(
        string="codSusp")


class RemunPerAnt(spec_models.AbstractSpecMixin):
    "Remuneração do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.remunperant'
    _generateds_type = 'remunPerAntType'
    _concrete_rec_name = 'esoc_matricula'

    esoc02_remunPerAnt_ideEstabLot1_id = fields.Many2one(
        "esoc.02.evtremunlib.ideestablot1")
    esoc02_matricula = fields.Char(
        string="matricula")
    esoc02_indSimples = fields.Boolean(
        string="indSimples")
    esoc02_itensRemun = fields.One2many(
        "esoc.02.evtremunlib.titemremuneracao",
        "esoc02_itensRemun_remunPerAnt_id",
        string="Itens da Remuneração do Trabalhador",
        xsd_required=True
    )
    esoc02_infoAgNocivo = fields.Many2one(
        "esoc.02.evtremunlib.infoagnocivo7",
        string="Grau de Exposição a Agentes Nocivos")
    esoc02_infoTrabInterm = fields.One2many(
        "esoc.02.evtremunlib.infotrabinterm9",
        "esoc02_infoTrabInterm_remunPerAnt_id",
        string="Informações da(s) convocação(ões) de trabalho intermitente"
    )


class RemunPerApur(spec_models.AbstractSpecMixin):
    "Remuneração do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.remunperapur'
    _generateds_type = 'remunPerApurType'
    _concrete_rec_name = 'esoc_matricula'

    esoc02_remunPerApur_ideEstabLot_id = fields.Many2one(
        "esoc.02.evtremunlib.ideestablot")
    esoc02_matricula = fields.Char(
        string="matricula")
    esoc02_indSimples = fields.Boolean(
        string="indSimples")
    esoc02_itensRemun = fields.One2many(
        "esoc.02.evtremunlib.titemremuneracao",
        "esoc02_itensRemun_remunPerApur_id",
        string="Itens da Remuneração do Trabalhador",
        xsd_required=True
    )
    esoc02_infoSaudeColet = fields.Many2one(
        "esoc.02.evtremunlib.tsaudecol",
        string="infoSaudeColet",
        help="Informações de plano privado coletivo empresarial de"
        "\nassistência à saúde")
    esoc02_infoAgNocivo = fields.Many2one(
        "esoc.02.evtremunlib.infoagnocivo",
        string="Grau de Exposição a Agentes Nocivos")
    esoc02_infoTrabInterm = fields.One2many(
        "esoc.02.evtremunlib.infotrabinterm",
        "esoc02_infoTrabInterm_remunPerApur_id",
        string="Informações da(s) convocação(ões) de trabalho intermitente"
    )


class SucessaoVinc(spec_models.AbstractSpecMixin):
    "Grupo de informações da sucessão de vínculo trabalhista"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtremunlib.sucessaovinc'
    _generateds_type = 'sucessaoVincType'
    _concrete_rec_name = 'esoc_tpInscAnt'

    esoc02_tpInscAnt = fields.Boolean(
        string="tpInscAnt", xsd_required=True)
    esoc02_cnpjEmpregAnt = fields.Char(
        string="cnpjEmpregAnt",
        xsd_required=True)
    esoc02_matricAnt = fields.Char(
        string="matricAnt")
    esoc02_dtAdm = fields.Date(
        string="dtAdm", xsd_required=True)
    esoc02_observacao = fields.Char(
        string="observacao")
