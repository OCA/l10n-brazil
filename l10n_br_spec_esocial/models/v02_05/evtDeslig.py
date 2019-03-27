# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:32 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtdesligli.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.tideevetrab'
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
    _name = 'esoc.02.evtdesligli.tidevinculonisobrig'
    _generateds_type = 'TIdeVinculoNisObrig'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab", xsd_required=True)
    esoc02_matricula = fields.Char(
        string="matricula", xsd_required=True)


class TRemunOutrasEmpresas(spec_models.AbstractSpecMixin):
    "Remuneração em outras empresas ou atividades"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.tremunoutrasempresas'
    _generateds_type = 'TRemunOutrasEmpresas'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_remunOutrEmpr_infoMV_id = fields.Many2one(
        "esoc.02.evtdesligli.infomv")
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
    _name = 'esoc.02.evtdesligli.tsaudecol'
    _generateds_type = 'TSaudeCol'
    _concrete_rec_name = 'esoc_detOper'

    esoc02_detOper = fields.One2many(
        "esoc.02.evtdesligli.detoper",
        "esoc02_detOper_TSaudeCol_id",
        string="detOper", xsd_required=True,
        help="Detalhamento dos valores pagos a Operadoras de Planos de"
        "\nSaúde"
    )


class ConsigFGTS(spec_models.AbstractSpecMixin):
    """Informações sobre operação de crédito consignado com garantia de FGTS"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.consigfgts'
    _generateds_type = 'consigFGTSType'
    _concrete_rec_name = 'esoc_insConsig'

    esoc02_consigFGTS_infoDeslig_id = fields.Many2one(
        "esoc.02.evtdesligli.infodeslig")
    esoc02_insConsig = fields.Char(
        string="insConsig", xsd_required=True)
    esoc02_nrContr = fields.Char(
        string="nrContr", xsd_required=True)


class DetOper(spec_models.AbstractSpecMixin):
    "Detalhamento dos valores pagos a Operadoras de Planos de Saúde"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.detoper'
    _generateds_type = 'detOperType'
    _concrete_rec_name = 'esoc_cnpjOper'

    esoc02_detOper_TSaudeCol_id = fields.Many2one(
        "esoc.02.evtdesligli.tsaudecol")
    esoc02_cnpjOper = fields.Char(
        string="cnpjOper", xsd_required=True)
    esoc02_regANS = fields.Char(
        string="regANS", xsd_required=True)
    esoc02_vrPgTit = fields.Monetary(
        string="vrPgTit", xsd_required=True)
    esoc02_detPlano = fields.One2many(
        "esoc.02.evtdesligli.detplano",
        "esoc02_detPlano_detOper_id",
        string="Informações do dependente do plano privado de saúde"
    )


class DetPlano(spec_models.AbstractSpecMixin):
    "Informações do dependente do plano privado de saúde"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.detplano'
    _generateds_type = 'detPlanoType'
    _concrete_rec_name = 'esoc_tpDep'

    esoc02_detPlano_detOper_id = fields.Many2one(
        "esoc.02.evtdesligli.detoper")
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
    "Detalhamento das verbas rescisórias"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.detverbas'
    _generateds_type = 'detVerbasType'
    _concrete_rec_name = 'esoc_codRubr'

    esoc02_detVerbas_ideEstabLot_id = fields.Many2one(
        "esoc.02.evtdesligli.ideestablot")
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


class DetVerbas5(spec_models.AbstractSpecMixin):
    "Itens da Remuneração do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.detverbas5'
    _generateds_type = 'detVerbasType5'
    _concrete_rec_name = 'esoc_codRubr'

    esoc02_detVerbas_ideEstabLot1_id = fields.Many2one(
        "esoc.02.evtdesligli.ideestablot1")
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
    "Demonstrativos de valores devidos ao trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.dmdev'
    _generateds_type = 'dmDevType'
    _concrete_rec_name = 'esoc_ideDmDev'

    esoc02_dmDev_verbasResc_id = fields.Many2one(
        "esoc.02.evtdesligli.verbasresc")
    esoc02_ideDmDev = fields.Char(
        string="ideDmDev", xsd_required=True)
    esoc02_infoPerApur = fields.Many2one(
        "esoc.02.evtdesligli.infoperapur",
        string="infoPerApur",
        help="Verbas rescisórias relativas ao mês da data do desligamento")
    esoc02_infoPerAnt = fields.Many2one(
        "esoc.02.evtdesligli.infoperant",
        string="Remuneração em Períodos Anteriores",
        help="Remuneração em Períodos Anteriores"
        "\n(Acordo/Convenção/CCP/Dissídio)")
    esoc02_infoTrabInterm = fields.One2many(
        "esoc.02.evtdesligli.infotrabinterm",
        "esoc02_infoTrabInterm_dmDev_id",
        string="Informações da(s) convocação(ões) de trabalho intermitente"
    )


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtdesligli.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtDeslig'

    esoc02_evtDeslig = fields.Many2one(
        "esoc.02.evtdesligli.evtdeslig",
        string="evtDeslig", xsd_required=True)


class EvtDeslig(spec_models.AbstractSpecMixin):
    _description = 'evtdeslig'
    _name = 'esoc.02.evtdesligli.evtdeslig'
    _generateds_type = 'evtDesligType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtdesligli.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtdesligli.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideVinculo = fields.Many2one(
        "esoc.02.evtdesligli.tidevinculonisobrig",
        string="Informações de Identificação do Trabalhador e do Vínculo",
        xsd_required=True)
    esoc02_infoDeslig = fields.Many2one(
        "esoc.02.evtdesligli.infodeslig",
        string="infoDeslig", xsd_required=True)


class IdeADC(spec_models.AbstractSpecMixin):
    "Identificação do Acordo/Legislação/Convenção/CCP/Dissídio/Conversão"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.ideadc'
    _generateds_type = 'ideADCType'
    _concrete_rec_name = 'esoc_dtAcConv'

    esoc02_ideADC_infoPerAnt_id = fields.Many2one(
        "esoc.02.evtdesligli.infoperant")
    esoc02_dtAcConv = fields.Date(
        string="dtAcConv", xsd_required=True)
    esoc02_tpAcConv = fields.Char(
        string="tpAcConv", xsd_required=True)
    esoc02_compAcConv = fields.Char(
        string="compAcConv")
    esoc02_dtEfAcConv = fields.Date(
        string="dtEfAcConv", xsd_required=True)
    esoc02_dsc = fields.Char(
        string="dsc", xsd_required=True)
    esoc02_idePeriodo = fields.One2many(
        "esoc.02.evtdesligli.ideperiodo",
        "esoc02_idePeriodo_ideADC_id",
        string="Identificação do período de referência da remuneração",
        xsd_required=True
    )


class IdeEstabLot(spec_models.AbstractSpecMixin):
    "Identificação do estabelecimento e lotação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.ideestablot'
    _generateds_type = 'ideEstabLotType'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_ideEstabLot_infoPerApur_id = fields.Many2one(
        "esoc.02.evtdesligli.infoperapur")
    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_codLotacao = fields.Char(
        string="codLotacao", xsd_required=True)
    esoc02_detVerbas = fields.One2many(
        "esoc.02.evtdesligli.detverbas",
        "esoc02_detVerbas_ideEstabLot_id",
        string="Detalhamento das verbas rescisórias",
        xsd_required=True
    )
    esoc02_infoSaudeColet = fields.Many2one(
        "esoc.02.evtdesligli.tsaudecol",
        string="infoSaudeColet",
        help="Informações de plano privado coletivo empresarial de"
        "\nassistência à saúde")
    esoc02_infoAgNocivo = fields.Many2one(
        "esoc.02.evtdesligli.infoagnocivo",
        string="Grau de Exposição a Agentes Nocivos")
    esoc02_infoSimples = fields.Many2one(
        "esoc.02.evtdesligli.infosimples",
        string="Informação relativa a empresas do Simples")


class IdeEstabLot1(spec_models.AbstractSpecMixin):
    "Identificação do estabelecimento e lotação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.ideestablot1'
    _generateds_type = 'ideEstabLotType1'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_ideEstabLot_idePeriodo_id = fields.Many2one(
        "esoc.02.evtdesligli.ideperiodo")
    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_codLotacao = fields.Char(
        string="codLotacao", xsd_required=True)
    esoc02_detVerbas = fields.One2many(
        "esoc.02.evtdesligli.detverbas5",
        "esoc02_detVerbas_ideEstabLot1_id",
        string="Itens da Remuneração do Trabalhador",
        xsd_required=True
    )
    esoc02_infoAgNocivo = fields.Many2one(
        "esoc.02.evtdesligli.infoagnocivo12",
        string="Grau de Exposição a Agentes Nocivos")
    esoc02_infoSimples = fields.Many2one(
        "esoc.02.evtdesligli.infosimples14",
        string="Informação relativa a empresas do Simples")


class IdePeriodo(spec_models.AbstractSpecMixin):
    "Identificação do período de referência da remuneração"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.ideperiodo'
    _generateds_type = 'idePeriodoType'
    _concrete_rec_name = 'esoc_perRef'

    esoc02_idePeriodo_ideADC_id = fields.Many2one(
        "esoc.02.evtdesligli.ideadc")
    esoc02_perRef = fields.Char(
        string="perRef", xsd_required=True)
    esoc02_ideEstabLot = fields.One2many(
        "esoc.02.evtdesligli.ideestablot1",
        "esoc02_ideEstabLot_idePeriodo_id",
        string="Identificação do estabelecimento e lotação",
        xsd_required=True
    )


class InfoAgNocivo(spec_models.AbstractSpecMixin):
    "Grau de Exposição a Agentes Nocivos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.infoagnocivo'
    _generateds_type = 'infoAgNocivoType'
    _concrete_rec_name = 'esoc_grauExp'

    esoc02_grauExp = fields.Boolean(
        string="grauExp", xsd_required=True)


class InfoAgNocivo12(spec_models.AbstractSpecMixin):
    "Grau de Exposição a Agentes Nocivos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.infoagnocivo12'
    _generateds_type = 'infoAgNocivoType12'
    _concrete_rec_name = 'esoc_grauExp'

    esoc02_grauExp = fields.Boolean(
        string="grauExp", xsd_required=True)


class InfoDeslig(spec_models.AbstractSpecMixin):
    _description = 'infodeslig'
    _name = 'esoc.02.evtdesligli.infodeslig'
    _generateds_type = 'infoDesligType'
    _concrete_rec_name = 'esoc_mtvDeslig'

    esoc02_mtvDeslig = fields.Char(
        string="mtvDeslig", xsd_required=True)
    esoc02_dtDeslig = fields.Date(
        string="dtDeslig", xsd_required=True)
    esoc02_indPagtoAPI = fields.Char(
        string="indPagtoAPI", xsd_required=True)
    esoc02_dtProjFimAPI = fields.Date(
        string="dtProjFimAPI")
    esoc02_pensAlim = fields.Boolean(
        string="pensAlim", xsd_required=True)
    esoc02_percAliment = fields.Monetary(
        string="percAliment")
    esoc02_vrAlim = fields.Monetary(
        string="vrAlim")
    esoc02_nrCertObito = fields.Char(
        string="nrCertObito")
    esoc02_nrProcTrab = fields.Char(
        string="nrProcTrab")
    esoc02_indCumprParc = fields.Boolean(
        string="indCumprParc",
        xsd_required=True)
    esoc02_qtdDiasInterm = fields.Boolean(
        string="qtdDiasInterm")
    esoc02_observacoes = fields.One2many(
        "esoc.02.evtdesligli.observacoes",
        "esoc02_observacoes_infoDeslig_id",
        string="Observações sobre o desligamento"
    )
    esoc02_sucessaoVinc = fields.Many2one(
        "esoc.02.evtdesligli.sucessaovinc",
        string="Sucessão do Vínculo Trabalhista/Estatutário")
    esoc02_transfTit = fields.Many2one(
        "esoc.02.evtdesligli.transftit",
        string="Transferência de titularidade do empregado doméstico")
    esoc02_mudancaCPF = fields.Many2one(
        "esoc.02.evtdesligli.mudancacpf",
        string="Informação do novo CPF do trabalhador")
    esoc02_verbasResc = fields.Many2one(
        "esoc.02.evtdesligli.verbasresc",
        string="verbasResc")
    esoc02_quarentena = fields.Many2one(
        "esoc.02.evtdesligli.quarentena",
        string="quarentena",
        help="Informações sobre a quarentena remunerada de trabalhador"
        "\ndesligado")
    esoc02_consigFGTS = fields.One2many(
        "esoc.02.evtdesligli.consigfgts",
        "esoc02_consigFGTS_infoDeslig_id",
        string="consigFGTS",
        help="Informações sobre operação de crédito consignado com garantia"
        "\nde FGTS"
    )


class InfoMV(spec_models.AbstractSpecMixin):
    "Informação de Múltiplos Vínculos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.infomv'
    _generateds_type = 'infoMVType'
    _concrete_rec_name = 'esoc_indMV'

    esoc02_indMV = fields.Boolean(
        string="indMV", xsd_required=True)
    esoc02_remunOutrEmpr = fields.One2many(
        "esoc.02.evtdesligli.tremunoutrasempresas",
        "esoc02_remunOutrEmpr_infoMV_id",
        string="remunOutrEmpr",
        xsd_required=True,
        help="Remuneração recebida pelo trabalhador em outras empresas ou"
        "\natividades"
    )


class InfoPerAnt(spec_models.AbstractSpecMixin):
    "Remuneração em Períodos Anteriores (Acordo/Convenção/CCP/Dissídio)"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.infoperant'
    _generateds_type = 'infoPerAntType'
    _concrete_rec_name = 'esoc_ideADC'

    esoc02_ideADC = fields.One2many(
        "esoc.02.evtdesligli.ideadc",
        "esoc02_ideADC_infoPerAnt_id",
        string="ideADC", xsd_required=True,
        help="Identificação do"
        "\nAcordo/Legislação/Convenção/CCP/Dissídio/Conversão"
    )


class InfoPerApur(spec_models.AbstractSpecMixin):
    "Verbas rescisórias relativas ao mês da data do desligamento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.infoperapur'
    _generateds_type = 'infoPerApurType'
    _concrete_rec_name = 'esoc_ideEstabLot'

    esoc02_ideEstabLot = fields.One2many(
        "esoc.02.evtdesligli.ideestablot",
        "esoc02_ideEstabLot_infoPerApur_id",
        string="Identificação do estabelecimento e lotação",
        xsd_required=True
    )


class InfoSimples(spec_models.AbstractSpecMixin):
    "Informação relativa a empresas do Simples"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.infosimples'
    _generateds_type = 'infoSimplesType'
    _concrete_rec_name = 'esoc_indSimples'

    esoc02_indSimples = fields.Boolean(
        string="indSimples", xsd_required=True)


class InfoSimples14(spec_models.AbstractSpecMixin):
    "Informação relativa a empresas do Simples"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.infosimples14'
    _generateds_type = 'infoSimplesType14'
    _concrete_rec_name = 'esoc_indSimples'

    esoc02_indSimples = fields.Boolean(
        string="indSimples", xsd_required=True)


class InfoTrabInterm(spec_models.AbstractSpecMixin):
    "Informações da(s) convocação(ões) de trabalho intermitente"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.infotrabinterm'
    _generateds_type = 'infoTrabIntermType'
    _concrete_rec_name = 'esoc_codConv'

    esoc02_infoTrabInterm_dmDev_id = fields.Many2one(
        "esoc.02.evtdesligli.dmdev")
    esoc02_codConv = fields.Char(
        string="codConv", xsd_required=True)


class MudancaCPF(spec_models.AbstractSpecMixin):
    "Informação do novo CPF do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.mudancacpf'
    _generateds_type = 'mudancaCPFType'
    _concrete_rec_name = 'esoc_novoCPF'

    esoc02_novoCPF = fields.Char(
        string="novoCPF", xsd_required=True)


class Observacoes(spec_models.AbstractSpecMixin):
    "Observações sobre o desligamento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.observacoes'
    _generateds_type = 'observacoesType'
    _concrete_rec_name = 'esoc_observacao'

    esoc02_observacoes_infoDeslig_id = fields.Many2one(
        "esoc.02.evtdesligli.infodeslig")
    esoc02_observacao = fields.Char(
        string="observacao", xsd_required=True)


class ProcCS(spec_models.AbstractSpecMixin):
    """Informação sobre processo judicial que suspende a exigibilidade da
    Contribuição Social Rescisória"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.proccs'
    _generateds_type = 'procCSType'
    _concrete_rec_name = 'esoc_nrProcJud'

    esoc02_nrProcJud = fields.Char(
        string="nrProcJud", xsd_required=True)


class ProcJudTrab(spec_models.AbstractSpecMixin):
    """Informações sobre a existência de processos judiciais do trabalhador"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.procjudtrab'
    _generateds_type = 'procJudTrabType'
    _concrete_rec_name = 'esoc_tpTrib'

    esoc02_procJudTrab_verbasResc_id = fields.Many2one(
        "esoc.02.evtdesligli.verbasresc")
    esoc02_tpTrib = fields.Boolean(
        string="tpTrib", xsd_required=True)
    esoc02_nrProcJud = fields.Char(
        string="nrProcJud", xsd_required=True)
    esoc02_codSusp = fields.Integer(
        string="codSusp")


class Quarentena(spec_models.AbstractSpecMixin):
    "Informações sobre a quarentena remunerada de trabalhador desligado"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.quarentena'
    _generateds_type = 'quarentenaType'
    _concrete_rec_name = 'esoc_dtFimQuar'

    esoc02_dtFimQuar = fields.Date(
        string="dtFimQuar", xsd_required=True)


class SucessaoVinc(spec_models.AbstractSpecMixin):
    "Sucessão do Vínculo Trabalhista/Estatutário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.sucessaovinc'
    _generateds_type = 'sucessaoVincType'
    _concrete_rec_name = 'esoc_tpInscSuc'

    esoc02_tpInscSuc = fields.Boolean(
        string="tpInscSuc", xsd_required=True)
    esoc02_cnpjSucessora = fields.Char(
        string="cnpjSucessora",
        xsd_required=True)


class TransfTit(spec_models.AbstractSpecMixin):
    "Transferência de titularidade do empregado doméstico"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtdesligli.transftit'
    _generateds_type = 'transfTitType'
    _concrete_rec_name = 'esoc_cpfSubstituto'

    esoc02_cpfSubstituto = fields.Char(
        string="cpfSubstituto",
        xsd_required=True)
    esoc02_dtNascto = fields.Date(
        string="dtNascto", xsd_required=True)


class VerbasResc(spec_models.AbstractSpecMixin):
    _description = 'verbasresc'
    _name = 'esoc.02.evtdesligli.verbasresc'
    _generateds_type = 'verbasRescType'
    _concrete_rec_name = 'esoc_dmDev'

    esoc02_dmDev = fields.One2many(
        "esoc.02.evtdesligli.dmdev",
        "esoc02_dmDev_verbasResc_id",
        string="Demonstrativos de valores devidos ao trabalhador",
        xsd_required=True
    )
    esoc02_procJudTrab = fields.One2many(
        "esoc.02.evtdesligli.procjudtrab",
        "esoc02_procJudTrab_verbasResc_id",
        string="procJudTrab",
        help="Informações sobre a existência de processos judiciais do"
        "\ntrabalhador"
    )
    esoc02_infoMV = fields.Many2one(
        "esoc.02.evtdesligli.infomv",
        string="Informação de Múltiplos Vínculos")
    esoc02_procCS = fields.Many2one(
        "esoc.02.evtdesligli.proccs",
        string="procCS",
        help="Informação sobre processo judicial que suspende a"
        "\nexigibilidade da Contribuição Social Rescisória")
