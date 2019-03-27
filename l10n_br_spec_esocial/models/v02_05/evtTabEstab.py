# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:45 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TDadosEstab(spec_models.AbstractSpecMixin):
    "Detalhamento das informações do estabelecimento/obra"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.tdadosestab'
    _generateds_type = 'TDadosEstab'
    _concrete_rec_name = 'esoc_cnaePrep'

    esoc02_cnaePrep = fields.Integer(
        string="cnaePrep", xsd_required=True)
    esoc02_aliqGilrat = fields.Many2one(
        "esoc.02.evttabestab.aliqgilrat",
        string="aliqGilrat", xsd_required=True,
        help="Informações de Apuração da alíquota Gilrat do Estabelecimento")
    esoc02_infoCaepf = fields.Many2one(
        "esoc.02.evttabestab.infocaepf",
        string="Informações relativas ao CAEPF")
    esoc02_infoObra = fields.Many2one(
        "esoc.02.evttabestab.infoobra",
        string="Indicativo de substituição da contribuição Patronal",
        help="Indicativo de substituição da contribuição Patronal - Obra de"
        "\nConstrução Civil")
    esoc02_infoTrab = fields.Many2one(
        "esoc.02.evttabestab.infotrab",
        string="infoTrab", xsd_required=True)


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evttabestab.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeCadastro(spec_models.AbstractSpecMixin):
    "Identificação de evento de cadastro/tabelas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.tidecadastro'
    _generateds_type = 'TIdeCadastro'
    _concrete_rec_name = 'esoc_tpAmb'

    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class TIdeEstab(spec_models.AbstractSpecMixin):
    """Identificação do estabelecimento, obra ou órgão público e validade das
    informações"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.tideestab'
    _generateds_type = 'TIdeEstab'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class TPeriodoValidade(spec_models.AbstractSpecMixin):
    "Período de validade das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.tperiodovalidade'
    _generateds_type = 'TPeriodoValidade'
    _concrete_rec_name = 'esoc_iniValid'

    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class AliqGilrat(spec_models.AbstractSpecMixin):
    "Informações de Apuração da alíquota Gilrat do Estabelecimento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.aliqgilrat'
    _generateds_type = 'aliqGilratType'
    _concrete_rec_name = 'esoc_aliqRat'

    esoc02_aliqRat = fields.Integer(
        string="aliqRat", xsd_required=True)
    esoc02_fap = fields.Monetary(
        string="fap")
    esoc02_aliqRatAjust = fields.Monetary(
        string="aliqRatAjust")
    esoc02_procAdmJudRat = fields.Many2one(
        "esoc.02.evttabestab.procadmjudrat",
        string="Processo administrativo/judicial relativo à alíquota RAT")
    esoc02_procAdmJudFap = fields.Many2one(
        "esoc.02.evttabestab.procadmjudfap",
        string="Processo administrativo/judicial relativo ao FAP")


class Alteracao(spec_models.AbstractSpecMixin):
    "Alteração das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.alteracao'
    _generateds_type = 'alteracaoType'
    _concrete_rec_name = 'esoc_ideEstab'

    esoc02_ideEstab = fields.Many2one(
        "esoc.02.evttabestab.tideestab",
        string="Identificação do estabelecimento",
        xsd_required=True,
        help="Identificação do estabelecimento, obra ou órgão público e"
        "\nvalidade das informações")
    esoc02_dadosEstab = fields.Many2one(
        "esoc.02.evttabestab.tdadosestab",
        string="Detalhamento das informações do estabelecimento",
        xsd_required=True,
        help="Detalhamento das informações do estabelecimento, obra ou"
        "\nórgão público")
    esoc02_novaValidade = fields.Many2one(
        "esoc.02.evttabestab.tperiodovalidade",
        string="Novo período de validade das informações")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttabestab.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtTabEstab'

    esoc02_evtTabEstab = fields.Many2one(
        "esoc.02.evttabestab.evttabestab",
        string="evtTabEstab", xsd_required=True)


class EvtTabEstab(spec_models.AbstractSpecMixin):
    "Evento Tabela de Estabelecimentos, Obras ou Órgãos Públicos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.evttabestab'
    _generateds_type = 'evtTabEstabType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttabestab.tidecadastro",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttabestab.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoEstab = fields.Many2one(
        "esoc.02.evttabestab.infoestab",
        string="Informações do Estabelecimento ou obra",
        xsd_required=True)


class Exclusao(spec_models.AbstractSpecMixin):
    "Exclusão das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.exclusao'
    _generateds_type = 'exclusaoType'
    _concrete_rec_name = 'esoc_ideEstab'

    esoc02_ideEstab = fields.Many2one(
        "esoc.02.evttabestab.tideestab",
        string="Identificação do estabelecimento",
        xsd_required=True,
        help="Identificação do estabelecimento, obra ou órgão público")


class Inclusao(spec_models.AbstractSpecMixin):
    "Inclusão de novas informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.inclusao'
    _generateds_type = 'inclusaoType'
    _concrete_rec_name = 'esoc_ideEstab'

    esoc02_ideEstab = fields.Many2one(
        "esoc.02.evttabestab.tideestab",
        string="Identificação do estabelecimento",
        xsd_required=True,
        help="Identificação do estabelecimento, obra ou órgão público e"
        "\nvalidade das informações")
    esoc02_dadosEstab = fields.Many2one(
        "esoc.02.evttabestab.tdadosestab",
        string="Detalhamento das informações do estabelecimento",
        xsd_required=True,
        help="Detalhamento das informações do estabelecimento, obra ou"
        "\nórgão público")


class InfoApr(spec_models.AbstractSpecMixin):
    "Informações relacionadas à contratação de aprendiz"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.infoapr'
    _generateds_type = 'infoAprType'
    _concrete_rec_name = 'esoc_contApr'

    esoc02_contApr = fields.Boolean(
        string="contApr", xsd_required=True)
    esoc02_nrProcJud = fields.Char(
        string="nrProcJud")
    esoc02_contEntEd = fields.Char(
        string="contEntEd")
    esoc02_infoEntEduc = fields.One2many(
        "esoc.02.evttabestab.infoenteduc",
        "esoc02_infoEntEduc_infoApr_id",
        string="infoEntEduc",
        help="Identificação da(s) entidade(s) educativa(s) ou de prática"
        "\ndesportiva"
    )


class InfoCaepf(spec_models.AbstractSpecMixin):
    "Informações relativas ao CAEPF"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.infocaepf'
    _generateds_type = 'infoCaepfType'
    _concrete_rec_name = 'esoc_tpCaepf'

    esoc02_tpCaepf = fields.Boolean(
        string="tpCaepf", xsd_required=True)


class InfoEntEduc(spec_models.AbstractSpecMixin):
    """Identificação da(s) entidade(s) educativa(s) ou de prática desportiva"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.infoenteduc'
    _generateds_type = 'infoEntEducType'
    _concrete_rec_name = 'esoc_nrInsc'

    esoc02_infoEntEduc_infoApr_id = fields.Many2one(
        "esoc.02.evttabestab.infoapr")
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class InfoEstab(spec_models.AbstractSpecMixin):
    "Informações do Estabelecimento ou obra"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.infoestab'
    _generateds_type = 'infoEstabType'
    _concrete_rec_name = 'esoc_inclusao'

    esoc02_choice1 = fields.Selection([
        ('esoc02_inclusao', 'inclusao'),
        ('esoc02_alteracao', 'alteracao'),
        ('esoc02_exclusao', 'exclusao')],
        "inclusao/alteracao/exclusao",
        default="esoc02_inclusao")
    esoc02_inclusao = fields.Many2one(
        "esoc.02.evttabestab.inclusao",
        choice='1',
        string="Inclusão de novas informações",
        xsd_required=True)
    esoc02_alteracao = fields.Many2one(
        "esoc.02.evttabestab.alteracao",
        choice='1',
        string="Alteração das informações",
        xsd_required=True)
    esoc02_exclusao = fields.Many2one(
        "esoc.02.evttabestab.exclusao",
        choice='1',
        string="Exclusão das informações",
        xsd_required=True)


class InfoObra(spec_models.AbstractSpecMixin):
    """Indicativo de substituição da contribuição Patronal - Obra de Construção
    Civil"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.infoobra'
    _generateds_type = 'infoObraType'
    _concrete_rec_name = 'esoc_indSubstPatrObra'

    esoc02_indSubstPatrObra = fields.Boolean(
        string="indSubstPatrObra",
        xsd_required=True)


class InfoPCD(spec_models.AbstractSpecMixin):
    "Informações sobre a contratação de pessoa com deficiência (PCD)"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.infopcd'
    _generateds_type = 'infoPCDType'
    _concrete_rec_name = 'esoc_contPCD'

    esoc02_contPCD = fields.Boolean(
        string="contPCD", xsd_required=True)
    esoc02_nrProcJud = fields.Char(
        string="nrProcJud")


class InfoTrab(spec_models.AbstractSpecMixin):
    _description = 'infotrab'
    _name = 'esoc.02.evttabestab.infotrab'
    _generateds_type = 'infoTrabType'
    _concrete_rec_name = 'esoc_regPt'

    esoc02_regPt = fields.Boolean(
        string="regPt", xsd_required=True)
    esoc02_infoApr = fields.Many2one(
        "esoc.02.evttabestab.infoapr",
        string="Informações relacionadas à contratação de aprendiz",
        xsd_required=True)
    esoc02_infoPCD = fields.Many2one(
        "esoc.02.evttabestab.infopcd",
        string="Informações sobre a contratação de pessoa com deficiência",
        help="Informações sobre a contratação de pessoa com deficiência"
        "\n(PCD)")


class ProcAdmJudFap(spec_models.AbstractSpecMixin):
    "Processo administrativo/judicial relativo ao FAP"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.procadmjudfap'
    _generateds_type = 'procAdmJudFapType'
    _concrete_rec_name = 'esoc_tpProc'

    esoc02_tpProc = fields.Boolean(
        string="tpProc", xsd_required=True)
    esoc02_nrProc = fields.Char(
        string="nrProc", xsd_required=True)
    esoc02_codSusp = fields.Integer(
        string="codSusp", xsd_required=True)


class ProcAdmJudRat(spec_models.AbstractSpecMixin):
    "Processo administrativo/judicial relativo à alíquota RAT"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabestab.procadmjudrat'
    _generateds_type = 'procAdmJudRatType'
    _concrete_rec_name = 'esoc_tpProc'

    esoc02_tpProc = fields.Boolean(
        string="tpProc", xsd_required=True)
    esoc02_nrProc = fields.Char(
        string="nrProc", xsd_required=True)
    esoc02_codSusp = fields.Integer(
        string="codSusp", xsd_required=True)
