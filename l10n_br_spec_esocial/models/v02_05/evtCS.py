# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:31 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtcslib.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class BasesAquis(spec_models.AbstractSpecMixin):
    "Informações sobre aquisição rural"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.basesaquis'
    _generateds_type = 'basesAquisType'
    _concrete_rec_name = 'esoc_indAquis'

    esoc02_basesAquis_ideEstab_id = fields.Many2one(
        "esoc.02.evtcslib.ideestab")
    esoc02_indAquis = fields.Boolean(
        string="indAquis", xsd_required=True)
    esoc02_vlrAquis = fields.Monetary(
        string="vlrAquis", xsd_required=True)
    esoc02_vrCPDescPR = fields.Monetary(
        string="vrCPDescPR", xsd_required=True)
    esoc02_vrCPNRet = fields.Monetary(
        string="vrCPNRet", xsd_required=True)
    esoc02_vrRatNRet = fields.Monetary(
        string="vrRatNRet", xsd_required=True)
    esoc02_vrSenarNRet = fields.Monetary(
        string="vrSenarNRet", xsd_required=True)
    esoc02_vrCPCalcPR = fields.Monetary(
        string="vrCPCalcPR", xsd_required=True)
    esoc02_vrRatDescPR = fields.Monetary(
        string="vrRatDescPR", xsd_required=True)
    esoc02_vrRatCalcPR = fields.Monetary(
        string="vrRatCalcPR", xsd_required=True)
    esoc02_vrSenarDesc = fields.Monetary(
        string="vrSenarDesc", xsd_required=True)
    esoc02_vrSenarCalc = fields.Monetary(
        string="vrSenarCalc", xsd_required=True)


class BasesAvNPort(spec_models.AbstractSpecMixin):
    "Contratação de avulsos não portuários"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.basesavnport'
    _generateds_type = 'basesAvNPortType'
    _concrete_rec_name = 'esoc_vrBcCp00'

    esoc02_vrBcCp00 = fields.Monetary(
        string="vrBcCp00", xsd_required=True)
    esoc02_vrBcCp15 = fields.Monetary(
        string="vrBcCp15", xsd_required=True)
    esoc02_vrBcCp20 = fields.Monetary(
        string="vrBcCp20", xsd_required=True)
    esoc02_vrBcCp25 = fields.Monetary(
        string="vrBcCp25", xsd_required=True)
    esoc02_vrBcCp13 = fields.Monetary(
        string="vrBcCp13", xsd_required=True)
    esoc02_vrBcFgts = fields.Monetary(
        string="vrBcFgts", xsd_required=True)
    esoc02_vrDescCP = fields.Monetary(
        string="vrDescCP", xsd_required=True)


class BasesComerc(spec_models.AbstractSpecMixin):
    "Informações da Comercialização da produção"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.basescomerc'
    _generateds_type = 'basesComercType'
    _concrete_rec_name = 'esoc_indComerc'

    esoc02_basesComerc_ideEstab_id = fields.Many2one(
        "esoc.02.evtcslib.ideestab")
    esoc02_indComerc = fields.Boolean(
        string="indComerc", xsd_required=True)
    esoc02_vrBcComPR = fields.Monetary(
        string="vrBcComPR", xsd_required=True)
    esoc02_vrCPSusp = fields.Monetary(
        string="vrCPSusp")
    esoc02_vrRatSusp = fields.Monetary(
        string="vrRatSusp")
    esoc02_vrSenarSusp = fields.Monetary(
        string="vrSenarSusp")


class BasesCp(spec_models.AbstractSpecMixin):
    "Bases, contribuições do segurado e deduções da CP"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.basescp'
    _generateds_type = 'basesCpType'
    _concrete_rec_name = 'esoc_vrBcCp00'

    esoc02_vrBcCp00 = fields.Monetary(
        string="vrBcCp00", xsd_required=True)
    esoc02_vrBcCp15 = fields.Monetary(
        string="vrBcCp15", xsd_required=True)
    esoc02_vrBcCp20 = fields.Monetary(
        string="vrBcCp20", xsd_required=True)
    esoc02_vrBcCp25 = fields.Monetary(
        string="vrBcCp25", xsd_required=True)
    esoc02_vrSuspBcCp00 = fields.Monetary(
        string="vrSuspBcCp00",
        xsd_required=True)
    esoc02_vrSuspBcCp15 = fields.Monetary(
        string="vrSuspBcCp15",
        xsd_required=True)
    esoc02_vrSuspBcCp20 = fields.Monetary(
        string="vrSuspBcCp20",
        xsd_required=True)
    esoc02_vrSuspBcCp25 = fields.Monetary(
        string="vrSuspBcCp25",
        xsd_required=True)
    esoc02_vrDescSest = fields.Monetary(
        string="vrDescSest", xsd_required=True)
    esoc02_vrCalcSest = fields.Monetary(
        string="vrCalcSest", xsd_required=True)
    esoc02_vrDescSenat = fields.Monetary(
        string="vrDescSenat", xsd_required=True)
    esoc02_vrCalcSenat = fields.Monetary(
        string="vrCalcSenat", xsd_required=True)
    esoc02_vrSalFam = fields.Monetary(
        string="vrSalFam", xsd_required=True)
    esoc02_vrSalMat = fields.Monetary(
        string="vrSalMat", xsd_required=True)


class BasesRemun(spec_models.AbstractSpecMixin):
    "Bases de cálculo por categoria"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.basesremun'
    _generateds_type = 'basesRemunType'
    _concrete_rec_name = 'esoc_indIncid'

    esoc02_basesRemun_ideLotacao_id = fields.Many2one(
        "esoc.02.evtcslib.idelotacao")
    esoc02_indIncid = fields.Boolean(
        string="indIncid", xsd_required=True)
    esoc02_codCateg = fields.Integer(
        string="codCateg", xsd_required=True)
    esoc02_basesCp = fields.Many2one(
        "esoc.02.evtcslib.basescp",
        string="Bases", xsd_required=True,
        help="Bases, contribuições do segurado e deduções da CP")


class DadosOpPort(spec_models.AbstractSpecMixin):
    "Informações relativas ao operador portuário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.dadosopport'
    _generateds_type = 'dadosOpPortType'
    _concrete_rec_name = 'esoc_cnpjOpPortuario'

    esoc02_cnpjOpPortuario = fields.Char(
        string="cnpjOpPortuario",
        xsd_required=True)
    esoc02_aliqRat = fields.Integer(
        string="aliqRat", xsd_required=True)
    esoc02_fap = fields.Monetary(
        string="fap", xsd_required=True)
    esoc02_aliqRatAjust = fields.Monetary(
        string="aliqRatAjust",
        xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtcslib.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtCS'

    esoc02_evtCS = fields.Many2one(
        "esoc.02.evtcslib.evtcs",
        string="evtCS", xsd_required=True)


class EvtCS(spec_models.AbstractSpecMixin):
    "Evento Contribuições Sociais"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.evtcs'
    _generateds_type = 'evtCSType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtcslib.ideevento",
        string="Identificação do evento de retorno",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtcslib.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoCS = fields.Many2one(
        "esoc.02.evtcslib.infocs",
        string="Informações relativas às Contribuições Sociais",
        xsd_required=True)


class IdeEstab(spec_models.AbstractSpecMixin):
    "Identificação do estabelecimento/obra"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.ideestab'
    _generateds_type = 'ideEstabType'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_ideEstab_infoCS_id = fields.Many2one(
        "esoc.02.evtcslib.infocs")
    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_infoEstab = fields.Many2one(
        "esoc.02.evtcslib.infoestab",
        string="Informações do estabelecimento")
    esoc02_ideLotacao = fields.One2many(
        "esoc.02.evtcslib.idelotacao",
        "esoc02_ideLotacao_ideEstab_id",
        string="Identificação da lotação tributária"
    )
    esoc02_basesAquis = fields.One2many(
        "esoc.02.evtcslib.basesaquis",
        "esoc02_basesAquis_ideEstab_id",
        string="Informações sobre aquisição rural"
    )
    esoc02_basesComerc = fields.One2many(
        "esoc.02.evtcslib.basescomerc",
        "esoc02_basesComerc_ideEstab_id",
        string="Informações da Comercialização da produção"
    )
    esoc02_infoCREstab = fields.One2many(
        "esoc.02.evtcslib.infocrestab",
        "esoc02_infoCREstab_ideEstab_id",
        string="Códigos de Receita por Estabelecimento"
    )


class IdeEvento(spec_models.AbstractSpecMixin):
    "Identificação do evento de retorno"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'esoc_indApuracao'

    esoc02_indApuracao = fields.Boolean(
        string="indApuracao", xsd_required=True)
    esoc02_perApur = fields.Char(
        string="perApur", xsd_required=True)


class IdeLotacao(spec_models.AbstractSpecMixin):
    "Identificação da lotação tributária"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.idelotacao'
    _generateds_type = 'ideLotacaoType'
    _concrete_rec_name = 'esoc_codLotacao'

    esoc02_ideLotacao_ideEstab_id = fields.Many2one(
        "esoc.02.evtcslib.ideestab")
    esoc02_codLotacao = fields.Char(
        string="codLotacao", xsd_required=True)
    esoc02_fpas = fields.Integer(
        string="fpas", xsd_required=True)
    esoc02_codTercs = fields.Char(
        string="codTercs", xsd_required=True)
    esoc02_codTercsSusp = fields.Char(
        string="codTercsSusp")
    esoc02_infoTercSusp = fields.One2many(
        "esoc.02.evtcslib.infotercsusp",
        "esoc02_infoTercSusp_ideLotacao_id",
        string="Informações de suspensão de contribuição a Terceiros"
    )
    esoc02_infoEmprParcial = fields.Many2one(
        "esoc.02.evtcslib.infoemprparcial",
        string="Informação complementar de obra de construção civil")
    esoc02_dadosOpPort = fields.Many2one(
        "esoc.02.evtcslib.dadosopport",
        string="Informações relativas ao operador portuário")
    esoc02_basesRemun = fields.One2many(
        "esoc.02.evtcslib.basesremun",
        "esoc02_basesRemun_ideLotacao_id",
        string="Bases de cálculo por categoria"
    )
    esoc02_basesAvNPort = fields.Many2one(
        "esoc.02.evtcslib.basesavnport",
        string="Contratação de avulsos não portuários")
    esoc02_infoSubstPatrOpPort = fields.One2many(
        "esoc.02.evtcslib.infosubstpatropport",
        "esoc02_infoSubstPatrOpPort_ideLotacao_id",
        string="Inf de substituição prevista na Lei 12546/2011"
    )


class InfoAtConc(spec_models.AbstractSpecMixin):
    "Informações de Atividades Concomitantes"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.infoatconc'
    _generateds_type = 'infoAtConcType'
    _concrete_rec_name = 'esoc_fatorMes'

    esoc02_fatorMes = fields.Monetary(
        string="fatorMes", xsd_required=True)
    esoc02_fator13 = fields.Monetary(
        string="fator13", xsd_required=True)


class InfoCPSeg(spec_models.AbstractSpecMixin):
    "Informações de contribuição previdenciária do Segurado"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.infocpseg'
    _generateds_type = 'infoCPSegType'
    _concrete_rec_name = 'esoc_vrDescCP'

    esoc02_vrDescCP = fields.Monetary(
        string="vrDescCP", xsd_required=True)
    esoc02_vrCpSeg = fields.Monetary(
        string="vrCpSeg", xsd_required=True)


class InfoCRContrib(spec_models.AbstractSpecMixin):
    "Totalizador dos CT do contribuinte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.infocrcontrib'
    _generateds_type = 'infoCRContribType'
    _concrete_rec_name = 'esoc_tpCR'

    esoc02_infoCRContrib_infoCS_id = fields.Many2one(
        "esoc.02.evtcslib.infocs")
    esoc02_tpCR = fields.Integer(
        string="tpCR", xsd_required=True)
    esoc02_vrCR = fields.Monetary(
        string="vrCR", xsd_required=True)
    esoc02_vrCRSusp = fields.Monetary(
        string="vrCRSusp")


class InfoCREstab(spec_models.AbstractSpecMixin):
    "Códigos de Receita por Estabelecimento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.infocrestab'
    _generateds_type = 'infoCREstabType'
    _concrete_rec_name = 'esoc_tpCR'

    esoc02_infoCREstab_ideEstab_id = fields.Many2one(
        "esoc.02.evtcslib.ideestab")
    esoc02_tpCR = fields.Integer(
        string="tpCR", xsd_required=True)
    esoc02_vrCR = fields.Monetary(
        string="vrCR", xsd_required=True)
    esoc02_vrSuspCR = fields.Monetary(
        string="vrSuspCR")


class InfoCS(spec_models.AbstractSpecMixin):
    "Informações relativas às Contribuições Sociais"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.infocs'
    _generateds_type = 'infoCSType'
    _concrete_rec_name = 'esoc_nrRecArqBase'

    esoc02_nrRecArqBase = fields.Char(
        string="nrRecArqBase",
        xsd_required=True)
    esoc02_indExistInfo = fields.Boolean(
        string="indExistInfo",
        xsd_required=True)
    esoc02_infoCPSeg = fields.Many2one(
        "esoc.02.evtcslib.infocpseg",
        string="Informações de contribuição previdenciária do Segurado")
    esoc02_infoContrib = fields.Many2one(
        "esoc.02.evtcslib.infocontrib",
        string="Informações gerais do contribuinte",
        xsd_required=True)
    esoc02_ideEstab = fields.One2many(
        "esoc.02.evtcslib.ideestab",
        "esoc02_ideEstab_infoCS_id",
        string="Identificação do estabelecimento/obra"
    )
    esoc02_infoCRContrib = fields.One2many(
        "esoc.02.evtcslib.infocrcontrib",
        "esoc02_infoCRContrib_infoCS_id",
        string="Totalizador dos CT do contribuinte"
    )


class InfoComplObra(spec_models.AbstractSpecMixin):
    "Informações complementares relativas a obras"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.infocomplobra'
    _generateds_type = 'infoComplObraType'
    _concrete_rec_name = 'esoc_indSubstPatrObra'

    esoc02_indSubstPatrObra = fields.Boolean(
        string="indSubstPatrObra",
        xsd_required=True)


class InfoContrib(spec_models.AbstractSpecMixin):
    "Informações gerais do contribuinte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.infocontrib'
    _generateds_type = 'infoContribType'
    _concrete_rec_name = 'esoc_classTrib'

    esoc02_classTrib = fields.Char(
        string="classTrib", xsd_required=True)
    esoc02_infoPJ = fields.Many2one(
        "esoc.02.evtcslib.infopj",
        string="Informações exclusivas da PJ")


class InfoEmprParcial(spec_models.AbstractSpecMixin):
    "Informação complementar de obra de construção civil"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.infoemprparcial'
    _generateds_type = 'infoEmprParcialType'
    _concrete_rec_name = 'esoc_tpInscContrat'

    esoc02_tpInscContrat = fields.Boolean(
        string="tpInscContrat",
        xsd_required=True)
    esoc02_nrInscContrat = fields.Char(
        string="nrInscContrat",
        xsd_required=True)
    esoc02_tpInscProp = fields.Boolean(
        string="tpInscProp", xsd_required=True)
    esoc02_nrInscProp = fields.Char(
        string="nrInscProp", xsd_required=True)


class InfoEstab(spec_models.AbstractSpecMixin):
    "Informações do estabelecimento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.infoestab'
    _generateds_type = 'infoEstabType'
    _concrete_rec_name = 'esoc_cnaePrep'

    esoc02_cnaePrep = fields.Integer(
        string="cnaePrep", xsd_required=True)
    esoc02_aliqRat = fields.Integer(
        string="aliqRat", xsd_required=True)
    esoc02_fap = fields.Monetary(
        string="fap", xsd_required=True)
    esoc02_aliqRatAjust = fields.Monetary(
        string="aliqRatAjust",
        xsd_required=True)
    esoc02_infoComplObra = fields.Many2one(
        "esoc.02.evtcslib.infocomplobra",
        string="Informações complementares relativas a obras")


class InfoPJ(spec_models.AbstractSpecMixin):
    "Informações exclusivas da PJ"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.infopj'
    _generateds_type = 'infoPJType'
    _concrete_rec_name = 'esoc_indCoop'

    esoc02_indCoop = fields.Boolean(
        string="indCoop")
    esoc02_indConstr = fields.Boolean(
        string="indConstr", xsd_required=True)
    esoc02_indSubstPatr = fields.Boolean(
        string="indSubstPatr")
    esoc02_percRedContrib = fields.Monetary(
        string="percRedContrib")
    esoc02_infoAtConc = fields.Many2one(
        "esoc.02.evtcslib.infoatconc",
        string="Informações de Atividades Concomitantes")


class InfoSubstPatrOpPort(spec_models.AbstractSpecMixin):
    "Inf de substituição prevista na Lei 12546/2011"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.infosubstpatropport'
    _generateds_type = 'infoSubstPatrOpPortType'
    _concrete_rec_name = 'esoc_cnpjOpPortuario'

    esoc02_infoSubstPatrOpPort_ideLotacao_id = fields.Many2one(
        "esoc.02.evtcslib.idelotacao")
    esoc02_cnpjOpPortuario = fields.Char(
        string="cnpjOpPortuario",
        xsd_required=True)


class InfoTercSusp(spec_models.AbstractSpecMixin):
    "Informações de suspensão de contribuição a Terceiros"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcslib.infotercsusp'
    _generateds_type = 'infoTercSuspType'
    _concrete_rec_name = 'esoc_codTerc'

    esoc02_infoTercSusp_ideLotacao_id = fields.Many2one(
        "esoc.02.evtcslib.idelotacao")
    esoc02_codTerc = fields.Char(
        string="codTerc", xsd_required=True)
